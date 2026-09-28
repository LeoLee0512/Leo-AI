"""Real Chromium DOM regression for the two Settings theme pickers.

Uses the production start page (the only theme picker since the upstream-page
injection layer was removed on 2026-09-26) with
the real ShellApi/SettingsStore contract, carried over a loopback JSON bridge.
Only unrelated workbench navigation/language coordination is stubbed; no theme
cards or state responses are fabricated. Every request reconstructs the store,
and the page reloads after saving, so persistence cannot pass on cached state.

This is a source integration check, not an installed EXE/WebView2 acceptance
test. LEO_THEME_TEST_APP_ROOT can select installed theme assets (read-only),
but Python still comes from this checkout. Chrome has a fresh temporary profile
and all appearance writes go to pytest's temporary root. No packages or browser
downloads are needed. A missing browser is explicitly reported as SKIP.
"""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from leo_shell.api import ShellApi
from leo_shell.paths import AppPaths
from leo_shell.secrets_store import SecretsStore
from leo_shell.settings_store import SettingsStore


ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    "ink-autumn": {"zh": "淡墨浓秋", "en": "Ink Autumn"},
    "deep-sea-molten-orange": {
        "zh": "深海 × 熔橙", "en": "Deep Sea × Molten Orange"
    },
    "amethyst-teal": {"zh": "紫晶 × 青绿", "en": "Amethyst × Teal"},
}


def _chrome() -> str:
    explicit = os.environ.get("LEO_THEME_TEST_CHROME")
    if explicit:
        assert Path(explicit).is_file(), "LEO_THEME_TEST_CHROME does not exist"
        return explicit
    for executable in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(executable)
        if found:
            return found
    for folder in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        if os.environ.get(folder):
            candidate = Path(os.environ[folder]) / "Google/Chrome/Application/chrome.exe"
            if candidate.is_file():
                return str(candidate)
    pytest.skip("Chrome/Chromium unavailable: actual Settings DOM was NOT tested")


BRIDGE = r"""
function rpc(method, payload) {
  // The transport alone substitutes for pywebview. Responses and writes are
  // real ShellApi calls; synchronous local XHR avoids virtual-time fetch races.
  const request = new XMLHttpRequest();
  request.open('POST', '/api/' + method, false);
  request.setRequestHeader('Content-Type', 'application/json');
  request.send(JSON.stringify(payload || {}));
  if (request.status !== 200) throw new Error('bridge HTTP ' + request.status);
  return JSON.parse(request.responseText);
}
window.pywebview = {api: {
  get_state: () => Promise.resolve(rpc('get_state')),
  save_appearance: payload => Promise.resolve(rpc('save_appearance', payload))
}};
"""


DRIVER = r"""
(async () => {
  const assert = (condition, message) => {if (!condition) throw new Error(message)};
  const waitFor = async (predicate, message) => {
    for (let i = 0; i < 100; i++) {
      if (predicate()) return;
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    throw new Error(message);
  };
  const cards = () => Array.from(document.querySelectorAll(TEST.page === 'shell'
    ? '#theme-choices .theme-card' : '#leo-theme-grid .leo-theme-choice'));
  const buttonFor = id => cards().find(button =>
    button.querySelector('b')?.textContent === TEST.themes[id][TEST.locale]);
  const checkCards = () => {
    assert(cards().length === 3, 'Expected exactly three rendered theme choices');
    for (const id of Object.keys(TEST.themes)) {
      assert(buttonFor(id), 'Missing bilingual theme label: ' + id);
    }
    assert(!cards().some(button => button.textContent.includes('淡墨秋黄')),
      'Obsolete Ink Autumn name in actual theme picker');
  };
  try {
    if (TEST.page === 'shell') {
      window.dispatchEvent(new Event('pywebviewready'));
      await waitFor(() => document.body.classList.contains('ready'), 'Shell not ready');
      document.querySelector('#settings-top').click();
      document.querySelector('[data-tab="appearance"]').click();
      assert(document.querySelector('#settings').classList.contains('open'),
        'Settings drawer did not open');
      assert(document.querySelector('[data-pane="appearance"]').classList.contains('active'),
        'Appearance tab did not activate');
    } else {
      await loadPanelState(document.querySelector('#test-overlay'));
    }
    checkCards();
    const selected = id => buttonFor(id)?.classList.contains('active');
    assert(selected('ink-autumn'), 'Ink Autumn was not selected on page load');
    if (!sessionStorage.getItem('leo-theme-test-reloaded')) {
      for (const id of ['deep-sea-molten-orange', 'amethyst-teal', 'ink-autumn']) {
        buttonFor(id).click();
        await waitFor(() => selected(id), 'Clicked choice did not become active: ' + id);
        const persisted = rpc('get_state').appearance;
        assert(persisted.theme === id, 'Backend did not persist clicked theme: ' + id);
        assert(persisted.locale === TEST.locale, 'Theme save changed the locale');
        assert(cards().filter(button => button.classList.contains('active')).length === 1,
          'Theme selection has multiple active choices');
        checkCards();
      }
      sessionStorage.setItem('leo-theme-test-reloaded', '1');
      location.reload();
      return;
    }
    const persisted = rpc('get_state').appearance;
    assert(persisted.theme === 'ink-autumn', 'Reload lost the selected theme');
    assert(persisted.locale === TEST.locale, 'Reload lost the selected locale');
    const output = document.createElement('pre');
    output.id = 'leo-theme-integration-result';
    output.textContent = JSON.stringify({ok: true, reloaded: true,
      page: TEST.page, locale: TEST.locale,
      labels: cards().map(button => button.querySelector('b').textContent),
      selected: persisted.theme});
    document.body.appendChild(output);
  } catch (error) {
    const output = document.createElement('pre');
    output.id = 'leo-theme-integration-result';
    output.textContent = JSON.stringify({ok: false, error: String(error.stack || error)});
    document.body.appendChild(output);
  }
})();
"""


def _page(assets: Path, page: str, locale: str) -> str:
    config = json.dumps({"page": page, "locale": locale, "themes": THEMES}, ensure_ascii=False)
    setup = f"<script>{BRIDGE}\nconst TEST = {config};</script>"
    if page == "shell":
        source = (assets / "shell.html").read_text(encoding="utf-8-sig")
        source = source.replace("__LEO_OPEN_SETTINGS__", "0")
        source = source.replace("__LEO_LION_DATA_URI__", "data:,")
        return source.replace("<script>", setup + "<script>", 1).replace(
            "</body>", f"<script>{DRIVER}</script></body>"
        )

    # The second picker lived in the injected upstream page, removed on 2026-09-26.
    raise ValueError(f"no theme picker on page {page!r}")


@pytest.mark.parametrize("page", ["shell"])
@pytest.mark.parametrize("locale", ["zh", "en"])
def test_actual_settings_theme_picker(tmp_path: Path, page: str, locale: str) -> None:
    chrome = _chrome()
    app_override = os.environ.get("LEO_THEME_TEST_APP_ROOT")
    assets = Path(app_override) / "theme" if app_override else ROOT / "stage"
    paths = AppPaths.from_root(tmp_path / "isolated-app")
    paths.theme.mkdir(parents=True)
    shutil.copyfile(assets / "themes.json", paths.theme / "themes.json")

    def new_api() -> ShellApi:
        store = SettingsStore(paths, SecretsStore(paths.credentials))
        # No model methods are exposed by this test transport; no coordinator
        # or loaded backend is needed for the real appearance methods.
        return ShellApi(store, None, paths=paths)

    if locale == "en":
        assert new_api().save_appearance({"theme": "ink-autumn", "locale": locale})["ok"]
    assert new_api().get_state()["appearance"] == {"theme": "ink-autumn", "locale": locale}
    page_bytes = _page(assets, page, locale).encode("utf-8")
    writes: list[dict] = []
    loads: list[str] = []
    failures: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:
            pass

        def do_GET(self) -> None:
            if self.path != "/":
                self.send_error(404)
                return
            loads.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(page_bytes)))
            self.end_headers()
            self.wfile.write(page_bytes)

        def do_POST(self) -> None:
            if self.path not in ("/api/get_state", "/api/save_appearance"):
                self.send_error(404)
                return
            try:
                api = new_api()
                length = int(self.headers.get("Content-Length", "0"))
                assert 0 <= length <= 4096
                payload = json.loads(self.rfile.read(length))
                if self.path == "/api/save_appearance":
                    writes.append(payload)
                    result = api.save_appearance(payload)
                else:
                    result = api.get_state()
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as error:
                failures.append(repr(error))
                self.send_error(500)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        command = [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                   "--no-default-browser-check", "--disable-background-networking",
                   "--disable-component-update", "--disable-extensions",
                   "--no-proxy-server", f"--user-data-dir={tmp_path / 'chrome-profile'}",
                   "--dump-dom", "--virtual-time-budget=12000",
                   f"http://127.0.0.1:{server.server_port}/"]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=45,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)

    assert not failures, failures
    assert result.returncode == 0, result.stderr[-3000:]
    match = re.search(r'<pre id="leo-theme-integration-result">(.*?)</pre>', result.stdout, re.S)
    assert match, "Browser did not complete the Settings DOM check: " + result.stderr[-3000:]
    observed = json.loads(html.unescape(match.group(1)))
    assert observed.get("ok"), observed
    assert observed["reloaded"] and len(loads) >= 2
    assert observed["labels"] == [theme[locale] for theme in THEMES.values()]
    assert writes == [
        {"theme": theme, "locale": locale}
        for theme in ("deep-sea-molten-orange", "amethyst-teal", "ink-autumn")
    ]
    persisted = json.loads((paths.user / "appearance.json").read_text(encoding="utf-8"))
    assert persisted == {"schema_version": 1, "theme": "ink-autumn", "locale": locale}
    # SecretsStore creates its directory at construction, even without keys.
    assert not any(paths.credentials.iterdir()), "Theme selection unexpectedly wrote credentials"

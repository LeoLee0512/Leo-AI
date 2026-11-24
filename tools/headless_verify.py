"""Headless end-to-end verification of the new leo_shell stack against a real package.

Runs the exact connection pipeline the UI would drive, without opening a window:
preflight -> status -> (install if needed) -> start -> url -> HTTP probe -> stop.

Usage (from the build repository root):
    .venv/Scripts/python tools/headless_verify.py [package-root]

Nothing is written to the package's user/ directory. The API key is never read;
the daemon is started keyless, which is a supported browsing mode.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from leo_shell.bridge_client import BridgeError, WslBridge
from leo_shell.paths import AppPaths
from leo_shell.secrets_store import SecretsStore
from leo_shell.settings_store import SettingsStore
from leo_shell.theme_runtime import ThemeRuntime, trusted_backend_url


def _redact_token(url: str) -> str:
    return url.split("token=", 1)[0] + ("token=<redacted>" if "token=" in url else "")


def main() -> int:
    # Repo-relative by default, overridable, so this runs on any machine.
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    elif os.environ.get("LEO_APP_ROOT"):
        root = Path(os.environ["LEO_APP_ROOT"])
    else:
        root = Path(__file__).resolve().parents[1] / "LeoAIStudio"
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger("leo_shell.headless")

    paths = AppPaths.from_root(root)
    print(f"[paths] root={paths.root} bridge={paths.bridge_script.exists()} webview2={paths.webview2_dir()}")

    secrets = SecretsStore(paths.credentials)
    settings = SettingsStore(paths, secrets)
    state = settings.state_for_shell()
    profile = settings.active_profile()
    print(f"[settings] active={profile.id if profile else None} provider={profile.provider if profile else '-'} "
          f"model={profile.model if profile else '-'} base_url={profile.base_url if profile else '-'} "
          f"has_key={bool(state.get('has_key'))} profiles={len(state.get('profiles', []))}")

    theme = ThemeRuntime(paths.theme)
    shell = theme.render_shell(open_settings=False)
    workbench = theme.render_workbench()
    print(f"[theme] shell={len(shell.encode('utf-8'))} bytes, workbench={len(workbench.encode('utf-8'))} bytes")

    bridge = WslBridge(paths, logger=logger)
    stages = []

    def stage(name, fn):
        started = time.monotonic()
        try:
            result = fn()
        except BridgeError as exc:
            stages.append((name, f"FAIL {exc.code}: {exc.message}"))
            print(f"[stage] {name}: FAIL code={exc.code} message={exc.message}")
            return None
        elapsed = time.monotonic() - started
        stages.append((name, f"ok {elapsed:.1f}s"))
        print(f"[stage] {name}: ok ({elapsed:.1f}s)")
        return result

    if stage("preflight", bridge.preflight) is None:
        return 1
    status = stage("status", bridge.status)
    if status is None:
        return 1
    print(f"[status] {json.dumps(status, ensure_ascii=False)}")

    if profile is None:
        print("[stage] start: skipped (no active profile)")
        return 0

    started = stage("start", lambda: bridge.start(
        provider=profile.provider, model=profile.model,
        base_url=profile.base_url, api_key=None,
    ))
    if started is None:
        return 1
    print(f"[start] {json.dumps(started, ensure_ascii=False)}")

    url = stage("url", bridge.client_url)
    if url is None:
        stage("stop", bridge.stop)
        return 1
    print(f"[url] {_redact_token(url)} trusted={trusted_backend_url(url)}")

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def probe():
        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(url, timeout=10) as response:  # noqa: S310 - loopback only
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code  # 303 is the expected "token accepted, redirect" answer

    def health():
        request = urllib.request.Request("http://127.0.0.1:8760/health")
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    code = stage("http-root", probe)
    payload = stage("http-health", health)
    print(f"[http] root_status={code} health={json.dumps(payload, ensure_ascii=False) if payload else None}")

    stage("stop", bridge.stop)
    print("[summary] " + "; ".join(f"{name}={outcome}" for name, outcome in stages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

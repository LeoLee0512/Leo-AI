"""The opening animation: once per launch, skippable, never blocking, and attributed in Settings."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

from leo_shell.intro import INTRO_DIRECTORY, INTRO_FILE, INTRO_HOST, IntroGate, intro_url
from leo_shell.theme_runtime import ThemeRuntime

REPO = Path(__file__).resolve().parents[2]
STAGE = REPO / "stage"
NOTE_ZH = "开场动画由 Seedance 2.5 模型生成。"


def _gate(tmp_path: Path, *, with_file: bool = True, enabled: bool = True) -> IntroGate:
    folder = tmp_path / INTRO_DIRECTORY
    folder.mkdir()
    if with_file:
        (folder / INTRO_FILE).write_bytes(b"\x00\x00\x00\x20ftypisom")
    return IntroGate(folder, enabled=enabled)


def test_the_gate_hands_the_intro_out_exactly_once(tmp_path):
    gate = _gate(tmp_path)
    assert gate.pending() is True
    assert gate.claim() is True
    assert gate.claim() is False, "returning to the start page must not replay the animation"
    assert gate.pending() is False


def test_no_file_or_a_cancelled_gate_means_no_intro(tmp_path):
    for name in ("a", "b", "c"):
        (tmp_path / name).mkdir()
    assert _gate(tmp_path / "a", with_file=False).claim() is False
    cancelled = _gate(tmp_path / "b")
    cancelled.cancel()
    assert cancelled.pending() is False and cancelled.claim() is False
    assert _gate(tmp_path / "c", enabled=False).claim() is False


def test_the_url_is_the_reserved_virtual_host_and_the_page_accepts_only_it():
    assert INTRO_HOST.endswith(".example")
    assert intro_url() == f"https://{INTRO_HOST}/{INTRO_FILE}"
    shell = (STAGE / "shell.html").read_text(encoding="utf-8")
    assert f'const HOST="https://{INTRO_HOST}/"' in shell


def test_the_api_passes_the_url_through_and_degrades_to_null():
    from leo_shell.api import ShellApi

    assert ShellApi(None, None, SimpleNamespace(intro_video_url=lambda: intro_url())).intro_video() == \
        {"ok": True, "url": intro_url()}
    assert ShellApi(None, None, SimpleNamespace(intro_video_url=lambda: None)).intro_video() == {"ok": True, "url": None}
    assert ShellApi(None, None, SimpleNamespace()).intro_video() == {"ok": True, "url": None}

    def broken():
        raise RuntimeError("no webview")
    assert ShellApi(None, None, SimpleNamespace(intro_video_url=broken)).intro_video() == {"ok": True, "url": None}


def test_the_start_page_marks_the_intro_only_on_launch_and_never_with_settings():
    runtime = ThemeRuntime(STAGE)
    assert 'data-intro="1"' in runtime.render_shell(open_settings=False, intro=True)
    assert 'data-intro="0"' in runtime.render_shell(open_settings=False)
    assert 'data-intro="0"' in runtime.render_shell(open_settings=True, intro=True)


def _ui(tmp_path, loaded):
    from leo_shell.ui import DesktopUI

    (tmp_path / INTRO_DIRECTORY).mkdir(parents=True, exist_ok=True)
    (tmp_path / INTRO_DIRECTORY / INTRO_FILE).write_bytes(b"x")
    ui = DesktopUI(SimpleNamespace(theme=tmp_path), None, None, None)
    ui._window = SimpleNamespace(native=object(), load_html=loaded.append, evaluate_js=lambda _s: None)
    ui._boot = ("<with intro>", "<plain>")
    return ui


def test_boot_maps_first_then_loads_the_start_page_and_hands_the_url_out_once(tmp_path, monkeypatch):
    import leo_shell.ui as ui_module

    mapped, loaded = [], []
    monkeypatch.setattr(ui_module, "map_intro_folder", lambda native, folder: mapped.append(folder))
    ui = _ui(tmp_path, loaded)
    assert ui.intro_video_url() is None, "nothing is handed out before the mapping exists"
    ui._on_boot_loaded()
    ui._on_boot_loaded()                      # the start page's own load event must not boot again
    assert mapped == [tmp_path / INTRO_DIRECTORY] and loaded == ["<with intro>"]
    assert ui.intro_video_url() == intro_url()
    assert ui.intro_video_url() is None, "returning to the start page must not replay the animation"


def test_a_failed_mapping_or_a_silent_boot_page_still_reaches_the_start_page(tmp_path, monkeypatch):
    import leo_shell.ui as ui_module

    def refuse(native, folder):
        raise RuntimeError("no CoreWebView2")
    monkeypatch.setattr(ui_module, "map_intro_folder", refuse)
    loaded = []
    ui = _ui(tmp_path / "a", loaded)
    ui._on_boot_loaded()
    assert loaded == ["<plain>"] and ui.intro_video_url() is None

    monkeypatch.setattr(ui_module.time, "sleep", lambda _s: None)
    loaded = []
    ui = _ui(tmp_path / "b", loaded)
    ui._boot_fallback()
    ui._on_boot_loaded()                      # a late load event after the fallback changes nothing
    assert loaded == ["<plain>"] and ui.intro_video_url() is None


def test_a_settings_launch_skips_the_intro(tmp_path):
    from leo_shell.ui import DesktopUI

    (tmp_path / INTRO_DIRECTORY).mkdir()
    (tmp_path / INTRO_DIRECTORY / INTRO_FILE).write_bytes(b"x")
    ui = DesktopUI(SimpleNamespace(theme=tmp_path), None, None, None)
    ui._window = SimpleNamespace(evaluate_js=lambda _s: None)
    ui.request_open_settings()
    assert ui._intro.pending() is False and ui.intro_video_url() is None


def test_the_page_skips_on_click_and_any_key_and_never_blocks():
    shell = (STAGE / "shell.html").read_text(encoding="utf-8")
    script = shell[shell.index('<div id="leo-intro"'):shell.index("</script>", shell.index('<div id="leo-intro"'))]
    assert 'addEventListener("pointerdown"' in script
    assert 'document.addEventListener("keydown",onKey,true)' in script, "any key, captured before the page's own handlers"
    assert 'film.addEventListener("ended",dismiss)' in script and 'film.addEventListener("error",dismiss)' in script
    assert re.search(r'setTimeout\(\(\)=>\{if\(!layer\.classList\.contains\("playing"\)\)dismiss\(\)\},\d+\)', script)
    assert "film.muted=true" in script, "a blocked autoplay with sound falls back to muted playback"
    assert 'window.LeoIntro&&window.LeoIntro.dismiss()' in shell, "opening Settings ends the animation"
    assert "object-fit:contain" in shell, "the whole film is shown; its closing line sits near the left edge"


def test_no_watermark_but_settings_name_the_model_next_to_openai4s():
    shell = (STAGE / "shell.html").read_text(encoding="utf-8")
    overlay = shell[shell.index('<div id="leo-intro"'):shell.index("</div>", shell.index('<div id="leo-intro"'))]
    assert "Seedance" not in overlay and "AI" not in overlay, "nothing is drawn over the film"
    source = '<span class="about-source">github.com/PKU-YuanGroup/OpenAI4S</span>'
    assert shell.count(source + f'<span class="about-note">{NOTE_ZH}</span>') == 2, "static About and zh copy"
    assert source + '<span class="about-note">The opening animation was generated with the Seedance 2.5 model.</span>' in shell
    assert f"<p>{NOTE_ZH}</p>" in (STAGE / "workbench.html").read_text(encoding="utf-8")


def test_the_video_ships_and_its_origin_is_recorded():
    video = STAGE / INTRO_DIRECTORY / INTRO_FILE
    data = video.read_bytes()
    assert data[4:8] == b"ftyp" and 0 < data.find(b"moov") < data.find(b"mdat"), "faststart: index before media"
    origin = json.loads((REPO / "manifests/runtime-asset-origins.json").read_text(encoding="utf-8"))["assets"][
        f"{INTRO_DIRECTORY}/{INTRO_FILE}"]
    assert origin["expected_sha256"] == hashlib.sha256(data).hexdigest()
    assert origin["ai_generated"] == {"model": "Seedance 2.5", "disclosure": "Settings -> About (start page and workbench)",
                                      "visible_watermark_added": False}
    contract = (REPO / "tools/package_contract.py").read_text(encoding="utf-8")
    required = contract[contract.index("REQUIRED_FILES = ("):contract.index("REQUIRED_ARCHIVE_MODULES")]
    assert '"theme/intro/leo-intro.mp4"' in required

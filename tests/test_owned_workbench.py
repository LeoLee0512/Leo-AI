import io
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from leo_shell.workbench import WorkbenchGateway, route
from leo_shell.theme_runtime import ThemeRuntime, MAX_SAFE_SHELL_HTML_BYTES


@pytest.mark.parametrize("payload", [
    {"operation":"fetch", "url":"https://example.org"},
    {"operation":"frame", "frameId":"../model-profiles"},
    {"operation":"send", "frameId":"f-1", "text":""},
    {"operation":"messages", "frameId":"f-1", "before":True},
    {"operation":"cancel", "frameId":"f-1"},
])
def test_workbench_rejects_unscoped_or_malformed_requests(payload):
    with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
        route(payload)


def test_cancel_keeps_exact_execution_identity():
    method, path, body = route({"operation":"cancel","frameId":"f-1","executionId":"exec-3",
                                "owner":{"kind":"agent","id":"job-2"}})
    assert (method,path)==("POST","/frames/f-1/cancel")
    assert body=={"execution_id":"exec-3","owner":{"kind":"agent","id":"job-2"}}


def test_send_requires_reviewed_model_and_reasoning_snapshot():
    base = {"operation":"send", "frameId":"f-1", "text":"hello"}
    with pytest.raises(ValueError):
        route(base)
    binding = {"profile_id":"mp-leo-test", "revision":3}
    reasoning = {"choice":"default", "capability_revision":"cap-v2"}
    _, _, body = route({**base, "modelBinding":binding, "reasoningSelection":reasoning})
    assert body["model_binding"] == binding
    assert body["reasoning_selection"] == reasoning
    assert body["input_data"]["request"] == "hello"


def test_native_transport_keeps_token_out_of_response():
    observed=[]
    class Opener:
        def open(self, request, timeout):
            observed.append(request)
            return io.BytesIO(b'{"frames":[]}')
    gateway=WorkbenchGateway(lambda:'http://127.0.0.1:8760/?token=test-private-token',Opener())
    result=gateway.request({"operation":"frames"})
    assert result=={"ok":True,"data":{"frames":[]}}
    assert observed[0].get_header('Authorization')=='Bearer test-private-token'
    assert 'test-private-token' not in observed[0].full_url
    assert 'test-private-token' not in json.dumps(result)


def test_native_transport_does_not_reflect_http_body():
    class Opener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url,400,'secret',{},io.BytesIO(b'api-key-secret'))
    gateway=WorkbenchGateway(lambda:'http://127.0.0.1:8760/?token=private',Opener())
    with pytest.raises(ValueError,match='^WORKBENCH_REQUEST_FAILED$'):
        gateway.request({"operation":"projects"})


def test_credential_failure_is_not_misreported_as_busy():
    class Opener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url,409,'private',{},io.BytesIO(
                b'{"code":"MODEL_CREDENTIALS_NOT_READY","message":"private detail"}'))
    gateway=WorkbenchGateway(lambda:'http://127.0.0.1:8760/?token=private',Opener())
    with pytest.raises(ValueError,match='^MODEL_CREDENTIALS_NOT_READY$'):
        gateway.request({"operation":"projects"})


def test_owned_document_is_self_contained_and_under_native_budget():
    html=ThemeRuntime(Path(__file__).resolve().parents[1]/'stage').render_workbench()
    assert len(html.encode())<MAX_SAFE_SHELL_HTML_BYTES
    assert 'src="http' not in html and 'href="http' not in html
    assert 'id="home-view"' in html and 'id="chat-view"' in html
    assert '__LEO_WORKBENCH_' not in html and '__LEO_RESEARCH_JS__' not in html
    assert 'window.LeoWorkbench' in html


def test_regular_navigation_never_loads_the_upstream_document():
    from leo_shell.ui import DesktopUI
    loaded=[]
    theme=SimpleNamespace(render_workbench=lambda:'<html>Leo workbench</html>')
    ui=DesktopUI(None,None,theme,None)
    ui._window=SimpleNamespace(load_html=loaded.append,load_url=lambda *_:pytest.fail('upstream navigation'))
    assert ui.navigate('http://127.0.0.1:8760/?token=private') is True
    assert loaded==['<html>Leo workbench</html>']
    assert not hasattr(ui, '_backend_pending'), 'no upstream page is ever pending any more'
    assert ui.navigate('https://example.org') is False
    assert len(loaded)==1


# ---- notebook: Leo's own read-only view of what a conversation computed -------

from leo_shell.workbench import preview_payload, shape_artifacts, shape_kernel, shape_notebook

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


@pytest.mark.parametrize("operation,path", [
    ("notebook", "/frames/f-1/execution-log"),
    ("kernel", "/frames/f-1/kernel"),
    ("artifacts", "/frames/f-1/artifacts"),
])
def test_notebook_operations_are_fixed_read_only_routes(operation, path):
    assert route({"operation": operation, "frameId": "f-1"}) == ("GET", path, None)


@pytest.mark.parametrize("artifact", ["../frames", "a-1/versions", "", None, "a" * 129])
def test_artifact_preview_takes_an_identifier_never_a_path(artifact):
    with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
        route({"operation": "artifact_preview", "frameId": "f-1", "artifactId": artifact})


def test_notebook_keeps_only_rendered_fields_and_trims_output():
    raw = {"kernels": ["python"], "entries": [
        {"cell_index": 3, "language": "python", "status": "ok", "source": "print(1)", "stdout": "x" * 70000,
         "stderr": "", "error": "", "figures": ["a.png", 5], "files_written": ["a.png"], "attempt": 2,
         "attempt_count": 2, "is_latest_attempt": True, "stale": True, "cpu_seconds": 1.5,
         "variable_writes": ["secret"], "code_hash": "h"},
        "not-a-row"]}
    shaped = shape_notebook(raw)
    entry = shaped["entries"][0]
    assert shaped["total"] == 1 and shaped["omitted"] == 0
    assert len(entry["stdout"]) == 64 * 1024 and entry["truncated"] is True
    assert entry["figures"] == ["a.png"] and entry["cellIndex"] == 3 and entry["stale"] is True
    assert "variable_writes" not in entry and "code_hash" not in entry
    with pytest.raises(ValueError, match="WORKBENCH_RESPONSE_INVALID"):
        shape_notebook({"entries": "nope"})


def test_artifact_list_and_kernel_are_reduced_to_known_values():
    listed = shape_artifacts([{"artifact_id": "a-0123456789ab", "filename": "u.png", "content_type": "image/png",
                               "size_bytes": 10, "checksum": "c", "latest_version_id": "v-abc123"},
                              {"artifact_id": "a-0123456789ac", "filename": "v.png", "latest_version_id": "../x"},
                              {"artifact_id": "../x"}, "junk"])
    assert listed == {"artifacts": [{"id": "a-0123456789ab", "filename": "u.png", "contentType": "image/png",
                                     "size": 10, "versionId": "v-abc123", "createdAt": "", "upload": False},
                                    {"id": "a-0123456789ac", "filename": "v.png", "contentType": "",
                                     "size": None, "versionId": "", "createdAt": "", "upload": False}]}
    assert shape_kernel({"state": "exploded", "alive": 1, "generation": -3}) == {"state": "none", "alive": False, "generation": 0}
    with pytest.raises(ValueError, match="WORKBENCH_RESPONSE_INVALID"):
        shape_artifacts({"artifacts": []})


def test_preview_recognises_images_by_their_bytes():
    meta = {"id": "a-1", "filename": "plot.png", "contentType": "image/png", "size": len(PNG)}
    assert preview_payload(PNG, "image/png", meta)["dataUri"].startswith("data:image/png;base64,")
    # A server calling HTML an image does not make it one.
    assert preview_payload(b"<script>alert(1)</script>", "image/png", meta)["kind"] == "binary"
    svg = preview_payload(b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml", {**meta, "filename": "f.svg"})
    assert svg["kind"] == "image" and svg["dataUri"].startswith("data:image/svg+xml;base64,")
    text = preview_payload(b"x" * (300 * 1024), "text/csv; charset=utf-8", {**meta, "filename": "d.csv"})
    assert text["kind"] == "text" and text["truncated"] is True and len(text["text"]) == 256 * 1024
    assert preview_payload(b"\0\1", "application/octet-stream", {**meta, "filename": "w.pt"})["kind"] == "binary"


class _Response(io.BytesIO):
    def __init__(self, body, content_type="application/json"):
        super().__init__(body)
        self.headers = {"Content-Type": content_type}


def test_preview_only_serves_an_artifact_listed_for_the_open_session():
    seen = []
    class Opener:
        def open(self, request, timeout):
            seen.append(request.full_url.split("/api/v1", 1)[1])
            if request.full_url.endswith("/frames/f-1/artifacts"):
                return _Response(b'[{"artifact_id":"a-0123456789ab","filename":"u.png","content_type":"image/png"}]')
            return _Response(PNG, "image/png")
    gateway = WorkbenchGateway(lambda: 'http://127.0.0.1:8760/?token=private', Opener())
    result = gateway.request({"operation": "artifact_preview", "frameId": "f-1", "artifactId": "a-0123456789ab"})
    assert result["data"]["kind"] == "image"
    assert seen == ["/frames/f-1/artifacts", "/artifacts/a-0123456789ab"]
    with pytest.raises(ValueError, match="^WORKBENCH_NOT_FOUND$"):
        gateway.request({"operation": "artifact_preview", "frameId": "f-1", "artifactId": "a-ffffffffffff"})
    assert seen[-1] == "/frames/f-1/artifacts", "an unlisted artifact must never be fetched"


def test_workbench_shares_the_start_page_painting_and_palette():
    stage = Path(__file__).resolve().parents[1] / 'stage'
    html = ThemeRuntime(stage).render_workbench()
    assert '__LEO_BG_' not in html and 'data:image/webp;base64,' in html
    assert 'id="notebook-view"' in html
    import re
    css = (stage / 'workbench.css').read_text(encoding='utf-8')
    shell = (stage / 'shell.html').read_text(encoding='utf-8')
    ink = re.search(r'html\[data-leo-theme="ink-autumn"\]\{(.*?)\}', shell, re.S).group(1)
    light = re.search(r':root\{(.*?)\}', css, re.S).group(1)
    token = lambda block, name: re.search(r'--' + name + r':([^;]+);', block).group(1).strip()
    for shell_name, workbench_name in (("bg", "paper"), ("surface", "surface"), ("ink", "ink"), ("accent", "accent"), ("muted", "muted")):
        assert token(ink, shell_name).lower() == token(light, workbench_name).lower(), workbench_name
    # The retired green workbench palette must not creep back.
    for retired in ("#233d32", "#315943", "#345b44", "#25382f"):
        assert retired not in css.lower()


def test_no_path_from_the_workbench_to_the_upstream_page():
    from leo_shell.api import ShellApi
    from leo_shell.ui import DesktopUI
    assert not hasattr(ShellApi, "open_computational_tools")
    assert not hasattr(DesktopUI, "open_computational_tools")
    assert not hasattr(DesktopUI, "_load_backend_url")
    stage = Path(__file__).resolve().parents[1] / 'stage'
    for name in ('workbench.js', 'workbench.html', 'shell.html'):
        text = (stage / name).read_text(encoding='utf-8')
        assert 'open_computational_tools' not in text and 'href="http' not in text, name


def test_manage_models_opens_the_start_page_with_its_drawer():
    from leo_shell.api import ShellApi
    from leo_shell.ui import DesktopUI
    rendered = []
    theme = SimpleNamespace(render_shell=lambda open_settings: rendered.append(open_settings) or '<html>start</html>')
    ui = DesktopUI(None, None, theme, SimpleNamespace(cancel_pending=lambda: None))
    ui._window = SimpleNamespace(load_html=lambda html: None)
    api = ShellApi(None, None, ui)
    assert api.open_model_settings() == {"ok": True}
    assert api.return_to_start() == {"ok": True}
    assert rendered == [True, False]


def _tokens(block):
    import re
    return {name: value.strip() for name, value in re.findall(r'--([a-z0-9-]+):(#[0-9A-Fa-f]{6})', block)}


def _luminance(hex_colour):
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a, b):
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


#: Every text colour the workbench puts on a background, per the stylesheet.
TEXT_PAIRS = [("ink", "paper"), ("ink-2", "paper"), ("muted", "paper"), ("muted", "surface"), ("ink", "surface-2"),
              ("on-accent", "accent"), ("rail-ink", "rail"), ("rail-muted", "rail"), ("ochre-ink", "ochre-wash"),
              ("bamboo-ink", "bamboo-wash"), ("indigo-ink", "indigo-wash"), ("cinnabar-ink", "cinnabar-wash"),
              ("slate-ink", "slate-wash"), ("danger", "danger-wash")]


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_workbench_text_meets_wcag_aa_in_both_modes(mode):
    import re
    css = (Path(__file__).resolve().parents[1] / 'stage' / 'workbench.css').read_text(encoding='utf-8')
    tokens = _tokens(re.search(r':root\{(.*?)\}', css, re.S).group(1))
    if mode == "dark":
        tokens.update(_tokens(re.search(r':root\[data-leo-mode="dark"\]\{(.*?)\}', css, re.S).group(1)))
    failures = {f"{fg}/{bg}": round(_contrast(tokens[fg], tokens[bg]), 2) for fg, bg in TEXT_PAIRS
                if _contrast(tokens[fg], tokens[bg]) < 4.5}
    assert not failures, failures


def test_dark_tokens_are_declared_identically_for_system_and_explicit_mode():
    import re
    css = (Path(__file__).resolve().parents[1] / 'stage' / 'workbench.css').read_text(encoding='utf-8')
    system = re.search(r':root:not\(\[data-leo-mode="light"\]\)\{(.*?)\}', css, re.S).group(1)
    explicit = re.search(r':root\[data-leo-mode="dark"\]\{(.*?)\}', css, re.S).group(1)
    assert _tokens(system) == _tokens(explicit)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_ink_autumn_has_no_cool_gradient(mode):
    """The frozen Ink Autumn rule (formerly checked on leo.css): no cool 'tech' gradient stop."""
    import re
    css = (Path(__file__).resolve().parents[1] / 'stage' / 'workbench.css').read_text(encoding='utf-8')
    tokens = _tokens(re.search(r':root\{(.*?)\}', css, re.S).group(1))
    if mode == "dark":
        tokens.update(_tokens(re.search(r':root\[data-leo-mode="dark"\]\{(.*?)\}', css, re.S).group(1)))
    gradients = re.findall(r'(?:linear|radial|conic)-gradient\([^;]*', css)
    assert gradients, "the check must see the workbench's gradients"
    for fragment in gradients:
        resolved = re.sub(r'var\(--([a-z0-9-]+)\)', lambda m: tokens.get(m.group(1), m.group(0)), fragment)
        for colour in re.findall(r'#([0-9A-Fa-f]{6})\b', resolved):
            r, g, b = (int(colour[i:i + 2], 16) for i in (0, 2, 4))
            assert not b > r + 20, f"cool gradient stop #{colour} in {fragment[:70]}"


# ---- message actions: copy, rate, forward --------------------------------------

from leo_shell.workbench import shape_feedback


def test_feedback_routes_are_fixed_and_validated():
    assert route({"operation": "feedback", "frameId": "f-1"}) == ("GET", "/frames/f-1/feedback", None)
    method, path, body = route({"operation": "set_feedback", "frameId": "f-1", "key": "m-2", "rating": "up"})
    assert (method, path, body) == ("POST", "/frames/f-1/feedback", {"key": "m-2", "rating": "up"})
    assert route({"operation": "set_feedback", "frameId": "f-1", "key": "m-2", "rating": None})[2]["rating"] is None
    for bad in ({"key": "../x", "rating": "up"}, {"key": "m-2", "rating": "love"}, {"key": "", "rating": "up"},
                {"key": "m" * 200, "rating": "down"}, {"rating": "up"}):
        with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
            route({"operation": "set_feedback", "frameId": "f-1", **bad})


def test_feedback_response_keeps_only_real_ratings():
    shaped = shape_feedback({"feedback": {"m-1": "up", "m-2": "down", "m-3": "meh", 7: "up"}})
    assert shaped == {"feedback": {"m-1": "up", "m-2": "down"}}
    with pytest.raises(ValueError, match="WORKBENCH_RESPONSE_INVALID"):
        shape_feedback({"feedback": []})


class _FakeClipboard:
    """Records the Win32 calls; ``busy`` makes OpenClipboard fail that many times."""

    def __init__(self, *, busy=0, set_fails=False):
        self.busy, self.set_fails, self.calls, self.data, self.freed = busy, set_fails, [], None, []

    def api(self):
        import ctypes
        fake = self

        class User32:
            def OpenClipboard(self, hwnd):
                fake.calls.append("open")
                if fake.busy:
                    fake.busy -= 1
                    return 0
                return 1
            def EmptyClipboard(self):
                fake.calls.append("empty"); return 1
            def SetClipboardData(self, fmt, handle):
                fake.calls.append(("set", fmt)); return 0 if fake.set_fails else handle
            def CloseClipboard(self):
                fake.calls.append("close"); return 1

        class Kernel32:
            buffers = {}
            def GlobalAlloc(self, flags, size):
                buffer = ctypes.create_string_buffer(size)
                handle = ctypes.addressof(buffer)
                self.buffers[handle] = buffer
                return handle
            def GlobalLock(self, handle):
                return handle
            def GlobalUnlock(self, handle):
                fake.data = bytes(self.buffers[handle])
                return 1
            def GlobalFree(self, handle):
                fake.freed.append(handle)

        return User32(), Kernel32()


def test_clipboard_writes_unicode_text():
    from leo_shell.clipboard import set_text
    board = _FakeClipboard()
    set_text("边界条件 u(0)=0", api=board.api())
    assert board.calls == ["open", "empty", ("set", 13), "close"]
    assert board.data == "边界条件 u(0)=0\0".encode("utf-16-le")


def test_clipboard_retries_while_busy_and_frees_on_failure():
    from leo_shell.clipboard import ClipboardError, set_text
    board = _FakeClipboard(busy=2)
    set_text("x", api=board.api())
    assert board.calls[:3] == ["open", "open", "open"]
    failing = _FakeClipboard(set_fails=True)
    with pytest.raises(ClipboardError, match="CLIPBOARD_UNAVAILABLE"):
        set_text("x", api=failing.api())
    assert failing.freed and failing.calls[-1] == "close", "the handle is ours to free, and the clipboard is always closed"
    with pytest.raises(ClipboardError, match="CLIPBOARD_BUSY"):
        set_text("x", api=_FakeClipboard(busy=99).api())
    with pytest.raises(ClipboardError, match="CLIPBOARD_TEXT_INVALID"):
        set_text("x" * (1024 * 1024 + 1), api=_FakeClipboard().api())


def test_copy_text_api_rejects_anything_but_text():
    from leo_shell.api import ShellApi
    api = ShellApi(None, None, None)
    for payload in (None, {}, {"text": 5}, "text"):
        assert api.copy_text(payload) == {"ok": False, "message": "CLIPBOARD_TEXT_INVALID"}


def test_changelog_holds_no_stray_control_characters():
    """Escapes typed through a shell once turned '\f' in 'theme\fonts' into a form feed."""
    import re
    text = (Path(__file__).resolve().parents[1] / 'CHANGELOG.md').read_text(encoding='utf-8')
    head = text[:text.index('## 原文附录')]
    assert not re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', head)

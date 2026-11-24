"""3.1.0: web links, file upload, 「终端」, 「网页」 and 「插件」 through the bounded gateway."""
import base64
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from leo_shell import workbench
from leo_shell.extensions import Extensions
from leo_shell.web_links import LINK_INVALID, LinkOpener, describe_host, resolve_redirects, validate_url
from leo_shell.workbench import (TERMINAL_TIMEOUT, UPLOAD_MAX_BYTES, WorkbenchGateway, route, shape_connectors,
                                 shape_notebook, shape_probe, shape_skills, shape_steps, terminal_code,
                                 upload_content, upload_name)

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- web links

@pytest.mark.parametrize("url", ["https://example.com/x", "http://arxiv.org/abs/2104.08426?x=1#y",
                                 "https://中文.example.org/路径", "https://8.8.8.8/", "https://[2606:4700::1111]/"])
def test_public_web_addresses_are_accepted(url):
    assert validate_url(url).lower().startswith(("http://", "https://"))


@pytest.mark.parametrize("url", ["file:///C:/Windows/win.ini", "javascript:alert(1)", "ms-settings:privacy", "ftp://example.com/",
                                 "https://good.example@evil.example/", "https://user:pw@example.com/",
                                 "http://localhost:8760/?token=t", "http://127.0.0.1:8760/", "http://127.1/", "http://2130706433/",
                                 "http://0x7f.0.0.1/", "http://[::1]/", "http://10.0.0.2/", "http://192.168.1.1/", "http://169.254.1.1/",
                                 "http://router/", "http://nas.local/", "http://app.localhost/",
                                 "http://localtest.me/", "http://127.0.0.1.nip.io:8080/v1", "http://app.lvh.me/",
                                 "http://127.0.0.1%2e/", "http://10.1.2.3%2e/", "http://192.168.1.20%2e/",
                                 "http://169.254.169.254%2e/", "http://0x7f.0.0.1%2e/", "http://0177.0.0.1%2e/",
                                 "http://example.com\u202e.evil.com/",
                                 "https://example.com/a b",
                                 "https://example.com/\n", "https://example.com:99999/", "", None, 5, "x" * 3000])
def test_anything_but_a_public_web_address_is_refused(url):
    with pytest.raises(ValueError, match=f"^{LINK_INVALID}$"):
        validate_url(url)


def test_a_name_that_resolves_to_this_machine_is_refused(monkeypatch):
    monkeypatch.setattr("leo_shell.web_links._lookup", lambda host: [(None, None, None, "", ("127.0.0.1", 0))])
    with pytest.raises(ValueError, match=f"^{LINK_INVALID}$"):
        validate_url("http://loop.example/x")
    monkeypatch.setattr("leo_shell.web_links._lookup", lambda host: [(None, None, None, "", ("93.184.216.34", 0))])
    assert validate_url("http://loop.example/x") == "http://loop.example/x"
    monkeypatch.setattr("leo_shell.web_links._lookup", lambda host: "timeout")
    with pytest.raises(ValueError, match=f"^{LINK_INVALID}$"):
        validate_url("http://slow.example/x")


def test_an_internationalised_site_is_shown_with_its_ascii_name():
    assert describe_host("https://аpple.com/") .endswith("（xn--pple-43d.com）")
    assert describe_host("https://example.com/") == "example.com"


def test_a_link_opens_only_after_the_native_confirmation():
    launched, asked = [], []

    def confirm(window, title, text):
        asked.append((window, title, text))
        return answer

    opener = LinkOpener(lambda: "window", confirm=confirm, launch=lambda url: launched.append(url) or True,
                        resolve=lambda url: url)
    answer = False
    assert opener.open({"url": "https://example.com/x"}) == {"opened": False}
    assert launched == [] and asked[0][0] == "window" and "https://example.com/x" in asked[0][2]
    answer = True
    assert opener.open({"url": "https://example.com/x"}) == {"opened": True}
    assert launched == ["https://example.com/x"]
    with pytest.raises(ValueError):
        opener.open({"url": "http://127.0.0.1:8760/"})
    assert len(asked) == 2, "a refused address never reaches the dialog"


def test_a_redirect_onto_this_machine_is_refused_before_the_browser(monkeypatch):
    monkeypatch.setattr("leo_shell.web_links._lookup", lambda host: [(None, None, None, "", ("93.184.216.34", 0))])

    def probe(url):
        if url == "https://example.com/go":
            return 302, "http://127.0.0.1%2e/secret"
        return 200, None

    with pytest.raises(ValueError, match=f"^{LINK_INVALID}$"):
        resolve_redirects("https://example.com/go", probe=probe)


def test_a_public_redirect_is_the_address_that_opens(monkeypatch):
    monkeypatch.setattr("leo_shell.web_links._lookup", lambda host: [(None, None, None, "", ("93.184.216.34", 0))])

    def probe(url):
        if url == "https://example.com/a":
            return 302, "https://example.org/b"
        return 200, None

    assert resolve_redirects("https://example.com/a", probe=probe) == "https://example.org/b"


def test_the_desktop_registers_link_and_connector_operations(tmp_path):
    api = SimpleNamespace(_ui=SimpleNamespace(_window="w"))
    ext = Extensions(api, SimpleNamespace(user=tmp_path), lambda: "http://127.0.0.1:8760/?token=t", start=False)
    try:
        assert "open_link" in workbench._LOCAL_HANDLERS and "connector_add" in workbench._LOCAL_HANDLERS
        assert ext.links._window_getter() == "w"
    finally:
        ext.close()
    assert "open_link" not in workbench._LOCAL_HANDLERS and "connector_add" not in workbench._LOCAL_HANDLERS


# ---------------------------------------------------------------- upload

@pytest.mark.parametrize("given,expected", [("data.csv", "data.csv"), ("实验 记录(1).txt", "实验_记录_1.txt"),
                                            (r"C:\Users\me\secret\..\报告.PDF", "报告.PDF"), ("../../etc/passwd", "passwd"),
                                            (".bashrc", "bashrc"), ("a.tar.gz", "a.tar.gz"), ("noext", "noext"),
                                            ("图 1.png", "图_1.png"), ("x.p<>y", "x.py"), ("???.csv", "file.csv")])
def test_upload_names_stay_plain(given, expected):
    assert upload_name(given) == expected


def test_upload_content_is_checked_strictly():
    assert upload_content(base64.b64encode(b"x,y\n1,2\n").decode()) == "eCx5CjEsMgo="
    for bad in ("not base64!", "eCx5=CjEs", 123, None):
        with pytest.raises(ValueError):
            upload_content(bad)
    with pytest.raises(ValueError, match="^WORKBENCH_UPLOAD_TOO_LARGE$"):
        upload_content(base64.b64encode(b"\0" * (UPLOAD_MAX_BYTES + 1)).decode())


def test_the_upload_route_never_forwards_a_project_or_workspace():
    method, path, body = route({"operation": "upload", "frameId": "f1", "filename": "a b.csv", "data": "eA==",
                                "projectId": "p-other", "workspace_frame_id": "f-other"})
    assert (method, path) == ("POST", "/uploads")
    assert body == {"frame_id": "f1", "filename": "a_b.csv", "content_base64": "eA=="}


def test_an_upload_gets_a_longer_timeout_and_an_ordinary_call_keeps_the_old_signature():
    seen = []

    class Gateway(WorkbenchGateway):
        def _exchange(self, method, path, body, limit, timeout=None):
            seen.append((path, timeout))
            return json.dumps({"artifact_id": "a-1", "filename": "a.csv"}).encode(), "application/json"

    g = Gateway(lambda: "http://127.0.0.1:1/?token=t")
    assert g.request({"operation": "upload", "frameId": "f1", "filename": "a.csv", "data": "eA=="})["data"] == {"id": "a-1", "filename": "a.csv"}
    assert seen == [("/uploads", 180)]


# ---------------------------------------------------------------- terminal

TRICKY = ['echo "hi" \'there\'', 'printf "a\\nb" && ls -la\nwhoami', 'echo 😀 中文 \\ back\\\\slash',
          '"); import os; os.system("x"); ("', "'''\n\"\"\"end", "echo $(whoami) `id` ${HOME}"]


@pytest.mark.parametrize("command", TRICKY)
def test_a_typed_command_reaches_host_bash_unchanged_and_never_becomes_code(command):
    seen = []

    class Host:
        def bash(self, text, timeout):
            seen.append((text, timeout))
            return {"exit_code": 3, "stdout": "OUT", "stderr": "", "workdir": "/w"}

    code = terminal_code(command, "0123456789abcdef")
    out = io.StringIO()
    namespace = {"host": Host()}
    with contextlib.redirect_stdout(out):
        exec(compile(code, "<cell>", "exec"), namespace)
    assert seen == [(command, TERMINAL_TIMEOUT)]
    assert out.getvalue() == "OUT\n[exit 3]\n"
    assert set(namespace) == {"host", "__builtins__"}, "the cell leaves nothing behind in the kernel"
    assert workbench._terminal_cell(code) == ("0123456789abcdef", command)


def test_a_refused_command_is_reported_inside_the_cell():
    class Host:
        def bash(self, text, timeout):
            raise PermissionError("Permission denied: bash")

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(compile(terminal_code("ls", "0123456789abcdef"), "<cell>", "exec"), {"host": Host()})
    assert out.getvalue() == "[没有执行] Permission denied: bash\n"


def test_the_terminal_route_writes_the_cell_itself():
    method, path, body = route({"operation": "terminal_run", "frameId": "f1", "runId": "0123456789abcdef", "command": " ls -la ",
                                "code": "import os"})
    assert (method, path) == ("POST", "/frames/f1/kernel/execute")
    assert body["language"] == "python" and body["execution_id"] == "leo-term-0123456789abcdef"
    assert body["code"] == terminal_code("ls -la", "0123456789abcdef")
    for bad in ({"runId": "XYZ", "command": "ls"}, {"runId": "0123456789abcdef", "command": ""},
                {"runId": "0123456789abcdef", "command": "a\x00b"}, {"runId": "0123456789abcdef", "command": "x" * 8001}):
        with pytest.raises(ValueError):
            route({"operation": "terminal_run", "frameId": "f1", **bad})


def test_the_bridge_enables_the_notebook_repl_for_the_terminal():
    script = (ROOT / "bridge/leo_bridge.sh").read_text(encoding="utf-8")
    assert 'OPENAI4S_NOTEBOOK_REPL="1"' in script
    assert "OPENAI4S_NOTEBOOK_REPL\n" in script.split("export PATH PYTHONPATH", 1)[1].split("\n", 1)[0] + "\n"


def test_the_bridge_lets_built_in_connectors_import_the_active_source():
    script = (ROOT / "bridge/leo_bridge.sh").read_text(encoding="utf-8")
    body = script.split("link_connector_source() {", 1)[1].split("\n}\n", 1)[0]
    assert "leo-openai4s.pth" in body and "getusersitepackages" in body and "-u PYTHONPATH" in body
    assert 'case "$site_dir" in "${HOME:-/nonexistent}"/*)' in body, "only ever writes under the user's own home"
    start = script.split("\nstart)\n", 1)[1]
    assert start.index("  link_connector_source\n") < start.index('daemon_running "$status_out"'), "also refreshed for a daemon already running"


def test_notebook_cells_carry_their_origin_and_terminal_command():
    cell = terminal_code("ls", "0123456789abcdef")
    shaped = shape_notebook({"entries": [{"source": cell, "origin": "user", "stdout": "a\n[exit 0]\n"},
                                         {"source": "print(1)", "origin": "agent"},
                                         {"source": "# leo-terminal nothex x", "origin": "user"}]})["entries"]
    assert [(e["origin"], e["terminalRun"], e["command"]) for e in shaped] == [
        ("user", "0123456789abcdef", "ls"), ("agent", None, None), ("user", None, None)]


# ---------------------------------------------------------------- steps: commands and web

def test_steps_become_a_command_log_and_a_web_log():
    long = "x" * 5000
    rows = [
        {"seq": 1, "kind": "bash", "status": "done", "created_at": 1.5, "summary": "exit 0",
         "input": {"command": "ls", "command_sha256": "h", "cwd": "/ws"},
         "output": {"exit_code": 0, "duration_ms": 12, "stdout": {"preview": long, "truncated": True}, "stderr": {"preview": "warn"},
                    "workspace_diff": {"created": ["a.txt"], "modified": ["b.txt"], "deleted": []}}},
        {"seq": 2, "kind": "bash", "status": "error", "input": {"command": "rm -rf /"}, "output": {"error": "Permission denied: no"}},
        {"seq": 3, "kind": "search", "status": "done", "input": {"query": "pinn"}, "output": {"source": "ddg", "results": [
            {"title": "A", "url": "https://a.example/", "snippet": "s"}, {"title": "B", "url": "javascript:alert(1)", "snippet": ""}]}},
        {"seq": 4, "kind": "fetch", "status": "done", "input": {"url": "https://a.example/p"}, "output": {"content": "内容" * 400, "url": "file:///etc"}},
        {"seq": 5, "kind": "python", "status": "done", "input": {"code": "secret"}, "output": {}},
        "junk",
    ]
    shaped = shape_steps({"steps": rows})
    first, refused = shaped["commands"]
    assert first["command"] == "ls" and first["exitCode"] == 0 and first["durationMs"] == 12
    assert len(first["stdout"]) == 4000 and first["stdoutTruncated"] is True and first["stderr"] == "warn"
    assert first["changed"] == ["a.txt", "b.txt"]
    assert refused["exitCode"] is None and refused["error"] == "Permission denied: no"
    search, fetch = shaped["web"]
    assert [r["url"] for r in search["results"]] == ["https://a.example/", None], "only web addresses can be opened"
    assert fetch["url"] == "https://a.example/p" and fetch["finalUrl"] is None and len(fetch["excerpt"]) == 600 and fetch["chars"] == 800
    assert shaped["lastSeq"] == 5 and shaped["capped"] is False
    assert "secret" not in json.dumps(shaped), "other step kinds never reach the page"
    assert shape_steps({"steps": [{"seq": i, "kind": "note"} for i in range(800)]})["capped"] is True
    with pytest.raises(ValueError):
        shape_steps({"nope": []})


def test_the_steps_route_is_read_with_the_large_limit():
    assert route({"operation": "steps", "frameId": "f1"}) == ("GET", "/frames/f1/steps", None)
    assert "steps" in workbench._LARGE_OPERATIONS


# ---------------------------------------------------------------- plugins

def test_plugin_routes_are_fixed_and_names_are_checked():
    assert route({"operation": "skills"}) == ("GET", "/skills/catalog", None)
    assert route({"operation": "skill_toggle", "name": "lean-math", "enabled": False}) == (
        "PUT", "/skills/catalog/lean-math/enabled", {"enabled": False})
    assert route({"operation": "skill_delete", "name": "a.b_c"}) == ("DELETE", "/skills/a.b_c", None)
    assert route({"operation": "skill_import", "content": "---\nname: x\n---\nbody"})[2] == {"content": "---\nname: x\n---\nbody"}
    assert route({"operation": "connector_probe", "id": "example"}) == ("POST", "/connectors/example/probe", {})
    for bad in ({"operation": "skill_toggle", "name": "../x", "enabled": True}, {"operation": "skill_toggle", "name": "x", "enabled": "yes"},
                {"operation": "connector_delete", "id": "a/b"}, {"operation": "skill_import", "content": "x" * (1024 * 1024 + 1)}):
        with pytest.raises(ValueError):
            route(bad)
    assert not any(op in {"connector_add", "connector_call", "connector_edit"} for op in ("skills",))
    with pytest.raises(ValueError):
        route({"operation": "connector_call", "id": "example"})


def test_connectors_reach_the_page_without_their_command_or_environment():
    shaped = shape_connectors({"connectors": [
        {"connector_id": "example", "name": "Example", "description": "demo", "command": ["python", "-m", "x"], "args": ["--token", "SECRET"],
         "enabled": True, "env_keys": ["API_KEY"], "has_env": True, "command_display": "python -m x --token SECRET", "managed": False},
        {"connector_id": "custom", "name": "Mine", "description": "d", "command": ["npx", "tool"], "enabled": 0},
        {"connector_id": "../bad"}]})
    text = json.dumps(shaped)
    assert "SECRET" not in text and "python" not in text and "API_KEY" not in text and "npx" not in text
    example, custom = shaped["connectors"]
    assert example["name"] == "示例连接器" and example["leoChecked"] and example["hasCredentials"]
    assert custom["leoChecked"] is False and custom["enabled"] is False
    assert shaped["available"] == [], "an added connector is not offered again"
    assert shape_connectors({"connectors": []})["available"][0]["id"] == "example"


def test_a_failed_probe_says_nothing_else():
    assert shape_probe({"ok": False, "error": "spawn failed: --token SECRET"}) == {"ok": False, "tools": []}
    assert shape_probe({"ok": True, "tools": [{"name": "echo", "inputSchema": {}}, {"name": "now"}, "junk"]}) == {
        "ok": True, "tools": ["echo", "now"], "count": 2}


def test_skills_are_projected_for_the_list():
    shaped = shape_skills({"skills": [{"name": "gpu-thing", "displayName": "GPU", "description": "d" * 900, "scope": "bundled",
                                       "editable": False, "enabled": True, "readiness": {"state": "needs_setup", "missing": ["gpu"]}},
                                      {"name": 3}]})["skills"]
    assert shaped == [{"name": "gpu-thing", "title": "GPU", "description": "d" * 400, "scope": "bundled", "collection": "",
                       "editable": False, "enabled": True, "ready": "needs_setup", "missing": ["gpu"]}]


def test_only_a_leo_checked_connector_can_be_added_and_its_command_comes_from_the_daemon():
    calls = []
    directory = [{"id": "example", "name": "Example", "description": "demo", "command": ["/py/bin/python", "-m", "openai4s.mcp_servers.example_server"]},
                 {"id": "filesystem", "name": "FS", "command": ["npx", "-y", "x"]}]

    class Gateway(WorkbenchGateway):
        def _exchange(self, method, path, body, limit, timeout=None):
            calls.append((method, path, body))
            if path == "/connectors/directory":
                return json.dumps({"directory": directory}).encode(), "application/json"
            return b'{"connector_id":"example"}', "application/json"

    g = Gateway(lambda: "http://127.0.0.1:1/?token=t")
    assert g.add_connector({"id": "example", "command": ["evil"]}) == {"ok": True}
    assert calls[-1] == ("POST", "/connectors", {"connector_id": "example", "name": "Example", "description": "demo",
                                                  "command": ["/py/bin/python", "-m", "openai4s.mcp_servers.example_server"], "enabled": True})
    for ident in ("filesystem", "custom", None):
        with pytest.raises(ValueError):
            g.add_connector({"id": ident})
    directory[0]["env"] = {"KEY": "v"}
    with pytest.raises(ValueError):
        g.add_connector({"id": "example"})

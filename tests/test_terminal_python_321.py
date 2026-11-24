"""3.2.1: 「终端」 is the person's own shell (not the AI's, no approvals); 「Python」 runs their code as a
kernel cell. The shell is exercised with a fake process that speaks the relay's JSON lines."""
import base64
import json
import queue
import threading

import pytest

from leo_shell import user_terminal, workbench
from leo_shell.user_terminal import BOOT, RELAY_SOURCE, UserTerminals


class FakeStdin:
    def __init__(self):
        self.lines = []
        self.closed = False
        self._buffer = b""

    def write(self, data):
        if self.closed:
            raise ValueError("closed")
        self._buffer += data

    def flush(self):
        *done, self._buffer = self._buffer.split(b"\n")
        self.lines += [line.decode("utf-8") for line in done]

    def close(self):
        self.closed = True


class FakeStdout:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        while True:
            item = self.queue.get()
            if item is None:
                return
            yield item


class FakeProcess:
    def __init__(self, argv, **kwargs):
        self.argv = argv
        self.kwargs = kwargs
        self.stdin = FakeStdin()
        self.stdout = FakeStdout()
        self.killed = False

    def emit(self, message):
        self.stdout.queue.put((json.dumps(message) + "\n").encode("utf-8"))

    def end(self):
        self.stdout.queue.put(None)

    def wait(self, timeout=None):
        self.end()
        return 0

    def kill(self):
        self.killed = True

    def sent(self):
        return [json.loads(line) for line in self.stdin.lines[1:]]


def wait_for(check, timeout=3):
    done = threading.Event()
    for _ in range(int(timeout / 0.01)):
        if check():
            return
        done.wait(0.01)
    raise AssertionError("condition not reached")


@pytest.fixture
def terminals():
    made = []

    def popen(argv, **kwargs):
        made.append(FakeProcess(argv, **kwargs))
        return made[-1]

    shells = UserTerminals("Ubuntu-24.04", popen=popen)
    yield shells, made
    shells.close()


def out(text_bytes):
    return {"t": "out", "d": base64.b64encode(text_bytes).decode("ascii")}


def test_the_relay_and_its_boot_line_are_valid_python():
    compile(RELAY_SOURCE, "relay", "exec")
    compile(BOOT, "boot", "exec")
    # The relay runs a login-free interactive bash in the conversation's workspace, nothing else.
    assert '"bash", ["bash", "-i"]' in RELAY_SOURCE
    assert "agent-workspaces" in RELAY_SOURCE and "os.chdir(workspace)" in RELAY_SOURCE


def test_a_shell_opens_in_wsl_with_the_relay_on_stdin_and_streams_output(terminals):
    shells, made = terminals
    first = shells.handle({"operation": "terminal_open", "frameId": "f-1", "rows": 24, "cols": 80})
    assert first["alive"] is True and first["text"] == ""
    process = made[0]
    assert process.argv == ["wsl.exe", "-d", "Ubuntu-24.04", "-e", "/usr/bin/python3", "-u", "-c", BOOT]
    assert json.loads(process.stdin.lines[0]) == RELAY_SOURCE
    assert process.sent() == [{"t": "start", "frame": "f-1", "rows": 24, "cols": 80}]
    process.emit({"t": "ready", "cwd": "/home/leo/ws/f-1", "pid": 7})
    # A character split across two chunks is decoded whole.
    raw = "héllo 你好\r\n".encode("utf-8")
    process.emit(out(raw[:8]))
    process.emit(out(raw[8:]))
    wait_for(lambda: shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 0})["next"] == 2)
    got = shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 0})
    assert got["text"] == "héllo 你好\r\n" and got["cwd"] == "/home/leo/ws/f-1" and got["more"] is False
    assert shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 2})["text"] == ""
    # Typing goes to the shell as typed.
    shells.handle({"operation": "terminal_input", "frameId": "f-1", "data": "ls -la\r"})
    shells.handle({"operation": "terminal_resize", "frameId": "f-1", "rows": 40, "cols": 120})
    sent = process.sent()
    assert base64.b64decode(sent[1]["d"]).decode("utf-8") == "ls -la\r"
    assert sent[2] == {"t": "resize", "rows": 40, "cols": 120}
    # Opening again (the tab shown again) reuses the same shell.
    shells.handle({"operation": "terminal_open", "frameId": "f-1"})
    assert len(made) == 1


def test_each_conversation_has_its_own_shell_and_restart_replaces_it(terminals):
    shells, made = terminals
    shells.handle({"operation": "terminal_open", "frameId": "f-1"})
    shells.handle({"operation": "terminal_open", "frameId": "f-2"})
    assert [p.sent()[0]["frame"] for p in made] == ["f-1", "f-2"]
    shells.handle({"operation": "terminal_restart", "frameId": "f-1"})
    assert made[0].stdin.closed and len(made) == 3 and made[2].sent()[0]["frame"] == "f-1"
    shells.close()
    assert all(p.stdin.closed for p in made)


def test_an_ended_shell_reports_its_exit_and_is_reopened_on_the_next_open(terminals):
    shells, made = terminals
    shells.handle({"operation": "terminal_open", "frameId": "f-1"})
    made[0].emit(out(b"exit\r\n"))
    made[0].emit({"t": "exit", "code": 0})
    made[0].end()
    wait_for(lambda: not shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 0})["alive"])
    got = shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 0})
    assert got["exitCode"] == 0 and got["text"] == "exit\r\n"
    with pytest.raises(ValueError, match="TERMINAL_NOT_RUNNING"):
        shells.handle({"operation": "terminal_input", "frameId": "f-1", "data": "ls\r"})
    assert shells.handle({"operation": "terminal_open", "frameId": "f-1"})["alive"] is True
    assert len(made) == 2


def test_requests_are_checked(terminals):
    shells, made = terminals
    for bad in ("", "../x", "f 1", None, "a" * 101):
        with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
            shells.handle({"operation": "terminal_open", "frameId": bad})
    with pytest.raises(ValueError, match="TERMINAL_NOT_RUNNING"):
        shells.handle({"operation": "terminal_input", "frameId": "f-9", "data": "ls\r"})
    shells.handle({"operation": "terminal_open", "frameId": "f-1"})
    for data in ("", "a\x00b", "x" * (user_terminal.MAX_INPUT + 1), 5):
        with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
            shells.handle({"operation": "terminal_input", "frameId": "f-1", "data": data})
    # The page's longest line (8000 characters) plus its Enter is accepted.
    shells.handle({"operation": "terminal_input", "frameId": "f-1", "data": "x" * 8000 + "\r"})
    with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
        shells.handle({"operation": "terminal_run", "frameId": "f-1"})
    # Out-of-range sizes fall back to the defaults.
    shells.handle({"operation": "terminal_open", "frameId": "f-3", "rows": 9999, "cols": True})
    assert made[-1].sent()[0] == {"t": "start", "frame": "f-3", "rows": 30, "cols": 100}


def test_old_output_is_dropped_past_the_limit_and_the_page_is_told(terminals, monkeypatch):
    monkeypatch.setattr(user_terminal, "MAX_BUFFER", 100)
    shells, made = terminals
    shells.handle({"operation": "terminal_open", "frameId": "f-1"})
    for i in range(5):
        made[0].emit(out(bytes([97 + i]) * 40))
    wait_for(lambda: shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 0})["next"] == 5)
    got = shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 0})
    assert got["truncated"] is True and got["text"] == "d" * 40 + "e" * 40
    assert shells.handle({"operation": "terminal_read", "frameId": "f-1", "after": 3})["truncated"] is False


def test_the_terminal_operations_are_local_and_none_of_them_runs_through_the_ai():
    from leo_shell import extensions
    assert set(extensions.TERMINAL_OPERATIONS) == {"terminal_open", "terminal_input", "terminal_read", "terminal_resize", "terminal_restart"}
    assert "terminal_run" not in extensions.TERMINAL_OPERATIONS


def test_python_cells_run_the_persons_code_marked_and_can_be_interrupted():
    run = "0123456789abcdef"
    method, path, body = workbench.route({"operation": "python_run", "frameId": "f-1", "runId": run, "code": "x = 1\nprint(x)"})
    assert (method, path) == ("POST", "/frames/f-1/kernel/execute")
    assert body == {"code": "# leo-python " + run + "\nx = 1\nprint(x)", "language": "python", "execution_id": "leo-py-" + run}
    method, path, body = workbench.route({"operation": "python_interrupt", "frameId": "f-1", "runId": run})
    assert (method, path) == ("POST", "/frames/f-1/kernel/interrupt")
    assert body == {"execution_id": "leo-py-" + run, "owner": {"kind": "user_repl", "id": "leo-py-" + run}}
    for code in ("", "   ", "a\x00", "x" * 100_001, None):
        with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
            workbench.route({"operation": "python_run", "frameId": "f-1", "runId": run, "code": code})
    with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
        workbench.route({"operation": "python_run", "frameId": "f-1", "runId": "../x", "code": "1"})
    # A cell that holds no running lease is not "stopped": the page is told.
    shaper = workbench._SHAPERS["python_interrupt"]
    assert shaper({"ok": True, "frame_id": "f-1"}) == {"ok": True}
    with pytest.raises(ValueError, match="PYTHON_INTERRUPT_REFUSED"):
        shaper({"ok": False, "reason": "exact kernel interrupt requires execution_id"})


def test_the_notebook_shows_a_python_panel_cell_as_the_persons_code_without_the_marker():
    run = "0123456789abcdef"
    shaped = workbench.shape_notebook({"entries": [
        {"origin": "user", "source": "# leo-python " + run + "\nprint(3)", "stdout": "3\n", "status": "ok"},
        {"origin": "user", "source": "# leo-python not-a-run\nprint(4)", "status": "ok"},
        {"origin": "agent", "source": "import numpy", "status": "ok"},
    ]})["entries"]
    assert [(e["pythonRun"], e["source"], e["origin"]) for e in shaped] == [
        (run, "print(3)", "user"), (None, "# leo-python not-a-run\nprint(4)", "user"), (None, "import numpy", "agent")]

"""3.2.1 · 「终端」: the person's own shell, in the conversation's working directory.

Owner, 2026-09-29: a terminal is a terminal -- what the person types runs as they typed it, not
through the AI and not through the approval flow. Each conversation gets one interactive ``bash`` in
WSL, started in that conversation's workspace (the directory the AI works in, so both see the same
files), as the same WSL user that runs Leo's daemon, with the network the machine has.

How it runs: Leo starts ``wsl.exe ... python3 -u -c BOOT`` and hands it the relay below on stdin, so
no extra file has to be installed anywhere. The relay opens a pseudo-terminal, starts ``bash -i`` in
the workspace and passes bytes both ways as JSON lines; Leo keeps the output in a bounded buffer that
the page polls. Line mode only in this version: full-screen programs (vim, top) are not supported.

Nothing here touches the research code identity, the daemon or its approvals.
"""
from __future__ import annotations

import base64
import codecs
import json
import os
import re
import subprocess
import threading

FRAME = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
# One line from the page (the box allows 8000 characters) plus its Enter.
MAX_INPUT = 8192
# Characters of output kept per conversation; older output is dropped (and the page is told).
MAX_BUFFER = 1_000_000
MAX_READ = 400_000
WORKSPACES = ".local/share/leo-ai-studio/data/agent-workspaces"

# Runs inside WSL under /usr/bin/python3 (standard library only). Kept as data here and sent on
# stdin, so the Windows package needs no new resource file.
RELAY_SOURCE = r'''
import base64, fcntl, json, os, pty, re, select, signal, struct, sys, termios

def emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

pending = b""
def messages():
    global pending
    data = os.read(0, 65536)
    if not data:
        return None
    pending += data
    out = []
    while b"\n" in pending:
        line, pending = pending.split(b"\n", 1)
        if line.strip():
            out.append(json.loads(line))
    return out

start = None
while start is None:
    got = messages()
    if got is None:
        sys.exit(0)
    for message in got:
        if message.get("t") == "start":
            start = message
frame = str(start.get("frame", ""))
if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", frame):
    emit({"t": "error", "code": "TERMINAL_FRAME_INVALID"})
    sys.exit(2)
workspace = os.path.join(os.path.expanduser("~"), WORKSPACES, frame)
os.makedirs(workspace, exist_ok=True)

def resize(fd, rows, cols):
    rows = max(5, min(int(rows or 30), 500))
    cols = max(20, min(int(cols or 100), 500))
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

pid, fd = pty.fork()
if pid == 0:
    os.chdir(workspace)
    env = dict(os.environ)
    env.update({"TERM": "xterm-256color", "LEO_TERMINAL": "1"})
    os.execvpe("bash", ["bash", "-i"], env)

resize(fd, start.get("rows"), start.get("cols"))
emit({"t": "ready", "cwd": workspace, "pid": pid})
while True:
    ready, _, _ = select.select([fd, 0], [], [])
    if fd in ready:
        try:
            data = os.read(fd, 65536)
        except OSError:
            data = b""
        if not data:
            break
        emit({"t": "out", "d": base64.b64encode(data).decode("ascii")})
    if 0 in ready:
        got = messages()
        if got is None:
            try:
                os.kill(pid, signal.SIGHUP)
            except OSError:
                pass
            break
        for message in got:
            kind = message.get("t")
            if kind == "in":
                os.write(fd, base64.b64decode(message.get("d", "")))
            elif kind == "resize":
                resize(fd, message.get("rows"), message.get("cols"))
_, status = os.waitpid(pid, 0)
emit({"t": "exit", "code": os.waitstatus_to_exitcode(status)})
'''.replace("WORKSPACES", repr(WORKSPACES))

BOOT = ("import sys,json;f=sys.stdin.buffer.raw;"
        "exec(compile(json.loads(f.readline()),'leo-terminal-relay','exec'))")


def frame_id(value):
    if not isinstance(value, str) or not FRAME.fullmatch(value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


def _size(value, default):
    return value if type(value) is int and 5 <= value <= 500 else default


class TerminalSession:
    """One conversation's shell: the relay process, its reader thread and the output buffer."""

    def __init__(self, frame, argv, popen, *, rows=30, cols=100):
        self.frame = frame
        self.lock = threading.Lock()
        self.chunks = []          # (sequence number, text)
        self.size = 0
        self.seq = 0
        self.first = 1            # the oldest sequence number still kept
        self.alive = True
        self.exit_code = None
        self.cwd = None
        self.error = None
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.process = popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             creationflags=0x08000000 if os.name == "nt" else 0)
        self._send_raw(json.dumps(RELAY_SOURCE) + "\n")
        self._send({"t": "start", "frame": frame, "rows": rows, "cols": cols})
        threading.Thread(target=self._read, name="leo-terminal-" + frame, daemon=True).start()

    def _send_raw(self, text):
        self.process.stdin.write(text.encode("utf-8"))
        self.process.stdin.flush()

    def _send(self, message):
        try:
            self._send_raw(json.dumps(message) + "\n")
        except (OSError, ValueError):
            with self.lock:
                self.alive = False
            raise ValueError("TERMINAL_NOT_RUNNING")

    def _append(self, text):
        if not text:
            return
        with self.lock:
            self.seq += 1
            self.chunks.append((self.seq, text))
            self.size += len(text)
            while self.size > MAX_BUFFER and len(self.chunks) > 1:
                dropped = self.chunks.pop(0)
                self.size -= len(dropped[1])
                self.first = self.chunks[0][0]

    def _read(self):
        try:
            for raw in self.process.stdout:
                try:
                    message = json.loads(raw)
                except ValueError:
                    continue
                kind = message.get("t")
                if kind == "out":
                    self._append(self._decoder.decode(base64.b64decode(message.get("d", ""))))
                elif kind == "ready":
                    with self.lock:
                        self.cwd = message.get("cwd") if isinstance(message.get("cwd"), str) else None
                elif kind == "exit":
                    with self.lock:
                        self.exit_code = message.get("code") if type(message.get("code")) is int else None
                elif kind == "error":
                    with self.lock:
                        self.error = str(message.get("code") or "TERMINAL_FAILED")[:64]
        except (OSError, ValueError):
            pass
        finally:
            self._append(self._decoder.decode(b"", final=True))
            with self.lock:
                self.alive = False

    def write(self, data):
        if not isinstance(data, str) or not data or len(data) > MAX_INPUT or "\x00" in data:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        if not self.alive:
            raise ValueError("TERMINAL_NOT_RUNNING")
        self._send({"t": "in", "d": base64.b64encode(data.encode("utf-8")).decode("ascii")})

    def resize(self, rows, cols):
        if self.alive:
            self._send({"t": "resize", "rows": _size(rows, 30), "cols": _size(cols, 100)})

    def read(self, after):
        after = after if type(after) is int and after >= 0 else 0
        with self.lock:
            parts, total = [], 0
            last = after
            for seq, text in self.chunks:
                if seq <= after:
                    continue
                if total + len(text) > MAX_READ and parts:
                    break
                parts.append(text)
                total += len(text)
                last = seq
            return {"text": "".join(parts), "next": last, "truncated": after + 1 < self.first,
                    "alive": self.alive, "exitCode": self.exit_code, "cwd": self.cwd, "error": self.error,
                    "more": last < self.seq}

    def stop(self):
        with self.lock:
            self.alive = False
        try:
            self.process.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.process.wait(timeout=3)
        except (subprocess.TimeoutExpired, OSError):
            try:
                self.process.kill()
            except OSError:
                pass


class UserTerminals:
    """The page's operations: open, input, read, resize, restart. One shell per conversation."""

    OPERATIONS = ("terminal_open", "terminal_input", "terminal_read", "terminal_resize", "terminal_restart")

    def __init__(self, distro=None, *, popen=subprocess.Popen):
        self._distro = distro
        self._popen = popen
        self._sessions = {}
        self._lock = threading.Lock()

    def _argv(self):
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        return argv + ["-e", "/usr/bin/python3", "-u", "-c", BOOT]

    def _session(self, frame, *, create=False, rows=30, cols=100):
        with self._lock:
            session = self._sessions.get(frame)
            if session is None and create:
                try:
                    session = TerminalSession(frame, self._argv(), self._popen, rows=rows, cols=cols)
                except OSError:
                    raise ValueError("TERMINAL_START_FAILED")
                self._sessions[frame] = session
            return session

    def handle(self, payload):
        op = payload.get("operation")
        frame = frame_id(payload.get("frameId"))
        rows, cols = _size(payload.get("rows"), 30), _size(payload.get("cols"), 100)
        if op == "terminal_restart":
            with self._lock:
                old = self._sessions.pop(frame, None)
            if old is not None:
                old.stop()
            op = "terminal_open"
        if op == "terminal_open":
            session = self._session(frame, create=True, rows=rows, cols=cols)
            if not session.alive:
                # A shell that ended (exit, or WSL restarted) is reopened on the next open.
                with self._lock:
                    self._sessions.pop(frame, None)
                session = self._session(frame, create=True, rows=rows, cols=cols)
            return session.read(payload.get("after") if type(payload.get("after")) is int else 0)
        session = self._session(frame)
        if session is None:
            raise ValueError("TERMINAL_NOT_RUNNING")
        if op == "terminal_input":
            session.write(payload.get("data"))
            return {"ok": True}
        if op == "terminal_resize":
            session.resize(rows, cols)
            return {"ok": True}
        if op == "terminal_read":
            return session.read(payload.get("after"))
        raise ValueError("WORKBENCH_INVALID_REQUEST")

    def close(self):
        with self._lock:
            sessions, self._sessions = list(self._sessions.values()), {}
        for session in sessions:
            session.stop()

"""A small RFC 6455 client on the standard library, for the local daemon's event socket.

The Leo shell bundles no WebSocket package, and this client only ever talks to the loopback
daemon, so it implements exactly what that needs: the upgrade handshake, masked text frames,
ping/pong, close, and message reassembly with a size cap.
"""
from __future__ import annotations

import base64
import hashlib
import os
import socket
import struct

_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_MESSAGE = 16 * 1024 * 1024


class WebSocketClosed(Exception):
    """The peer closed the connection or the stream ended."""


class WebSocket:
    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._buffer = b""

    @classmethod
    def connect(cls, host: str, port: int, path: str, headers: dict[str, str], timeout: float = 10.0) -> "WebSocket":
        sock = socket.create_connection((host, port), timeout=timeout)
        try:
            key = base64.b64encode(os.urandom(16)).decode()
            lines = [f"GET {path} HTTP/1.1", f"Host: {host}:{port}", "Upgrade: websocket", "Connection: Upgrade",
                     f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13"]
            lines += [f"{name}: {value}" for name, value in headers.items()]
            sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("ascii"))
            client = cls(sock)
            head = client._read_until(b"\r\n\r\n", limit=16384)
            status, *fields = head.decode("latin-1").split("\r\n")
            if not status.startswith("HTTP/1.1 101"):
                raise ConnectionError("WEBSOCKET_UPGRADE_REFUSED")
            received = {}
            for field in fields:
                name, _, value = field.partition(":")
                received[name.strip().lower()] = value.strip()
            expected = base64.b64encode(hashlib.sha1(key.encode() + _GUID).digest()).decode()
            if received.get("sec-websocket-accept") != expected:
                raise ConnectionError("WEBSOCKET_HANDSHAKE_INVALID")
            return client
        except BaseException:
            sock.close()
            raise

    def settimeout(self, seconds: float | None) -> None:
        self._sock.settimeout(seconds)

    def _read_until(self, marker: bytes, limit: int) -> bytes:
        while marker not in self._buffer:
            if len(self._buffer) > limit:
                raise ConnectionError("WEBSOCKET_HANDSHAKE_INVALID")
            chunk = self._sock.recv(4096)
            if not chunk:
                raise WebSocketClosed()
            self._buffer += chunk
        head, _, self._buffer = self._buffer.partition(marker)
        return head

    def _send(self, opcode: int, payload: bytes) -> None:
        header = bytes([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header += bytes([0x80 | length])
        elif length < 1 << 16:
            header += bytes([0x80 | 126]) + struct.pack("!H", length)
        else:
            header += bytes([0x80 | 127]) + struct.pack("!Q", length)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(header + mask + masked)

    def send_text(self, text: str) -> None:
        self._send(0x1, text.encode("utf-8"))

    def _frame(self) -> tuple[bool, int, bytes]:
        """One whole frame. Bytes are consumed only once the frame is complete, so a socket
        timeout while waiting never leaves the stream half-read."""
        while True:
            parsed = self._parse()
            if parsed is not None:
                return parsed
            chunk = self._sock.recv(65536)
            if not chunk:
                raise WebSocketClosed()
            self._buffer += chunk

    def _parse(self):
        data = self._buffer
        if len(data) < 2:
            return None
        first, second = data[0], data[1]
        offset, length = 2, second & 0x7F
        if length == 126:
            if len(data) < 4:
                return None
            length, offset = struct.unpack("!H", data[2:4])[0], 4
        elif length == 127:
            if len(data) < 10:
                return None
            length, offset = struct.unpack("!Q", data[2:10])[0], 10
        if length > MAX_MESSAGE:
            raise ConnectionError("WEBSOCKET_MESSAGE_TOO_LARGE")
        mask = None
        if second & 0x80:
            if len(data) < offset + 4:
                return None
            mask, offset = data[offset:offset + 4], offset + 4
        if len(data) < offset + length:
            return None
        payload, self._buffer = data[offset:offset + length], data[offset + length:]
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return bool(first & 0x80), first & 0x0F, payload

    def recv_text(self) -> str:
        """The next complete text message; answers pings on the way. Raises on close."""
        parts: list[bytes] = []
        size = 0
        while True:
            fin, opcode, payload = self._frame()
            if opcode == 0x8:
                try:
                    self._send(0x8, payload[:2])
                except OSError:
                    pass
                raise WebSocketClosed()
            if opcode == 0x9:
                self._send(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode in (0x1, 0x2, 0x0):
                size += len(payload)
                if size > MAX_MESSAGE:
                    raise ConnectionError("WEBSOCKET_MESSAGE_TOO_LARGE")
                parts.append(payload)
                if fin:
                    return b"".join(parts).decode("utf-8", "replace")
                continue
            raise ConnectionError("WEBSOCKET_PROTOCOL_ERROR")

    def close(self) -> None:
        try:
            self._send(0x8, struct.pack("!H", 1000))
        except OSError:
            pass
        try:
            self._sock.close()
        except OSError:
            pass

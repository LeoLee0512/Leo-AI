"""Plain-text clipboard access for explicit copy and paste actions.

The workbench is loaded as an in-memory document, where the browser clipboard API
can be unavailable; the page tries it first and falls back to this. Text only,
bounded; reads occur only for the user's explicit Paste menu action.
"""

from __future__ import annotations

import ctypes
import sys
import time

MAX_CLIPBOARD_CHARS = 1024 * 1024
_CF_UNICODETEXT = 13
_GMEM_MOVEABLE = 0x0002


class ClipboardError(RuntimeError):
    pass


def get_text(*, api=None) -> str:
    """Return the clipboard's plain text, or ``""`` when it holds none."""
    user32, kernel32 = api or _win32()
    _open_clipboard(user32)
    try:
        handle = user32.GetClipboardData(_CF_UNICODETEXT)
        if not handle:
            return ""
        size = kernel32.GlobalSize(handle)
        if size > (MAX_CLIPBOARD_CHARS + 1) * 2:
            raise ClipboardError("CLIPBOARD_TEXT_INVALID")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise ClipboardError("CLIPBOARD_UNAVAILABLE")
        try:
            return ctypes.string_at(pointer, size).decode("utf-16-le", "replace").split("\0", 1)[0]
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def _open_clipboard(user32) -> None:
    # Another process may hold the clipboard for a moment; retry briefly, never block.
    for _ in range(10):
        if user32.OpenClipboard(None):
            return
        time.sleep(0.02)
    raise ClipboardError("CLIPBOARD_BUSY")


def _win32():
    if sys.platform != "win32":
        raise ClipboardError("CLIPBOARD_UNAVAILABLE")
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalSize.restype = ctypes.c_size_t
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    return user32, kernel32


def set_text(text: str, *, api=None) -> None:
    """Replace the clipboard with ``text`` (UTF-16, NUL-terminated)."""
    if not isinstance(text, str) or len(text) > MAX_CLIPBOARD_CHARS:
        raise ClipboardError("CLIPBOARD_TEXT_INVALID")
    user32, kernel32 = api or _win32()
    data = (text + "\0").encode("utf-16-le")
    _open_clipboard(user32)
    try:
        if not user32.EmptyClipboard():
            raise ClipboardError("CLIPBOARD_UNAVAILABLE")
        handle = kernel32.GlobalAlloc(_GMEM_MOVEABLE, len(data))
        if not handle:
            raise ClipboardError("CLIPBOARD_UNAVAILABLE")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            kernel32.GlobalFree(handle)
            raise ClipboardError("CLIPBOARD_UNAVAILABLE")
        ctypes.memmove(pointer, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(_CF_UNICODETEXT, handle):
            # Ownership passes to the system only on success.
            kernel32.GlobalFree(handle)
            raise ClipboardError("CLIPBOARD_UNAVAILABLE")
    finally:
        user32.CloseClipboard()

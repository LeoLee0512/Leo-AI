"""Give the Windows taskbar an explicit Leo identity and icon resource.

WM_SETICON controls the native caption/Alt-Tab image, while the taskbar can
retain an icon associated with an implicit executable identity. Set the
process identity before creating UI, then set the relaunch properties before
the window identity. Clear those window properties during normal closing.

Only the supplied Leo window and Leo's derived icon resource are changed.
This module never restarts Explorer, deletes global Shell icon caches, changes
taskbar pins, or rewrites user shortcuts.

Microsoft API contracts:
https://learn.microsoft.com/windows/win32/shell/appids
https://learn.microsoft.com/windows/win32/properties/props-system-appusermodel-id
https://learn.microsoft.com/windows/win32/api/shellapi/nf-shellapi-shgetpropertystoreforwindow
"""

from __future__ import annotations

import ctypes
import hashlib
import re
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import UUID

APP_USER_MODEL_ID = "LeoAI.Studio.Desktop"
_PROPERTY_IDS = (2, 4, 3, 5)
_RPC_E_CHANGED_MODE = -2147417850


class _Guid(ctypes.Structure):
    _fields_ = [("data", ctypes.c_ubyte * 16)]

    @classmethod
    def parse(cls, value: str) -> "_Guid":
        return cls.from_buffer_copy(UUID(value).bytes_le)


class _PropertyKey(ctypes.Structure):
    _fields_ = [("fmtid", _Guid), ("pid", ctypes.c_uint32)]


class _PropVariant(ctypes.Structure):
    # PROPVARIANT's value union is two pointers wide on both Win32 and Win64.
    _fields_ = [
        ("vt", ctypes.c_uint16),
        ("reserved1", ctypes.c_uint16),
        ("reserved2", ctypes.c_uint16),
        ("reserved3", ctypes.c_uint16),
        ("pointer", ctypes.c_void_p),
        ("union_tail", ctypes.c_void_p),
    ]


def _check(result: int, operation: str) -> None:
    if result < 0:
        raise OSError(f"{operation} failed (HRESULT 0x{result & 0xFFFFFFFF:08X})")


def prepare_branding_resource(icon_path: Path) -> tuple[str, Path]:
    """Version Leo's group and private icon resource without clearing Shell caches."""
    icon = Path(icon_path).resolve(strict=True)
    if not icon.is_file() or icon.suffix.lower() != ".ico":
        raise ValueError("The taskbar icon must be an existing ICO file")
    content = icon.read_bytes()
    digest = hashlib.sha256(content).hexdigest()[:16]
    app_id = f"{APP_USER_MODEL_ID}.Artwork.{digest}"
    # Explorer can retain both an AppID's group image and a same-path ICO image.
    # A content-addressed copy alongside the installed ICO avoids both stale
    # keys. Leo's portable installation owns this directory; the source ICO
    # remains the single maintained artwork, and the copy is a derived resource.
    cache = icon.parent
    resource = cache / f"leo-lion.{digest}.ico"
    if not resource.is_file() or resource.read_bytes() != content:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=cache, prefix=".leo-icon-", delete=False) as output:
                temporary = Path(output.name)
                output.write(content)
            temporary.replace(resource)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    # Only our exact generated filenames are eligible for private-cache cleanup.
    # An older in-use icon can remain until a later start if Windows locks it.
    for old_resource in cache.iterdir():
        if old_resource != resource and re.fullmatch(r"leo-lion\.[0-9a-f]{16}\.ico", old_resource.name):
            try:
                if old_resource.is_file():
                    old_resource.unlink()
            except OSError:
                pass
    return app_id, resource


def set_process_app_id(icon_path: Path) -> bool:
    """Call with the installed icon before any native window exists."""
    if sys.platform != "win32":
        return False
    app_id, _ = prepare_branding_resource(icon_path)
    call = ctypes.WinDLL("shell32").SetCurrentProcessExplicitAppUserModelID
    call.argtypes = [ctypes.c_wchar_p]
    call.restype = ctypes.c_long
    _check(call(app_id), "SetCurrentProcessExplicitAppUserModelID")
    return True


@contextmanager
def _property_store(hwnd: int) -> Iterator[tuple[ctypes.c_void_p, object]]:
    if not hwnd:
        raise ValueError("A live native window handle is required")
    ole = ctypes.WinDLL("ole32")
    ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    ole.CoInitializeEx.restype = ctypes.c_long
    initialized = int(ole.CoInitializeEx(None, 0))
    if initialized != _RPC_E_CHANGED_MODE:
        _check(initialized, "CoInitializeEx")
    store = ctypes.c_void_p()
    try:
        shell = ctypes.WinDLL("shell32")
        get_store = shell.SHGetPropertyStoreForWindow
        get_store.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Guid),
                              ctypes.POINTER(ctypes.c_void_p)]
        get_store.restype = ctypes.c_long
        iid = _Guid.parse("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")
        _check(get_store(hwnd, ctypes.byref(iid), ctypes.byref(store)),
               "SHGetPropertyStoreForWindow")
        yield store, ole
    finally:
        if store.value:
            vtable = ctypes.cast(store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
            release(store)
        if initialized >= 0:
            ole.CoUninitialize()


def _set_value(store: ctypes.c_void_p, ole: object, prop_id: int, text: str | None) -> None:
    key = _PropertyKey(_Guid.parse("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), prop_id)
    value = _PropVariant()
    if text is not None:
        buffer = ctypes.create_unicode_buffer(text)
        ole.CoTaskMemAlloc.argtypes = [ctypes.c_size_t]
        ole.CoTaskMemAlloc.restype = ctypes.c_void_p
        value.pointer = ole.CoTaskMemAlloc(ctypes.sizeof(buffer))
        if not value.pointer:
            raise MemoryError("Cannot allocate the window branding property")
        ctypes.memmove(value.pointer, buffer, ctypes.sizeof(buffer))
        value.vt = 31  # VT_LPWSTR; the property store copies this string.
    try:
        vtable = ctypes.cast(store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        set_value = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(_PropertyKey),
            ctypes.POINTER(_PropVariant),
        )(vtable[6])
        _check(set_value(store, ctypes.byref(key), ctypes.byref(value)),
               f"IPropertyStore.SetValue({prop_id})")
    finally:
        ole.PropVariantClear.argtypes = [ctypes.POINTER(_PropVariant)]
        ole.PropVariantClear.restype = ctypes.c_long
        ole.PropVariantClear(ctypes.byref(value))


def apply_window_branding(hwnd: int, icon_path: Path, relaunch_command: str,
                          display_name: str = "Leo AI Studio") -> bool:
    """Apply to Leo's native HWND after creation, preserving its content/focus."""
    if sys.platform != "win32":
        return False
    if not relaunch_command.strip() or "\x00" in relaunch_command:
        raise ValueError("A valid Leo relaunch command is required")
    app_id, icon = prepare_branding_resource(icon_path)
    with _property_store(int(hwnd)) as (store, ole):
        # Microsoft requires name+command together, and AppUserModel.ID last
        # so the taskbar refresh observes all of the relaunch information.
        for prop_id, text in (
            (2, relaunch_command), (4, display_name), (3, f"{icon},0"),
            (5, app_id),
        ):
            _set_value(store, ole, prop_id, text)
    return True


def clear_window_branding(hwnd: int) -> bool:
    """Release the four properties before Leo's native window is destroyed."""
    if sys.platform != "win32":
        return False
    with _property_store(int(hwnd)) as (store, ole):
        for prop_id in reversed(_PROPERTY_IDS):
            _set_value(store, ole, prop_id, None)  # VT_EMPTY removes the value.
    return True

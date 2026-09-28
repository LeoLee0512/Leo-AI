"""Theme asset rendering for the Leo AI Studio shell.

The theme directory stays on disk next to the executable; nothing is compiled
into the binary.  Every public method re-reads the assets it needs (guarded by
an mtime+size cache) so a replaced theme takes effect without a rebuild.

Two documents are produced here, both owned by Leo and loaded as HTML:

* :meth:`ThemeRuntime.render_shell` renders the start page ``shell.html``.
* :meth:`ThemeRuntime.render_workbench` renders the workbench.

Both enforce the 1.5 MiB budget that keeps WebView2 ``NavigateToString`` from
silently rejecting the document.  (Until 2026-09-26 a third payload injected a
bundle into the upstream OpenAI4S page; that page is no longer reachable and
the injection layer was removed with the owner's approval.)
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

__all__ = [
    "MAX_SAFE_SHELL_HTML_BYTES",
    "ThemeRuntime",
    "ThemeRuntimeError",
    "trusted_backend_url",
]

MAX_SAFE_SHELL_HTML_BYTES = 1536 * 1024

_MAX_BACKGROUND_BYTES = 4 * 1024 * 1024
_MAX_CSS_BYTES = 1024 * 1024
_MAX_JS_BYTES = 1024 * 1024
_MAX_JSON_BYTES = 1024 * 1024
_MAX_SVG_BYTES = 512 * 1024

_RIFF_MAGIC = b"RIFF"
_WEBP_MAGIC = b"WEBP"
_PLACEHOLDER_PREFIX = "__LEO_"
_BACKGROUND_PLACEHOLDER_PATTERN = re.compile(r"__LEO_BG_[A-Z0-9_]+__")
_FAMILY_TOKEN_PATTERN = re.compile(r"[^A-Z0-9]+")

_TRUSTED_BACKEND_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_TRUSTED_BACKEND_PORT = 8760



class ThemeRuntimeError(RuntimeError):
    """Raised when theme assets are missing, invalid, or unsafe to embed."""


def _background_placeholder(key: str) -> str:
    """Map a manifest background key to its document placeholder.

    ``"ink-autumn-branch"`` becomes ``__LEO_BG_INK_AUTUMN_BRANCH__``, so the start
    page and the workbench can reference artwork without knowing its file name.
    """

    token = _FAMILY_TOKEN_PATTERN.sub("_", key.upper()).strip("_")
    if not token:
        raise ThemeRuntimeError("background key is empty in backgrounds/manifest.json")
    return f"__LEO_BG_{token}__"


def trusted_backend_url(url: object) -> bool:
    """Return True only for the loopback daemon URL the shell may navigate to."""

    if not isinstance(url, str) or not url:
        return False
    if any(ord(char) < 32 for char in url):
        return False
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    if parts.scheme != "http":
        return False
    if parts.hostname not in _TRUSTED_BACKEND_HOSTS:
        return False
    if port != _TRUSTED_BACKEND_PORT:
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if parts.fragment:
        return False
    return True


class ThemeRuntime:
    """Renders the splash shell and the workbench injection payload."""

    def __init__(self, theme_dir: Path) -> None:
        root = Path(theme_dir)
        if not root.is_dir():
            raise ThemeRuntimeError(f"theme directory is not available: {root}")
        self._root = root
        # relative path -> (mtime_ns, size, payload); invalidated on any change
        self._cache: dict[str, tuple[int, int, bytes]] = {}

    @property
    def theme_dir(self) -> Path:
        return self._root

    def render_shell(self, *, open_settings: bool, intro: bool = False) -> str:
        """Render ``shell.html`` with every brand placeholder resolved."""

        html = self._read_text("shell.html", limit=MAX_SAFE_SHELL_HTML_BYTES)
        lion = self._data_uri(
            self._read_asset("logos/leo-lion.svg", limit=_MAX_SVG_BYTES),
            "image/svg+xml",
        )
        # The favicon placeholder is optional in the template; replacing an
        # absent marker is intentionally a harmless no-op.
        favicon = self._data_uri(
            self._read_asset("logos/leo-favicon.svg", limit=_MAX_SVG_BYTES),
            "image/svg+xml",
        )
        rendered = (
            html.replace("__LEO_LION_DATA_URI__", lion)
            .replace("__LEO_FAVICON_DATA_URI__", favicon)
            .replace("__LEO_OPEN_SETTINGS__", "1" if open_settings else "0")
            .replace("__LEO_INTRO__", "1" if intro and not open_settings else "0")
        )
        # Shell artwork uses the same manifest and compressed files as the
        # workbench. Resolve only markers present in this document: a CSS
        # custom property embeds each image once even when several layers use it.
        rendered = self._resolve_backgrounds(rendered)
        if _PLACEHOLDER_PREFIX in rendered:
            raise ThemeRuntimeError("shell contains unresolved brand placeholders")
        if len(rendered.encode("utf-8")) > MAX_SAFE_SHELL_HTML_BYTES:
            raise ThemeRuntimeError(
                "shell exceeds the safe WebView2 in-memory navigation budget"
            )
        return rendered

    def render_workbench(self) -> str:
        """Own the first document, instead of repainting an upstream page later."""
        html = self._read_text("workbench.html", limit=MAX_SAFE_SHELL_HTML_BYTES)
        css = self._read_text("workbench.css", limit=_MAX_CSS_BYTES)
        js = self._read_text("workbench.js", limit=_MAX_JS_BYTES)
        research = self._read_text("research-panel.js", limit=_MAX_JS_BYTES)
        logo = self._data_uri(self._read_asset("logos/leo-lion.svg", limit=_MAX_SVG_BYTES), "image/svg+xml")
        rendered = html.replace("__LEO_WORKBENCH_CSS__", css).replace("__LEO_WORKBENCH_JS__", js)
        rendered = rendered.replace("__LEO_RESEARCH_JS__", research).replace("__LEO_LION_DATA_URI__", logo)
        # The home painting is the start page's own tree, so entering Leo keeps one picture.
        rendered = self._resolve_backgrounds(rendered)
        if any(token in rendered for token in ("__LEO_WORKBENCH_CSS__", "__LEO_WORKBENCH_JS__", "__LEO_RESEARCH_JS__", "__LEO_LION_DATA_URI__")) or len(rendered.encode("utf-8")) > MAX_SAFE_SHELL_HTML_BYTES:
            raise ThemeRuntimeError("workbench contains unresolved assets or exceeds navigation budget")
        return rendered

    def themes(self) -> list[str]:
        """Return the theme ids registered in ``themes.json`` (file order)."""

        data = self._read_json("themes.json")
        entries = data.get("themes") if isinstance(data, dict) else None
        if not isinstance(entries, list) or not entries:
            raise ThemeRuntimeError("themes.json does not register any theme")
        ids: list[str] = []
        for entry in entries:
            theme_id = entry.get("id") if isinstance(entry, dict) else None
            if not isinstance(theme_id, str) or not theme_id:
                raise ThemeRuntimeError("themes.json entry without a string id")
            if theme_id in ids:
                raise ThemeRuntimeError(f"themes.json registers {theme_id!r} twice")
            ids.append(theme_id)
        return ids

    def _default_theme(self, registered: list[str]) -> str:
        data = self._read_json("themes.json")
        candidate = data.get("default_theme") if isinstance(data, dict) else None
        if isinstance(candidate, str) and candidate in registered:
            return candidate
        return registered[0]

    def _resolve_backgrounds(self, source: str) -> str:
        """Resolve referenced artwork without duplicating unused assets."""
        assets = self._background_assets()
        for placeholder, relative in assets.items():
            if placeholder not in source:
                continue
            image = self._read_asset(relative, limit=_MAX_BACKGROUND_BYTES)
            if (
                len(image) < 12
                or not image.startswith(_RIFF_MAGIC)
                or image[8:12] != _WEBP_MAGIC
            ):
                raise ThemeRuntimeError(f"background asset is not webp: {relative}")
            source = source.replace(placeholder, self._data_uri(image, "image/webp"))
        if _BACKGROUND_PLACEHOLDER_PATTERN.search(source):
            raise ThemeRuntimeError("theme contains unresolved background placeholders")
        return source

    def _background_assets(self) -> dict[str, str]:
        """Map background placeholders to files under ``backgrounds/``.

        Absent manifest -> no backgrounds.  A malformed one is still an error:
        the difference between "this theme ships no artwork" and "this theme
        ships artwork the shell cannot read" must not collapse into a blank page.
        """

        if not (self._root / "backgrounds" / "manifest.json").is_file():
            return {}
        data = self._read_json("backgrounds/manifest.json")
        entries = data.get("backgrounds") if isinstance(data, dict) else None
        if not isinstance(entries, list) or not entries:
            raise ThemeRuntimeError("backgrounds/manifest.json does not list any background")
        mapping: dict[str, str] = {}
        for entry in entries:
            key = entry.get("key") if isinstance(entry, dict) else None
            filename = entry.get("file") if isinstance(entry, dict) else None
            if (
                not isinstance(key, str)
                or not key
                or not isinstance(filename, str)
                or not filename
                or Path(filename).name != filename
            ):
                raise ThemeRuntimeError("backgrounds/manifest.json entry is invalid")
            mapping[_background_placeholder(key)] = f"backgrounds/{filename}"
        return mapping

    def _read_json(self, relative: str) -> object:
        raw = self._read_text(relative, limit=_MAX_JSON_BYTES)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ThemeRuntimeError(f"theme asset is not valid JSON: {relative}") from exc

    def _read_text(self, relative: str, *, limit: int) -> str:
        data = self._read_asset(relative, limit=limit)
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ThemeRuntimeError(f"theme asset is not valid UTF-8: {relative}") from exc

    def _read_asset(self, relative: str, *, limit: int) -> bytes:
        parts = Path(relative).parts
        if not relative or Path(relative).is_absolute() or ".." in parts:
            raise ThemeRuntimeError(f"invalid theme asset path: {relative!r}")
        path = self._root / relative
        try:
            stat = path.stat()
        except OSError as exc:
            raise ThemeRuntimeError(f"theme asset is missing: {relative}") from exc
        if not path.is_file():
            raise ThemeRuntimeError(f"theme asset is not a file: {relative}")
        if stat.st_size > limit:
            raise ThemeRuntimeError(f"theme asset exceeds {limit} bytes: {relative}")
        cached = self._cache.get(relative)
        if cached is not None and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
            return cached[2]
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ThemeRuntimeError(f"theme asset is unreadable: {relative}") from exc
        if len(data) > limit:
            raise ThemeRuntimeError(f"theme asset exceeds {limit} bytes: {relative}")
        self._cache[relative] = (stat.st_mtime_ns, len(data), data)
        return data

    @staticmethod
    def _data_uri(data: bytes, mime: str) -> str:
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{encoded}"

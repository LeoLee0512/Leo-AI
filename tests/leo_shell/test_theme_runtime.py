"""Tests for leo_shell.theme_runtime.

A miniature theme directory (fake svg/png/css/json assets) is assembled under
``tmp_path``; the real theme assets are never touched.  No GUI imports.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

# A sibling-owned ``tests/leo_shell/__init__.py`` turns this directory into a
# package literally named ``leo_shell``, which shadows the source package at
# the build root once pytest prepends ``tests/`` to ``sys.path``.  Put the
# build root first and evict the shadow so ``leo_shell.theme_runtime`` below
# resolves to the real module.  Harmless once the shadow file is removed.
_BUILD_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_BUILD_ROOT))
_shadow = sys.modules.get("leo_shell")
if _shadow is not None and Path(getattr(_shadow, "__file__", "") or "").resolve() != (
    _BUILD_ROOT / "leo_shell" / "__init__.py"
).resolve():
    del sys.modules["leo_shell"]

from leo_shell import theme_runtime
from leo_shell.theme_runtime import (
    MAX_SAFE_SHELL_HTML_BYTES,
    ThemeRuntime,
    ThemeRuntimeError,
    trusted_backend_url,
)

_SHELL_TEMPLATE = (
    '<!doctype html><html><body data-open-settings="__LEO_OPEN_SETTINGS__">'
    '<img class="lion" src="__LEO_LION_DATA_URI__">'
    '<img src="__LEO_LION_DATA_URI__" alt="">'
    "</body></html>"
)

_BACKGROUNDS = ("ink-autumn-branch", "ink-autumn-tree")


def _fake_webp() -> bytes:
    """A RIFF/WEBP header is all the background resolver checks, and all it should."""
    return b"RIFF" + b"\x20\x00\x00\x00" + b"WEBPVP8 " + b"\x00" * 16


def make_theme(root: Path, *, shell: str = _SHELL_TEMPLATE) -> Path:
    theme = root / "theme"
    (theme / "logos").mkdir(parents=True)
    (theme / "shell.html").write_text(shell, encoding="utf-8")
    (theme / "logos" / "leo-lion.svg").write_text("<svg><rect/></svg>", "utf-8")
    (theme / "logos" / "leo-favicon.svg").write_text("<svg><circle/></svg>", "utf-8")
    (theme / "themes.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "default_theme": "deep-sea-molten-orange",
                "themes": [
                    {"id": "deep-sea-molten-orange"},
                    {"id": "amethyst-teal"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return theme


def add_backgrounds(theme: Path, *, entries: list[dict] | None = None) -> None:
    """Give an existing fake theme a ``backgrounds/`` directory.

    Kept out of :func:`make_theme` on purpose: backgrounds are optional, so the
    default fixture has to keep proving that a theme without them still renders.
    """
    if entries is None:
        entries = [{"key": key, "file": f"{key}.webp"} for key in _BACKGROUNDS]
    directory = theme / "backgrounds"
    directory.mkdir(exist_ok=True)
    for entry in entries:
        (directory / entry["file"]).write_bytes(_fake_webp())
    (directory / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "backgrounds": entries}), encoding="utf-8"
    )


def use_background_css(theme: Path, css: str) -> None:
    """Give the start page a stylesheet that references artwork placeholders."""
    (theme / "shell.html").write_text(
        '<body data-open-settings="__LEO_OPEN_SETTINGS__"><style>' + css + "</style>"
        '<img src="__LEO_LION_DATA_URI__"></body>',
        encoding="utf-8",
    )


@pytest.fixture()
def theme_dir(tmp_path: Path) -> Path:
    return make_theme(tmp_path)


@pytest.fixture()
def runtime(theme_dir: Path) -> ThemeRuntime:
    return ThemeRuntime(theme_dir)


class TestRenderShell:
    def test_replaces_every_placeholder(self, runtime: ThemeRuntime) -> None:
        rendered = runtime.render_shell(open_settings=False)
        assert "__LEO_" not in rendered
        assert rendered.count("data:image/svg+xml;base64,") == 2
        lion = Path(runtime.theme_dir / "logos" / "leo-lion.svg").read_bytes()
        assert base64.b64encode(lion).decode("ascii") in rendered

    def test_open_settings_flag(self, runtime: ThemeRuntime) -> None:
        assert 'data-open-settings="1"' in runtime.render_shell(open_settings=True)
        assert 'data-open-settings="0"' in runtime.render_shell(open_settings=False)

    def test_favicon_placeholder_is_optional(self, tmp_path: Path) -> None:
        theme = make_theme(
            tmp_path,
            shell=(
                '<body data-open-settings="__LEO_OPEN_SETTINGS__">'
                '<link rel="icon" href="__LEO_FAVICON_DATA_URI__">'
                '<img src="__LEO_LION_DATA_URI__"></body>'
            ),
        )
        rendered = ThemeRuntime(theme).render_shell(open_settings=False)
        assert "__LEO_" not in rendered
        assert rendered.count("data:image/svg+xml;base64,") == 2

    def test_unresolved_placeholder_raises(self, tmp_path: Path) -> None:
        theme = make_theme(
            tmp_path,
            shell=(
                '<body data-open-settings="__LEO_OPEN_SETTINGS__">'
                '<img src="__LEO_LION_DATA_URI__">__LEO_SURPRISE__</body>'
            ),
        )
        with pytest.raises(ThemeRuntimeError, match="unresolved"):
            ThemeRuntime(theme).render_shell(open_settings=False)

    def test_size_gate(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        theme = make_theme(tmp_path)
        gate = len(_SHELL_TEMPLATE.encode("utf-8")) + 16
        monkeypatch.setattr(theme_runtime, "MAX_SAFE_SHELL_HTML_BYTES", gate)
        with pytest.raises(ThemeRuntimeError, match="budget"):
            ThemeRuntime(theme).render_shell(open_settings=False)
        assert gate < MAX_SAFE_SHELL_HTML_BYTES

    def test_missing_theme_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ThemeRuntimeError):
            ThemeRuntime(tmp_path / "absent")


class TestBackgrounds:
    """Artwork placeholders are resolved for the documents Leo owns.

    These cases used to run through the upstream-page injection script, removed on
    2026-09-26; the resolver they exercise now serves the start page and workbench.
    """

    def test_theme_without_backgrounds_still_renders(self, runtime: ThemeRuntime) -> None:
        """The default fixture has no ``backgrounds/`` and must not need one."""
        assert "data:image/webp;base64," not in runtime.render_shell(open_settings=False)

    def test_inlines_webp_backgrounds(self, theme_dir: Path) -> None:
        add_backgrounds(theme_dir)
        use_background_css(
            theme_dir,
            "body{background-image:url(__LEO_BG_INK_AUTUMN_BRANCH__)}"
            "main{background-image:url(__LEO_BG_INK_AUTUMN_TREE__)}",
        )
        rendered = ThemeRuntime(theme_dir).render_shell(open_settings=False)
        assert "__LEO_BG_" not in rendered
        assert rendered.count("data:image/webp;base64,") == 2

    def test_leftover_background_placeholder_raises(self, theme_dir: Path) -> None:
        add_backgrounds(theme_dir)
        use_background_css(theme_dir, "body{background-image:url(__LEO_BG_ABSENT__)}")
        with pytest.raises(ThemeRuntimeError, match="background placeholder"):
            ThemeRuntime(theme_dir).render_shell(open_settings=False)

    def test_bad_background_magic_raises(self, theme_dir: Path) -> None:
        add_backgrounds(theme_dir)
        (theme_dir / "backgrounds" / "ink-autumn-branch.webp").write_bytes(
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
        )
        use_background_css(theme_dir, "body{background-image:url(__LEO_BG_INK_AUTUMN_BRANCH__)}")
        with pytest.raises(ThemeRuntimeError, match="webp"):
            ThemeRuntime(theme_dir).render_shell(open_settings=False)

    def test_riff_container_that_is_not_webp_raises(self, theme_dir: Path) -> None:
        """RIFF alone is not enough -- a wav would pass a prefix-only check."""
        add_backgrounds(theme_dir)
        (theme_dir / "backgrounds" / "ink-autumn-branch.webp").write_bytes(
            b"RIFF" + b"\x20\x00\x00\x00" + b"WAVEfmt " + b"\x00" * 16
        )
        use_background_css(theme_dir, "body{background-image:url(__LEO_BG_INK_AUTUMN_BRANCH__)}")
        with pytest.raises(ThemeRuntimeError, match="webp"):
            ThemeRuntime(theme_dir).render_shell(open_settings=False)

    @pytest.mark.parametrize(
        "entries",
        [
            [],
            [{"key": "", "file": "x.webp"}],
            [{"key": "ink-autumn-branch", "file": "../escape.webp"}],
            [{"key": "ink-autumn-branch"}],
        ],
        ids=["empty", "blank-key", "path-escape", "no-file"],
    )
    def test_invalid_background_manifest_raises(self, theme_dir: Path, entries: list[dict]) -> None:
        add_backgrounds(theme_dir, entries=[{"key": "k", "file": "k.webp"}])
        (theme_dir / "backgrounds" / "manifest.json").write_text(
            json.dumps({"schema_version": 1, "backgrounds": entries}), encoding="utf-8"
        )
        use_background_css(theme_dir, "body{background-image:url(__LEO_BG_K__)}")
        with pytest.raises(ThemeRuntimeError):
            ThemeRuntime(theme_dir).render_shell(open_settings=False)


class TestThemes:
    def test_registered_ids_in_file_order(self, runtime: ThemeRuntime) -> None:
        assert runtime.themes() == ["deep-sea-molten-orange", "amethyst-teal"]

    def test_invalid_registry_raises(self, theme_dir: Path) -> None:
        (theme_dir / "themes.json").write_text('{"themes": []}', encoding="utf-8")
        with pytest.raises(ThemeRuntimeError):
            ThemeRuntime(theme_dir).themes()


class TestTrustedBackendUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1:8760/",
            "http://127.0.0.1:8760",
            "http://127.0.0.1:8760/?token=abc123",
            "http://localhost:8760/ui",
            "http://LOCALHOST:8760/",
            "http://[::1]:8760/app?x=1",
        ],
    )
    def test_trusted(self, url: str) -> None:
        assert trusted_backend_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://127.0.0.1:8760/",
            "http://127.0.0.1:8759/",
            "http://127.0.0.1/",
            "http://user:pass@127.0.0.1:8760/",
            "http://user@127.0.0.1:8760/",
            "http://127.0.0.1:8760/#fragment",
            "http://evil.example:8760/",
            "http://127.0.0.1.evil.example:8760/",
            "http://127.0.0.1:badport/",
            "http://127.0.0.1:8760/\n",
            "http://127.0.0.1:8760/\tpath",
            "",
            "not a url",
            None,
            8760,
            b"http://127.0.0.1:8760/",
        ],
    )
    def test_untrusted(self, url: object) -> None:
        assert trusted_backend_url(url) is False

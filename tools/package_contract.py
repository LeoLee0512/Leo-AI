from __future__ import annotations

import argparse
import marshal
import re
import sys
import types
from pathlib import Path


REQUIRED_FILES = (
    "bridge/leo_identity.py",
    "bridge/leo_runtime_compat.py",
    "bridge/leo_example_persistence.py",
    "bridge/leo_runtime_features.py",
    "bridge/leo_reasoning.py",
    "bridge/leo_turn_binding.py",
    "bridge/leo_turn_binding_runtime.py",
    "bridge/leo_thought_runtime.py",
    "bridge/leo_local_relay.py",
    "bridge/leo_model_selection.py",
    "LeoAIStudio.exe",
    "_launcher/base_library.zip",
    "_launcher/python312.dll",
    "_launcher/libcrypto-3-x64.dll",
    "_launcher/_ssl.pyd",
    "_launcher/cryptography/hazmat/bindings/_rust.pyd",
    "_launcher/_cffi_backend.cp312-win_amd64.pyd",
    "_launcher/clr_loader/ffi/dlls/amd64/ClrLoader.dll",
    "_launcher/pythonnet/runtime/Python.Runtime.dll",
    "_launcher/webview/lib/Microsoft.Web.WebView2.Core.dll",
    "_launcher/webview/lib/Microsoft.Web.WebView2.WinForms.dll",
    "_launcher/webview/lib/runtimes/win-x64/native/WebView2Loader.dll",
    "theme/shell.html",
    "theme/workbench.html",
    "theme/workbench.css",
    "theme/workbench.js",
    "theme/research-panel.js",
    # The theme registry and the artwork it points at are read by the shell on
    # every render, so a package without them is not a shippable package --
    # the first-run default theme and every background would silently vanish.
    "theme/themes.json",
    "theme/backgrounds/manifest.json",
    "theme/backgrounds/ink-autumn-branch.webp",
    "theme/backgrounds/ink-autumn-branch-warm.webp",
    "theme/backgrounds/ink-autumn-tree.webp",
    "theme/logos/leo-lion.svg",
    "theme/logos/leo-favicon.svg",
    "theme/logos/leo-lion.ico",
    # Played by the start page on every launch (leo_shell/intro.py).
    "theme/intro/leo-intro.mp4",
)

REQUIRED_ARCHIVE_MODULES = (
    "leo_shell.workbench",
    "leo_shell.clipboard",
    "leo_shell.research",
    "leo_shell.research_draft",
    "pinn.research.storage",
    "pinn.research.evidence",
    "leo_shell.local_model",
    "leo_shell.session_models",
    "bridge.leo_reasoning",
    "leo_shell.entity_store",
    "leo_shell",
    "leo_shell.api",
    "leo_shell.app",
    "leo_shell.bridge_client",
    "leo_shell.connection",
    "leo_shell.diagnostics",
    "leo_shell.logging_setup",
    "leo_shell.paths",
    "leo_shell.secrets_store",
    "leo_shell.settings_store",
    "leo_shell.single_instance",
    "leo_shell.theme_runtime",
    "leo_shell.ui",
    "leo_shell.windows_branding",
    "leo_shell.webview2_runtime",
    "webview",
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    "bottle",
    "cffi",
    "clr",
    "proxy_tools",
    "pythonnet",
    "clr_loader",
    "cryptography",
)

FORBIDDEN_ENTRY_IMPORTS = ("leo_ai_studio", "leo_runtime_patch", "leo_repair_legacy")

TEXT_SUFFIXES = {
    ".cfg", ".css", ".html", ".ini", ".js", ".json", ".md",
    ".pth", ".py", ".svg", ".toml", ".txt", ".xml",
}

FORBIDDEN_PATH = re.compile(
    r"(?i)(^|/)user(/|$)|(^|/)\.env($|[./])|\.dpapi$|"
    r"(^|/)(?:credentials?|secrets?)(?:[./]|$)|"
    r"(^|/)__pycache__(/|$)|\.pyc$|\.(?:key|pem|p12|pfx)$"
)

SECRET_TEXT = (
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+"
        r"[A-Za-z0-9+/=\r\n]{80,}\s+-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    re.compile(
        r"(?im)^\s*(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|API_KEY|SECRET_KEY|ACCESS_TOKEN)\s*[:=]\s*[\"']"
        r"(?!example|placeholder|change-me|\$\{)[A-Za-z0-9_./+\-=]{12,}[\"']"
    ),
)


def fail(message: str) -> None:
    raise SystemExit(f"PACKAGE CONTRACT FAILED: {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Static LeoAIStudio onedir package contract")
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--pyinstaller-tools", required=True, type=Path)
    parser.add_argument("--forbidden-build-root", required=True, type=Path)
    return parser.parse_args()


def archive_modules(exe: Path, pyinstaller_tools: Path) -> set[str]:
    sys.path.insert(0, str(pyinstaller_tools))
    try:
        from PyInstaller.archive.readers import CArchiveReader
    except ImportError as exc:
        fail(f"cannot load the offline PyInstaller archive reader: {exc}")
    archive = CArchiveReader(str(exe))
    entry_data = archive.extract("leo_shell_entry")
    if not isinstance(entry_data, bytes):
        fail("EXE archive is missing the launcher entry code")
    try:
        entry_code = marshal.loads(entry_data)
    except (EOFError, ValueError, TypeError) as exc:
        fail(f"cannot inspect launcher entry code: {exc}")

    # No legacy shell module may be referenced anywhere in the entry code.
    pending = [entry_code]
    entry_functions: set[str] = set()
    while pending:
        code = pending.pop()
        entry_functions.update(code.co_names)
        pending.extend(
            value for value in code.co_consts if isinstance(value, types.CodeType)
        )
    legacy_refs = sorted(
        name
        for name in entry_functions
        if any(
            name == legacy or name.startswith(legacy + ".")
            for legacy in FORBIDDEN_ENTRY_IMPORTS
        )
    )
    if legacy_refs:
        fail("launcher entry still references the legacy shell: " + ", ".join(legacy_refs))

    # The entry must (1) disable bytecode caches before importing the shell,
    # (2) pull main from leo_shell.app, and (3) exit via SystemExit(main()).
    top_level_names = set(entry_code.co_names)
    if "dont_write_bytecode" not in top_level_names:
        fail("launcher entry does not set sys.dont_write_bytecode")
    if not {"leo_shell.app", "main"}.issubset(top_level_names):
        fail("launcher entry does not import main from leo_shell.app")
    if "SystemExit" not in top_level_names:
        fail("launcher entry does not exit through SystemExit(main())")

    pyz = archive.open_embedded_archive("PYZ.pyz")
    return set(pyz.toc)


def check_paths_without_reading_sensitive_files(dist: Path) -> list[Path]:
    text_files: list[Path] = []
    for path in dist.rglob("*"):
        relative = path.relative_to(dist).as_posix()
        if FORBIDDEN_PATH.search(relative):
            fail(f"forbidden user/credential path is packaged: {relative}")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text_files.append(path)
    return text_files


def check_text_assets(text_files: list[Path], dist: Path, forbidden_root: Path) -> None:
    forbidden_spellings = {
        str(forbidden_root).lower(),
        str(forbidden_root).replace("\\", "/").lower(),
    }
    generic_build_root = re.compile(r"(?i)[a-z]:[/\\]users[/\\][^/\\]+[/\\]desktop[/\\]leoai(?:studio)?-build")
    for path in text_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        if any(spelling in lowered for spelling in forbidden_spellings) or generic_build_root.search(text):
            fail(f"hard-coded build path found in text asset: {path.relative_to(dist).as_posix()}")
        for secret_pattern in SECRET_TEXT:
            if secret_pattern.search(text):
                fail(f"credential-like value found in text asset: {path.relative_to(dist).as_posix()}")


def packaged_theme_runtime(dist: Path, pyinstaller_tools: Path):
    """Read the renderer from this EXE, not a source checkout or old replica.

    This module imports only the standard library. Loading it does not start
    the desktop, webview, WSL, model, or application settings machinery.
    """
    sys.path.insert(0, str(pyinstaller_tools))
    try:
        from PyInstaller.archive.readers import CArchiveReader
        archive = CArchiveReader(str(dist / "LeoAIStudio.exe"))
        pyz = archive.open_embedded_archive("PYZ.pyz")
        code = pyz.extract("leo_shell.theme_runtime")
        if not isinstance(code, types.CodeType):
            fail("EXE archive is missing the theme renderer code")
        module = types.ModuleType("_leo_packaged_theme_runtime")
        module.__file__ = str(dist / "LeoAIStudio.exe") + "!leo_shell/theme_runtime.py"
        exec(code, module.__dict__)
        return module.ThemeRuntime(dist / "theme")
    except Exception as exc:
        fail(f"cannot load the packaged theme renderer: {type(exc).__name__}")


def check_shell_navigation_budget(dist: Path, pyinstaller_tools: Path) -> None:
    runtime = packaged_theme_runtime(dist, pyinstaller_tools)
    try:
        workbench = runtime.render_workbench()
        if len(workbench.encode("utf-8")) > 1536 * 1024:
            fail("Leo workbench exceeds the safe WebView2 navigation budget")
    except Exception as exc:
        fail(f"packaged Leo workbench renderer rejected the assets: {type(exc).__name__}")
    for open_settings in (False, True):
        try:
            rendered = runtime.render_shell(open_settings=open_settings)
        except Exception as exc:
            fail(f"packaged shell renderer rejected the theme: {exc}")
        if not isinstance(rendered, str):
            fail("packaged shell renderer returned a non-string document")
        # These independent gates deliberately remain even when the packaged
        # renderer checks them too: changing that module cannot raise the
        # package's accepted limit or exempt an unresolved marker.
        if "__LEO_" in rendered:
            fail("shell contains an unresolved runtime placeholder")
        rendered_size = len(rendered.encode("utf-8"))
        if rendered_size > 1536 * 1024:
            fail(
                "rendered shell exceeds the safe WebView2 navigation budget: "
                f"{rendered_size} bytes"
            )


def main() -> int:
    args = parse_args()
    dist = args.dist.resolve()
    if not dist.is_dir():
        fail(f"dist directory does not exist: {dist}")

    missing_files = [relative for relative in REQUIRED_FILES if not (dist / relative).is_file()]
    if missing_files:
        fail("missing required files: " + ", ".join(missing_files))

    text_files = check_paths_without_reading_sensitive_files(dist)
    check_text_assets(text_files, dist, args.forbidden_build_root.resolve())
    check_shell_navigation_budget(dist, args.pyinstaller_tools.resolve())

    modules = archive_modules(dist / "LeoAIStudio.exe", args.pyinstaller_tools.resolve())
    missing_modules = [name for name in REQUIRED_ARCHIVE_MODULES if name not in modules]
    if missing_modules:
        fail("EXE archive is missing importable modules: " + ", ".join(missing_modules))

    launcher_files = sum(1 for path in (dist / "_launcher").rglob("*") if path.is_file())
    if launcher_files < 250:
        fail(f"_launcher is unexpectedly sparse ({launcher_files} files; expected at least 250)")

    print(
        "PACKAGE CONTRACT PASSED: "
        f"{launcher_files} _launcher files, {len(REQUIRED_FILES)} critical files, "
        f"{len(REQUIRED_ARCHIVE_MODULES)} archive modules"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

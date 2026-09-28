"""PyInstaller entry point for the rewritten Leo AI Studio shell."""

from __future__ import annotations

import sys

# The portable onedir keeps pure-Python dependencies beside the EXE.  Never
# emit per-user bytecode caches into that release tree: their embedded source
# filename can expose the builder/runner's local Windows path in a later
# traceback, and the files are unnecessary for this small launcher surface.
sys.dont_write_bytecode = True

from leo_shell.app import main  # noqa: E402  (must follow dont_write_bytecode)


if __name__ == "__main__":
    raise SystemExit(main())

"""Leo AI Studio shell package.

A from-scratch rewrite of the Windows shell around the OpenAI4S daemon:
portable-path resolution, redacted logging, settings/secrets storage, a WSL
bridge client, a serial connection coordinator and a pywebview front end.
"""

from __future__ import annotations

__version__ = "2.1.2"
PRODUCT_NAME = "Leo AI"
DISPLAY_NAME = "Leo AI 2.1"

__all__ = ["__version__"]

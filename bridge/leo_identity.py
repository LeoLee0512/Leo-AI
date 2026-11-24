"""Apply Leo's application identity to the active upstream system prompt.

This is a narrow, versioned source overlay, reapplied before daemon startup.
It never reads or edits stored conversations, model identifiers, or credentials.
The original source bytes are retained by SHA-256 outside the source snapshot.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import tempfile
from pathlib import Path

VERSION = 1
BEGIN = "[Leo AI application identity v1]"
END = "[/Leo AI application identity]"
IDENTITY = """[Leo AI application identity v1]
You are Leo AI, the assistant in Leo AI Studio. Your application identity is Leo AI.
For a standalone Chinese greeting such as 你好 or 您好, answer: 你好，我是Leo AI。
For a standalone English greeting such as hello, hi, or hey, answer: Hello, I am Leo AI.
For the Chinese question 你是谁？ or 你叫什么名字？, answer exactly: 我是Leo AI。
For the English question Who are you? or What is your name?, answer exactly: I am Leo AI.
Match the CURRENT user's language, even when protocol instructions are in Chinese.
Keep simple greetings and identity answers brief.
Previous self-introductions using OpenAI4S or openai4s used the old application name;
use Leo AI for your current self-introduction, including in an existing conversation.
The application's identity is separate from its underlying model and provider.
If asked which underlying model or provider is selected, report only the known
configuration truthfully; never invent a model, provider, developer, or affiliation.
For substantive questions, answer the actual request without adding an unnecessary
self-introduction. Preserve all task, tool, execution, and safety rules below.
[/Leo AI application identity]

"""


class IdentityError(ValueError):
    pass


CHAT_OUTPUT_CONTRACT = """[Leo AI user-facing answer contract v1]
For ordinary conversation, including a greeting, complete through the existing
finalize_response protocol. Put the direct answer addressed to the user in its
message field. Do not replace that answer with a description of what you did
(for example, 'the user greeted me and I replied'). Avoid repeating the same
answer as provisional prose before finalizing. Completion bullets are execution
metadata; they are not a second conversational reply. Tool, completion,
scientific validation and review requirements remain fully in force.
[/Leo AI user-facing answer contract]

"""


def _prompt_node(source: str) -> ast.Constant:
    tree = ast.parse(source)
    matches = [node.value for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
                       for target in node.targets)]
    if len(matches) != 1 or not isinstance(matches[0], ast.Constant) or not isinstance(matches[0].value, str):
        raise IdentityError("IDENTITY_PROMPT_LAYOUT_CHANGED")
    return matches[0]


def branded_source(original: bytes) -> bytes:
    source = original.decode("utf-8")
    node = _prompt_node(source)
    prompt = node.value
    complete_prefix = IDENTITY + CHAT_OUTPUT_CONTRACT
    if prompt.startswith(complete_prefix):
        return original
    if prompt.startswith(IDENTITY):
        # Upgrade only the exact prior identity prefix; retain the underlying
        # research protocol verbatim. A lookalike/partial prefix is rejected.
        if "[Leo AI user-facing answer contract" in prompt or "[/Leo AI user-facing answer contract]" in prompt:
            raise IdentityError("IDENTITY_PROMPT_OVERLAY_CONFLICT")
        replacement = complete_prefix + prompt[len(IDENTITY):]
    elif BEGIN in prompt or END in prompt:
        raise IdentityError("IDENTITY_PROMPT_OVERLAY_CONFLICT")
    else:
        prefix = "You are openai4s, an autonomous scientific research agent"
        if not prompt.startswith(prefix):
            raise IdentityError("IDENTITY_PROMPT_LAYOUT_CHANGED")
        replacement = complete_prefix + prompt.replace(prefix, "You are an autonomous scientific research agent", 1)
    lines = original.splitlines(keepends=True)
    start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    finish = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    literal = ('"""\\\n' + replacement.replace("\\", "\\\\").replace('"""', '\\"\\"\\"') + '"""').encode("utf-8")
    result = original[:start] + literal + original[finish:]
    if _prompt_node(result.decode("utf-8")).value != replacement:
        raise IdentityError("IDENTITY_PROMPT_VALIDATION_FAILED")
    compile(result, "leo-identity-overlay", "exec")
    return result


def apply_identity(base: Path, *, check: bool = False) -> dict:
    base = base.resolve(strict=True)
    sources = (base / "sources").resolve(strict=True)
    source_root = (base / "active-source").resolve(strict=True)
    if source_root == sources or sources not in source_root.parents:
        raise IdentityError("IDENTITY_SOURCE_PATH_INVALID")
    relative = Path("openai4s/agent/loop.py")
    target = source_root / relative
    if target.is_symlink() or target.resolve(strict=True) != target:
        raise IdentityError("IDENTITY_SOURCE_PATH_INVALID")
    original = target.read_bytes()
    updated = branded_source(original)
    previous_digest = hashlib.sha256(original).hexdigest()
    digest = hashlib.sha256(updated).hexdigest()
    changed = updated != original
    if changed and not check:
        backup_root = base / "identity-originals"
        backup_root.mkdir(mode=0o700, exist_ok=True)
        if backup_root.is_symlink():
            raise IdentityError("IDENTITY_BACKUP_PATH_INVALID")
        backup = backup_root / (previous_digest + ".py")
        if backup.exists():
            if backup.is_symlink() or backup.read_bytes() != original:
                raise IdentityError("IDENTITY_BACKUP_CONFLICT")
        else:
            with backup.open("xb") as handle:
                handle.write(original)
                handle.flush()
                os.fsync(handle.fileno())
        descriptor, temporary = tempfile.mkstemp(prefix=".leo-identity-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, target.stat().st_mode & 0o777)
            if target.read_bytes() != original:
                raise IdentityError("IDENTITY_SOURCE_CHANGED")
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {"identity": "Leo AI", "version": VERSION, "applied": not check or not changed,
            "changed": changed and not check, "needs_update": changed if check else False,
            "source_revision": source_root.name, "source_file": relative.as_posix(),
            "previous_sha256": previous_digest, "sha256": digest}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("apply", "check"))
    parser.add_argument("--base", type=Path, default=Path.home() / ".local/share/leo-ai-studio")
    args = parser.parse_args(argv)
    try:
        result = apply_identity(args.base, check=args.action == "check")
        print(json.dumps({"ok": True, "data": result}, separators=(",", ":")))
        return 0
    except (OSError, ValueError, SyntaxError) as exc:
        code = str(exc) if isinstance(exc, IdentityError) else "IDENTITY_PREPARATION_FAILED"
        print(json.dumps({"ok": False, "error": {"code": code,
            "message": "Leo AI identity preparation failed; no conversation was changed."}}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

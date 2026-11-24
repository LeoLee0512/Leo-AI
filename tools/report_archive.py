"""Resolve historical reports without silently skipping missing evidence."""
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
HEADINGS = re.compile(r"^### R\d{3} — (.+)$", re.MULTILINE)


def read_report(relative: str, repo: Path = REPO) -> str:
    """Return only the requested report, from disk or its unique archive entry."""
    root = repo.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Report path escapes the repository")
    if path.is_file():
        return path.read_text(encoding="utf-8")
    archive = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = list(HEADINGS.finditer(archive))
    matches = [i for i, m in enumerate(headings) if m.group(1) == "项目/" + path.relative_to(root).as_posix()]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one archived report for {relative}; found {len(matches)}")
    i = matches[0]
    section = archive[headings[i].end():headings[i + 1].start() if i + 1 < len(headings) else len(archive)]
    opening = re.search(r"^(`{3,})markdown\n", section, re.MULTILINE)
    end = section.rfind("\n" + opening.group(1) + "\n\n</details>") if opening else -1
    if opening is None or end < opening.end():
        raise ValueError(f"Incomplete archived report: {relative}")
    return section[opening.end():end] + "\n"

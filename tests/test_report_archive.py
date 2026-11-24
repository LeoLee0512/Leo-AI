from pathlib import Path
import pytest
from tools.report_archive import read_report

ROOT = Path(__file__).resolve().parents[1]


def section(path, body):
    return f"### R001 — 项目/{path}\n\n<details>\n<summary>原文</summary>\n\n```markdown\n{body}\n```\n\n</details>\n"


def test_archive_does_not_borrow_evidence_from_another_report(tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(section("docs/a.md", "first") + section("docs/b.md", "41 reconstructed tests"), encoding="utf-8")
    assert read_report("docs/a.md", tmp_path) == "first\n"
    assert read_report("docs/b.md", tmp_path) == "41 reconstructed tests\n"


@pytest.mark.parametrize("archive", ["unrelated evidence", section("docs/a.md", "one") * 2])
def test_missing_or_duplicate_archived_evidence_fails_closed(tmp_path, archive):
    (tmp_path / "CHANGELOG.md").write_text(archive, encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        read_report("docs/a.md", tmp_path)


def test_truncated_archive_fails_closed(tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(section("docs/a.md", "one").split("</details>")[0], encoding="utf-8")
    with pytest.raises(ValueError):
        read_report("docs/a.md", tmp_path)


def test_archived_checklist_is_exactly_27_unique_items():
    import re
    text = read_report("docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md", ROOT)
    items = re.findall(r"^\|\s*([A-F]\d)\s*\|", text, re.MULTILINE)
    assert len(items) == len(set(items)) == 27

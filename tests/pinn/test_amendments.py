"""Amendment register: A-0002 cannot be effective before A-0001 and Constitution 1.1 (A-0002 second review, item 6)."""

from pathlib import Path

import pytest

from pinn.governance.amendments import load_amendment_register, parse_frontmatter, validate_amendment_register
from pinn.governance.prelock import PrelockPaths, declared_constitution_version, run_prelock

ROOT = Path(__file__).resolve().parents[2]


def amendment(aid, old, new, status, date=None, depends=None):
    entry = {"amendmentId": aid, "oldVersion": old, "newVersion": new, "status": status,
             "effectiveDate": date or ("PENDING" if status == "PROPOSED" else "2026-09-15")}
    if depends is not None:
        entry["dependsOn"] = depends
    return entry


DEP_ON_A1 = [{"amendmentId": "A-0001", "requiredStatus": "ACCEPTED", "requiredConstitutionVersion": "1.1"}]


def test_real_register_matches_the_constitution():
    register = load_amendment_register(ROOT / "governance/AMENDMENTS")
    version = declared_constitution_version((ROOT / "governance/PINN_RESEARCH_CONSTITUTION.md").read_bytes())
    assert validate_amendment_register(register, constitution_version=version) == []
    a2 = next(entry for entry in register if entry["amendmentId"] == "A-0002")
    assert a2["dependsOn"] == DEP_ON_A1 and a2["status"] == "ACCEPTED" and a2["effectiveDate"] == "2026-09-15"


def test_a0002_cannot_become_effective_while_a0001_is_proposed():
    register = [amendment("A-0001", "1.0", "1.1", "PROPOSED"),
                amendment("A-0002", "1.1", "1.2", "ACCEPTED", depends=DEP_ON_A1)]
    errors = validate_amendment_register(register, constitution_version="1.0")
    assert any("A-0001 is PROPOSED, required ACCEPTED" in error for error in errors)
    assert any("accepted chain is at 1.0" in error for error in errors)


def test_a0002_cannot_apply_against_constitution_1_0():
    register = [amendment("A-0001", "1.0", "1.1", "ACCEPTED"),
                amendment("A-0002", "1.1", "1.2", "ACCEPTED", depends=DEP_ON_A1)]
    errors = validate_amendment_register(register, constitution_version="1.0")
    assert any("declares version '1.0'" in error and "ends at 1.2" in error for error in errors)


def test_a0002_may_apply_when_a0001_is_accepted_and_the_constitution_is_1_1():
    register = [amendment("A-0001", "1.0", "1.1", "ACCEPTED"),
                amendment("A-0002", "1.1", "1.2", "PROPOSED", depends=DEP_ON_A1)]
    assert validate_amendment_register(register, constitution_version="1.1") == []
    register[1] = amendment("A-0002", "1.1", "1.2", "ACCEPTED", depends=DEP_ON_A1)
    assert validate_amendment_register(register, constitution_version="1.2") == []
    assert any("ends at 1.2" in error for error in validate_amendment_register(register, constitution_version="1.1"))


def test_dependency_targets_and_versions_are_checked():
    missing = [amendment("A-0002", "1.1", "1.2", "PROPOSED", depends=DEP_ON_A1)]
    assert any("unknown amendment 'A-0001'" in error for error in validate_amendment_register(missing, constitution_version="1.0"))
    wrong = [amendment("A-0001", "1.0", "1.1", "ACCEPTED"),
             amendment("A-0002", "1.1", "1.2", "ACCEPTED",
                       depends=[{"amendmentId": "A-0001", "requiredStatus": "ACCEPTED", "requiredConstitutionVersion": "1.5"}])]
    assert any("required 1.5" in error for error in validate_amendment_register(wrong, constitution_version="1.2"))


def test_status_and_date_discipline():
    assert any("needs an effectiveDate" in error for error in
               validate_amendment_register([amendment("A-0001", "1.0", "1.1", "ACCEPTED", date="PENDING")], constitution_version="1.1"))
    assert any("must carry effectiveDate PENDING" in error for error in
               validate_amendment_register([amendment("A-0001", "1.0", "1.1", "PROPOSED", date="2026-09-15")], constitution_version="1.0"))
    assert any("registered twice" in error for error in validate_amendment_register(
        [amendment("A-0001", "1.0", "1.1", "ACCEPTED"), amendment("A-0001", "1.1", "1.2", "PROPOSED")], constitution_version="1.1"))
    assert any("not one of" in error for error in validate_amendment_register(
        [amendment("A-0001", "1.0", "1.1", "DRAFT", date="PENDING")], constitution_version="1.0"))


def test_frontmatter_parser_reads_the_dependency_list():
    text = '---\namendmentId: A-0002\noldVersion: 1.1\nnewVersion: 1.2\nstatus: PROPOSED\neffectiveDate: PENDING\n' \
           'dependsOn:\n  - amendmentId: A-0001\n    requiredStatus: ACCEPTED\n    requiredConstitutionVersion: "1.1"\n---\n\n## reason\n'
    parsed = parse_frontmatter(text)
    assert parsed["dependsOn"] == DEP_ON_A1 and parsed["status"] == "PROPOSED"
    with pytest.raises(ValueError):
        parse_frontmatter("no frontmatter")
    with pytest.raises(ValueError):
        parse_frontmatter("---\namendmentId: A-0002\n")


def test_prelock_runs_the_register_check():
    result = run_prelock(PrelockPaths.defaults(ROOT))
    assert result["checks"]["amendmentRegister"]["status"] == "PASS"
    assert result["prelockStatus"] == "PASS"

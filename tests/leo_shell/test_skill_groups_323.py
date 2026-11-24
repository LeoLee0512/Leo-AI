"""3.2.3 · A skill collection is switched as one; biology is off by default, once."""
import json
import logging

import pytest

from leo_shell import extensions
from leo_shell.skill_groups import DEFAULT_OFF, MARKER, SkillGroups


class FakeGateway:
    def __init__(self, skills):
        self.skills = skills
        self.toggles = []

    def request(self, payload):
        if payload["operation"] == "skills":
            return {"ok": True, "data": {"skills": [dict(s) for s in self.skills]}}
        if payload["operation"] == "skill_toggle":
            self.toggles.append((payload["name"], payload["enabled"]))
            next(s for s in self.skills if s["name"] == payload["name"])["enabled"] = payload["enabled"]
            return {"ok": True, "data": {"ok": True}}
        raise AssertionError(payload)


def catalog(bio_on=(True, True, True)):
    return ([{"name": f"bio-{i}", "collection": "bioskills", "enabled": on} for i, on in enumerate(bio_on)]
            + [{"name": "scvi-tools", "collection": "", "enabled": True}, {"name": "lean-math", "collection": "", "enabled": True}])


def groups(tmp_path, gateway):
    return SkillGroups(tmp_path, gateway, logger=logging.getLogger("t"), start=False)


def test_a_collection_is_switched_as_one_and_only_changed_members_are_sent(tmp_path):
    gw = FakeGateway(catalog((True, False, True)))
    result = groups(tmp_path, gw).set_collection("bioskills", False)
    assert result == {"collection": "bioskills", "members": 3, "changed": 2, "enabled": False}
    assert gw.toggles == [("bio-0", False), ("bio-2", False)]
    # Skills outside the collection are never touched.
    assert all(s["enabled"] for s in gw.skills if not s["collection"])
    gw.toggles.clear()
    assert groups(tmp_path, gw).set_collection("bioskills", True)["changed"] == 3


def test_page_requests_are_checked(tmp_path):
    g = groups(tmp_path, FakeGateway(catalog()))
    for bad in ({"collection": "../x", "enabled": True}, {"collection": "bioskills", "enabled": "yes"}, {"enabled": True}):
        with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
            g.handle(bad)
    with pytest.raises(ValueError, match="SKILL_COLLECTION_NOT_FOUND"):
        g.handle({"collection": "chemskills", "enabled": False})


def test_biology_is_switched_off_once_and_then_left_to_the_person(tmp_path):
    assert DEFAULT_OFF == ("bioskills",)
    gw = FakeGateway(catalog())
    g = groups(tmp_path, gw)
    assert not g.defaults_applied()
    done = g.apply_defaults()
    assert done["bioskills"]["members"] == 3 and done["bioskills"]["switchedOff"] == 3
    assert not any(s["enabled"] for s in gw.skills if s["collection"] == "bioskills")
    marker = json.loads((tmp_path / MARKER).read_text(encoding="utf-8"))
    assert set(marker["defaultOff"]) == {"bioskills"} and g.defaults_applied()
    # The person switches biology back on; a later launch does not switch it off again.
    g.set_collection("bioskills", True)
    gw.toggles.clear()
    later = SkillGroups(tmp_path, gw, logger=logging.getLogger("t"), start=True)
    later.close()
    assert gw.toggles == [] and all(s["enabled"] for s in gw.skills)


def test_an_installation_without_the_collection_still_records_the_default(tmp_path):
    gw = FakeGateway([{"name": "lean-math", "collection": "", "enabled": True}])
    done = groups(tmp_path, gw).apply_defaults()
    assert done["bioskills"]["members"] == 0 and gw.toggles == []


def test_the_operation_is_local_to_leo():
    assert extensions.SKILL_GROUP_OPERATIONS == ("skill_collection_toggle",)

"""2.2.10: the local-env-check skill's one-line description is what the model reads every turn.

The upstream prompt lists a skill by name and a description that is cut at 200 characters, so the
instruction that matters must fit in that line and the file must parse the way the loader reads it.
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "local-env-check"


def _front_matter():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md must open with a front-matter block"
    return dict(line.split(": ", 1) for line in match.group(1).splitlines()), text


def test_the_front_matter_names_the_directory_and_is_leos_own():
    meta, _ = _front_matter()
    assert meta["name"] == SKILL.name == "local-env-check"
    assert meta["origin"] == "leo" and meta["license"] == "MIT"


def test_the_description_fits_the_line_the_prompt_keeps_and_carries_the_instruction():
    meta, _ = _front_matter()
    description = meta["description"]
    assert len(description) <= 197, "the loader cuts a longer description with an ellipsis"
    assert "pip list" in description and "web_search" in description and "web_fetch" in description


def test_the_body_keeps_installs_out_of_scope_and_names_real_host_calls():
    _, text = _front_matter()
    assert "host.bash(" in text and "host.accelerator_status()" in text
    assert "own approval" in text

"""3.2.15 · When DeepSeek writes a full, formatted answer as a remark and then submits a short plain-text digest
of it, the full one is shown as the answer (owner's 「什么是PDE的特征线」 screenshots, 2026-10-01: 1340 characters
with formulas folded away, 440 shown). Measured with the page's own functions (node): the owner's pair → fuller;
the 3.2.14 poem pair → same; a plan remark, a related but different remark, a long remark with another answer and
a long work log with a short result → neither."""
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "stage" / "workbench.js").read_text(encoding="utf-8")


def test_a_digest_of_a_longer_remark_gives_way_to_the_remark():
    assert "function fullerAnswer(remark,answer)" in JS
    assert "if(nx<200||ny<10||nx<1.5*ny)return false" in JS and "return common/ny>=0.6" in JS


def test_the_full_remark_is_shown_in_place_and_the_digest_is_not_repeated():
    assert "m!==fuller&&!(final&&sameAnswer(m.content,final.content))" in JS
    assert ".concat(fuller?[final]:[])" in JS


def test_the_3_2_14_rule_is_kept():
    assert "2*common/(nx+ny)>=0.75" in JS

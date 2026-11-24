"""3.2.14 · DeepSeek's reworded answer is not shown again in 「思考与步骤」 (owner, 2026-09-30, screenshot of
「落花时节又逢君」: the remark and the answer said the same thing). Measured with the page's own code (node):
the owner's pair scores 0.88; a related but different remark 0.55; ordinary remarks under 0.1."""
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "stage" / "workbench.js").read_text(encoding="utf-8")


def test_a_remark_that_restates_the_answer_is_left_out_of_the_fold():
    assert "function sameAnswer(a,b)" in JS and "2*common/(nx+ny)>=0.75" in JS
    assert "!(final&&sameAnswer(m.content,final.content))" in JS


def test_short_texts_are_never_judged_and_the_answer_itself_always_shows():
    assert "if(nx<10||ny<10)return false" in JS
    # Left-out remarks are neither in the fold nor shown as messages; the answer row is unchanged.
    assert "if(!notes.includes(m)&&!hidden.includes(m))area.append(messageRow(m))" in JS


def test_punctuation_and_spacing_do_not_count():
    assert r"replace(/[\s\p{P}\p{S}_]+/gu,'')" in JS

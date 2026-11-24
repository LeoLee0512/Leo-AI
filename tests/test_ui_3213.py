"""3.2.13 · Three small things from the owner's 3.2.12 screenshots (2026-09-30, 「问题有点小多」):
the approval pop-up's text ran out of its box, switching models could end in 「会话模型已变化」 with the list
showing a model not in use, and 「用量」's 「本轮」 showed another model's call."""
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / "stage"
JS = (STAGE / "workbench.js").read_text(encoding="utf-8")
CSS = (STAGE / "workbench.css").read_text(encoding="utf-8")


def test_choices_inside_toolbar_pop_ups_wrap():
    # The 3.1.0 rule keeps toolbar buttons on one line; it also caught the approval choices (buttons).
    assert ".composer-toolbar :is(button,.picker-button),.stop{white-space:nowrap}" in CSS
    assert ".composer-toolbar .approval-pop [data-mode],.composer-toolbar .usage-pop button{white-space:normal}" in CSS


def test_the_model_list_waits_for_a_switch_and_shows_the_real_model_after_a_failure():
    body = JS[JS.index("async function selectModel()"):JS.index("async function prepareMessage(")]
    assert "select.disabled=true" in body and "finally{select.disabled=false;}" in body
    assert "catch(error){if(state.frame?.id===fid)await refreshModels().catch(()=>{});throw error;}" in body


def test_this_turn_counts_only_the_chosen_models_calls():
    assert "mine=calls.filter(g=>g.model===id),last=mine[mine.length-1]?.usage||null" in JS
    assert "当前模型在这个对话里还没有调用过" in JS

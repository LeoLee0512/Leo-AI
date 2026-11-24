"""3.2.12 · 「用量」 limits Leo knows, and no temperature where it has no effect (owner, 2026-09-30:
「deepseek不是百万上下文吗」 — the panel showed 272.0k for DeepSeek V4 and for the local model)."""
import re
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "stage" / "workbench.js").read_text(encoding="utf-8")


def test_deepseek_v4_uses_its_published_one_million_context():
    table = re.search(r"const KNOWN_CONTEXT=\{([^}]*)\}", JS).group(1)
    assert "'deepseek-v4-pro':1e6" in table and "'deepseek-v4-flash':1e6" in table


def test_the_local_model_never_takes_the_daemons_provider_default():
    # The local limit comes only from the relay's record (the real 16K), never from /context.
    assert "m?.local?(req?.context||null):(KNOWN_CONTEXT[m?.model]||usage.context?.limit||null)" in JS
    assert "上限在下一条消息后显示" in JS


def test_other_models_keep_the_daemons_figure_but_say_it_may_be_wrong():
    assert "上限为底层默认值，可能不准" in JS


def test_deepseek_v4_temperature_is_shown_as_not_applicable():
    assert "function noTemperature(id){return /^deepseek-v4/.test(id||'');}" in JS
    assert "slider.disabled=!id||!t||fixed" in JS and "'不适用'" in JS
    assert "思考模式下温度不起作用，所以这里不能调" in JS
    assert "可能不起作用" not in JS


def test_millions_are_written_as_m():
    assert "n>=1e6?(n/1e6).toFixed(n%1e6?1:0)+'M'" in JS

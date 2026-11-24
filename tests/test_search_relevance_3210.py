"""3.2.10 · Search results that have nothing to do with the question get an honest fixed answer, and each
search is listed once in 「网页」 (owner's 3.2.9 test, 2026-09-30: 「飞雪江南不见梅」 came back as VPN and
video-site pages twice; the local model invented 「云间月上人未归」 by 「张旭《冬夜》」 both times)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge"))
import leo_local_relay as relay  # noqa: E402
from leo_shell import workbench  # noqa: E402

VPN_PAGES = ("联网搜索：找到 3 条结果。\n"
             "1. Proton - 全球高速隐私加密网络 VPN 服务 | Proton VPN\n   https://protonmv.com.cn/\n"
             "   6 days ago · Proton VPN 提供军事级加密、严格无日志与 NetShield 广告拦截\n"
             "2. 免费 VPN 下载 2026： VPN 免费额度真实对比，哪个能在中国用\n   https://vpn-power.com/\n   免费VPN下载去哪找？\n"
             "3. 腾讯视频频道 - 热门电影电视剧综艺动漫在线观看\n   https://v.qq.com/\n   腾讯视频官方网站")
POEM_PAGES = ("联网搜索：找到 2 条结果。\n"
              "1. \" 无边落木萧萧下 ，不尽长江滚滚来。\"全诗赏析_古文岛\n   https://www.gushiwen.cn/mingju/juv.aspx?id=1\n"
              "   注释 落木：指秋天飘落的树叶。\n"
              "2. 登高（唐代杜甫诗作）_百度百科\n   https://baike.baidu.com/item/登高\n   落叶一望无际萧萧堕下，长江不见尽头滚滚涌来。")


def turn(query, stdout):
    return {"model": relay.MODEL, "messages": [
        {"role": "user", "content": "问题"},
        {"role": "assistant", "content": "```python\n" + relay.web_search_cell(query) + "```"},
        {"role": "user", "content": "[Observation]\nstdout:\n" + stdout + "\n[usage wall=0.5s cpu=0.0s rss=1kb]"}]}


def test_unrelated_pages_get_an_honest_answer():
    answer = relay.fixed_answer(turn("飞雪江南不见梅", VPN_PAGES))
    assert answer.startswith("我联网搜索了「飞雪江南不见梅」，但搜到的网页和这个问题无关") and "不想编" in answer


def test_pages_that_contain_the_phrase_go_to_the_model():
    assert relay.fixed_answer(turn("无边落木萧萧下", POEM_PAGES)) is None


@pytest.mark.parametrize("query", ["PINN 最新论文", "pinn", "最近的 PINN 新论文"])
def test_any_query_term_counts_and_case_is_ignored(query):
    pages = "联网搜索：找到 1 条结果。\n1. 物理信息神经网络（PINN）综述\n   https://example.org\n   一篇综述"
    assert relay.fixed_answer(turn(query, pages)) is None


def test_web_addresses_do_not_count_as_mentions():
    pages = "联网搜索：找到 1 条结果。\n1. 酒店预订\n   https://example.org/feixue-jiangnan-pinn\n   酒店"
    assert relay.fixed_answer(turn("pinn", pages)) is not None


def test_a_query_too_short_to_match_is_not_left_to_the_model():
    # One character is not evidence that a page is about the question. Saying it matched
    # used to skip the fixed answer, and the model then invented one.
    answer = relay.fixed_answer(turn("梅", VPN_PAGES))
    assert answer.startswith("我联网搜索了「梅」，但搜到的网页和这个问题无关") and "不想编" in answer


def test_the_fixed_answer_holds_even_after_the_person_objects():
    payload = turn("飞雪江南不见梅", VPN_PAGES)
    payload["messages"][:0] = [{"role": "user", "content": "飞雪江南不见梅下一句是什么"},
                               {"role": "assistant", "content": "云间月上人未归。"}]
    assert relay.fixed_answer(payload) is not None


def test_notebook_entries_no_longer_carry_a_second_search_listing():
    shaped = workbench.shape_notebook({"entries": [{"source": relay.web_search_cell("无边落木萧萧下"), "stdout": POEM_PAGES}]})
    assert "webSearch" not in shaped["entries"][0]

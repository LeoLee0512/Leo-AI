"""3.2.9 · Web search that works from the owner's network, an honest answer when it finds nothing,
and searches that read as searches (owner, 2026-09-30: 「联网在哪？而且它为啥还要准备Python Cell，回答也莫名奇妙」)."""
import ast
import hashlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge"))
import leo_local_relay as relay  # noqa: E402
import leo_runtime_compat as compat  # noqa: E402
from leo_shell import workbench  # noqa: E402

# A stand-in for upstream webtools.py with the two audited anchors (the real file is checked on a copy
# of the daemon's source before release, see CHANGELOG).
FAKE_WEBTOOLS = (
    "def _open_http_response(url):\n"
    "    for response in [url]:\n"
    "        if True:\n"
    "            if True:\n"
    "                yield (\n"
    "                    response.raw,\n"
    "                    response.url,\n"
    "                )\n"
    "\n"
    "_ENGINES: tuple[tuple[str, object], ...] = (\n"
    '    ("duckduckgo", _ddg_html),\n'
    '    ("bing", _bing_html),\n'
    '    ("duckduckgo-lite", _ddg_lite),\n'
    ")\n"
)


@pytest.fixture
def audited(monkeypatch):
    lf = FAKE_WEBTOOLS.encode()
    crlf = FAKE_WEBTOOLS.replace("\n", "\r\n").encode()
    monkeypatch.setattr(compat, "WEB_SOURCE_SHA256",
                        frozenset({hashlib.sha256(lf).hexdigest(), hashlib.sha256(crlf).hexdigest()}))
    return lf, crlf


@pytest.mark.parametrize("form", [0, 1])
def test_the_web_fix_decodes_responses_and_tries_bing_first(audited, form):
    original = audited[form]
    updated = compat.web_compatible_source(original)
    text = updated.decode()
    assert "response.raw.decode_content = True" in text and compat.WEB_MARKER in text
    assert text.index('("bing", _bing_html)') < text.index('("duckduckgo", _ddg_html)')
    assert (b"\r\n" in updated) == bool(form) and b"\r\r" not in updated
    # Applying again is a no-op, and the original bytes are recovered exactly.
    assert compat.web_compatible_source(updated) == updated


def test_an_unknown_webtools_is_refused(audited):
    with pytest.raises(compat.CompatibilityError, match="RUNTIME_WEB_SOURCE_UNKNOWN"):
        compat.web_compatible_source(audited[0] + b"# changed upstream\n")


def test_a_failed_web_fix_never_stops_connecting(tmp_path, audited):
    base = tmp_path / "leo"
    source = base / "sources" / "rev"
    (source / "openai4s").mkdir(parents=True)
    (source / "openai4s" / "webtools.py").write_bytes(b"# some other upstream revision\n")
    result = compat._apply_web_fix(base, source, check=False)
    assert result["applied"] is False and result["skipped"] == "RUNTIME_WEB_SOURCE_UNKNOWN"
    assert (source / "openai4s" / "webtools.py").read_bytes() == b"# some other upstream revision\n"


def test_the_web_fix_is_applied_and_its_original_kept(tmp_path, audited):
    base = tmp_path / "leo"
    source = base / "sources" / "rev"
    (source / "openai4s").mkdir(parents=True)
    target = source / "openai4s" / "webtools.py"
    target.write_bytes(audited[1])
    first = compat._apply_web_fix(base, source, check=False)
    assert first["applied"] is True and first["changed"] is True
    assert (base / "runtime-compat-originals" / (first["previous_sha256"] + ".py")).read_bytes() == audited[1]
    again = compat._apply_web_fix(base, source, check=False)
    assert again["applied"] is True and again["changed"] is False


def run_cell(query, results):
    """Execute the relay's fixed cell against a fake host; return what it prints."""
    class Host:
        def web_search(self, q, num_results):
            assert q == query and num_results == 5
            return {"results": results}
    out = io.StringIO()
    with redirect_stdout(out):
        exec(relay.web_search_cell(query), {"host": Host()})
    return out.getvalue()


def test_the_cell_is_readable_and_says_what_it_found():
    code = relay.web_search_cell("无边落木萧萧下")
    assert code.splitlines()[0] == '_r = host.web_search("无边落木萧萧下", num_results=5)'
    printed = run_cell("无边落木萧萧下", [{"title": "登高\n杜甫", "url": "https://example.org/a", "snippet": "无边落木萧萧下，\n不尽长江滚滚来"}])
    assert printed.splitlines() == ["联网搜索：找到 1 条结果。", "1. 登高 杜甫", "   https://example.org/a",
                                    "   无边落木萧萧下， 不尽长江滚滚来"]
    assert run_cell("无边落木萧萧下", []).strip() == relay.WEB_SEARCH_EMPTY


def test_a_hostile_query_is_still_only_a_string():
    query = 'x"); import os;  os.system("rm -rf /") #'
    tree = ast.parse(relay.web_search_cell(query))
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "web_search")
    assert call.args[0].value == query.strip()
    assert relay.searched_query(relay.web_search_cell(query)) == query.strip()


def history(observation, query="无边落木萧萧下的下一句是", cell=None):
    cell = cell if cell is not None else "```python\n" + relay.web_search_cell(query) + "```"
    return {"model": relay.MODEL, "messages": [
        {"role": "system", "content": "host.submit_output ... Finishing: ..."},
        {"role": "user", "content": "无边落木萧萧下的下一句是"},
        {"role": "assistant", "content": cell},
        {"role": "user", "content": observation}]}


def test_an_empty_search_gets_a_fixed_honest_answer():
    answer = relay.fixed_answer(history("[Observation]\nstdout:\n联网搜索：没有找到结果。\n[usage wall=17.8s cpu=0.0s rss=1kb]"))
    assert answer.startswith("我联网搜索了「无边落木萧萧下的下一句是」，但没有找到结果") and "不想编" in answer


def test_the_3_2_8_cell_that_found_nothing_is_recognised_too():
    old_cell = ('```python\n_r = host.web_search("\\u65e0\\u8fb9\\u843d\\u6728", num_results=5)\n'
                '_rows = _r.get("results") or []\n```')
    answer = relay.fixed_answer(history("[Observation]\nstdout:\n没有找到结果。 \n", cell=old_cell))
    assert answer is not None and "「无边落木」" in answer


@pytest.mark.parametrize("observation", [
    "[Observation]\nstdout:\n联网搜索：找到 3 条结果。\n1. 登高\n   https://example.org\n   无边落木萧萧下",
    "[Observation]\nERROR:\nboom",
    "联网搜索：没有找到结果。",
])
def test_other_observations_stay_with_the_model(observation):
    # 3.2.10: results must mention the query to go to the model, so the query is the phrase they contain.
    assert relay.fixed_answer(history(observation, query="无边落木萧萧下")) is None


def test_an_ordinary_code_cell_is_not_mistaken_for_a_search():
    cell = "```python\nprint('联网搜索：没有找到结果。')\n```"
    assert relay.fixed_answer(history("[Observation]\nstdout:\n联网搜索：没有找到结果。", cell=cell)) is None


class FakeLlama:
    def __call__(self, port, route, body):
        if route == "/apply-template":
            self.body = body
            return {"prompt": "P"}
        if route == "/tokenize" and body.get("content") == "<think></think>":
            return {"tokens": [151667, 151668]}
        return {"tokens": list(range(9000))}


def test_the_fixed_answer_is_what_the_model_is_held_to(monkeypatch):
    fake = FakeLlama()
    monkeypatch.setattr(relay, "local_json", fake)
    payload = history("[Observation]\nstdout:\n联网搜索：没有找到结果。")
    body = json.loads(relay.prepare_chat(payload, 8080, 16384))
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["arguments"]["properties"]["summary"]["const"] == relay.fixed_answer(payload)
    assert body["messages"][-1]["content"].startswith("The web search found nothing.")


def test_the_reminder_asks_to_check_uncertain_facts_with_short_queries():
    assert "先用 web_search 查证" in relay.LOCAL_COMPLETION_REMINDER
    assert "不要照抄整句提问" in relay.LOCAL_COMPLETION_REMINDER


def test_the_search_key_goes_only_to_the_daemons_search_setting():
    assert workbench.route({"operation": "search_config"}) == ("GET", "/search/config", None)
    assert workbench.route({"operation": "search_key_save", "apiKey": " tvly-abc123 "}) == (
        "PUT", "/search/config", {"api_key": "tvly-abc123"})
    assert workbench.route({"operation": "search_key_clear"}) == ("PUT", "/search/config", {"clear_api_key": True})
    assert workbench.route({"operation": "search_key_save", "apiKey": "tvly-abc\n"})[2] == {"api_key": "tvly-abc"}
    for bad in ("", "   ", "a b", "x" * 257, "k\tx", "密钥", 5, None):
        with pytest.raises(ValueError):
            workbench.route({"operation": "search_key_save", "apiKey": bad})


def test_the_page_learns_only_whether_a_key_is_set():
    shaped = workbench.shape_search_config({"endpoint": "https://api.tavily.com/search", "api_key_configured": True,
                                            "api_key": "never-this"})
    assert shaped == {"configured": True}


def test_the_page_shows_searches_as_searches():
    js = (ROOT / "stage" / "workbench.js").read_text(encoding="utf-8")
    assert "'联网搜索：「'" in js and "localSearchStep" in js
    # 3.2.10: the daemon already records cell searches as steps; listing them from the notebook too
    # (3.2.9) showed every search twice in 「网页」.
    assert "localSearches" not in js and "webSearch" not in js

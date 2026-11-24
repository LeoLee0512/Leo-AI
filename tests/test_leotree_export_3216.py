"""3.2.16 · 整理成知识树 / 导出到 LeoTree (owner, 2026-10-02: 「开始，在 Leo 里恢复」).

The export of 2026-09-07 lived in the injection layer removed on 2026-09-26; it is restored on the workbench's own
message reader. The mapping is pure (no model call) and is run here with node, the page's own code, extracted from
stage/workbench.js between the LEO-TREE-EXPORT markers. During development the same output was also accepted by
Leo Tree 1.0.0-beta.3's own validateTree / parseImport / mergeTreeIntoWorkspace (CHANGELOG, 2026-10-02).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "stage" / "workbench.js").read_text(encoding="utf-8")
HTML = (ROOT / "stage" / "workbench.html").read_text(encoding="utf-8")

MESSAGES = [
    {"role": "user", "seq": 1, "message_id": "m1", "content": "解释热方程 $u_t = \\kappa u_{xx}$ 的能量为什么衰减？"},
    {"role": "assistant", "seq": 2, "message_id": "m2", "content":
        "先给结论：能量单调下降。\n\n## 能量恒等式\n\n$$\\frac{d}{dt}\\frac12\\int u^2 = -\\kappa\\int u_x^2$$\n\n"
        "## 一个数值例子\n\n```python\n# 代码块里以 # 开头的行不是标题\nprint(1)\n```\n\n### 小结 ###\n\n能量只会减少。"},
    {"role": "tool", "seq": 3, "content": "ignored"},
    {"role": "user", "seq": 4, "content": "   "},
]


def run_node(script: str) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    block = JS[JS.index("// LEO-TREE-EXPORT:BEGIN"):JS.index("// LEO-TREE-EXPORT:END")]
    source = (f"const api=new Function({json.dumps(block + '; return {treeChunks,serializeTreeDraft,treeDraft,treeFileName};')})();"
              + script)
    done = subprocess.run([node, "-e", source], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_the_conversation_maps_to_a_leo_tree_v3_single_tree_envelope():
    out = run_node(
        f"const d=api.treeDraft({{id:'frame-1',name:'热方程'}},{json.dumps(MESSAGES, ensure_ascii=False)},"
        "'2026-10-02T08:00:00.000Z',()=>'u');api.serializeTreeDraft(d);console.log(JSON.stringify(d));")
    tree = out["tree"]
    assert out["schemaVersion"] == 3 and tree["id"] == "leo-u" and tree["title"] == "热方程"
    assert [s["title"] for s in tree["sections"]] == ["问题与目标", "知识与推导"]
    assert [n["title"] for n in tree["nodes"]] == [
        "解释热方程 $u_t = \\kappa u_{xx}$ 的能量为什么衰减？", "先给结论：能量单调下降。", "能量恒等式", "一个数值例子", "小结"]
    assert all(n["status"] == "todo" and n["attachments"] == [] for n in tree["nodes"])
    assert any("# 代码块里以 # 开头的行不是标题" in n["note"] for n in tree["nodes"])     # fences never make nodes
    assert [n["order"] for n in tree["nodes"] if n["sectionId"].endswith("knowledge")] == [0, 1, 2, 3]
    assert tree["settings"]["leoSource"]["sourceMessageCount"] == 2                     # tool and blank skipped
    assert tree["settings"]["leoSource"]["attachmentsIncluded"] is False
    assert "未经自动事实核验" in tree["description"]


def test_limits_and_empty_conversations_fail_with_named_errors():
    out = run_node(
        "const r={};for(const [k,f] of Object.entries({"
        "empty:()=>api.treeDraft({id:'f'},[{role:'user',content:' '}]),"
        "big:()=>api.serializeTreeDraft({schemaVersion:3,tree:{title:'x',nodes:Array.from({length:501},()=>({title:'n',note:''}))}}),"
        "untitled:()=>api.serializeTreeDraft({schemaVersion:3,tree:{title:' ',nodes:[{title:'n',note:''}]}})"
        "}))try{f();r[k]='none';}catch(e){r[k]=e.message;}"
        "r.file=api.treeFileName('热方程: 能量/衰减?');console.log(JSON.stringify(r));")
    assert out == {"empty": "TREE_EMPTY", "big": "TREE_TOO_LARGE", "untitled": "TREE_INVALID",
                   "file": "热方程_ 能量_衰减_-LeoTree.json"}


def test_the_file_menu_dialog_and_help_are_wired():
    assert '<button role="menuitem" data-command="knowledge-tree">整理成知识树…</button>' in HTML
    assert 'id="tree-dialog"' in HTML and 'id="tree-save"' in HTML and 'id="tree-cancel"' in HTML
    assert "'knowledge-tree':openKnowledgeTree" in JS
    assert "[data-command=export],[data-command=knowledge-tree]" in JS        # disabled without an open conversation
    assert "$('tree-close').onclick=$('tree-cancel').onclick=" in JS
    assert "if(state.execution)throw Error('TREE_RUNNING')" in JS              # never exports a half-written answer
    assert "download(file,json,'application/json;charset=utf-8')" in JS        # native Save dialog (ALLOW_DOWNLOADS)
    assert "整理成知识树" in HTML[HTML.index('id="help-dialog"'):]


def test_both_exports_share_one_complete_message_reader():
    assert JS.count("async function allMessages(frame)") == 1
    assert "const unique=await allMessages(frame);" in JS
    assert "displayMessages(await allMessages(frame))" in JS

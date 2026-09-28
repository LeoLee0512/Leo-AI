# local-literature-rag · 本地文献库 RAG（中文说明）

对**你自己的 PDF 文献库**做检索，回答「我库里关于 X 的论文说了什么」，每一条结论都带 `[文件名 p.页码]` 出处，可以回原文核对。

- 归属：Leo 专属技能（`origin: leo`，MIT）。不修改 `upstream/OpenAI4S/`。
- 零新依赖：PDF 提取复用内置 `pdf-explore` 的 `pdf_pages`；检索用运行时已有的 `scikit-learn`（TF-IDF + 余弦相似度）。
- 全程本地，不联网，没有第三方服务，所以 SKILL.md 里也就没有 `metadata.third_party`。

## 文献放哪

kernel cell 只能读**当前会话的工作区**（这是 OpenAI4S 的沙箱规则，不是本技能加的限制），所以文献库必须是工作区里的一个目录，默认 `literature/`。

把 PDF 放进去的几种方式：在工作台里把文件拖进会话；让 agent 直接下载到该目录；或者从 artifact 里 materialise 出来。

支持 `.pdf`、`.md`、`.txt`、`.rst`。PDF 走 `pdf_pages`，页码就是真实页码；纯文本按空行切成「伪页」，引用格式保持一致。

## 建库

```python
lit_index_build()                       # 索引 ./literature
lit_index_build("papers/传热")           # 或任意工作区相对目录
lit_index_build(rebuild=True)            # 强制全量重建
lit_index_stats()                        # 只看当前索引状态，不碰文献
```

返回的报告会明说这次做了什么：

```python
{"files": 41, "added": ["新论文.pdf"], "updated": [], "removed": [],
 "unchanged": 40, "chunks": 1187, "index_path": "literature-index/index.json",
 "artifact": {"version_id": "..."}}
```

**增量建库**：每个文件按 `sha256 + 大小 + mtime` 打指纹。指纹没变的文件直接复用已有分块，不重新解析；只有新增和改动过的文件会被重新提取，删掉的文件会从索引里消失。加一篇新论文只解析那一篇。

## 查询

```python
hits = lit_search("误差来源 error decomposition", k=6)
# [{"file": "pinn_error.pdf", "page": 7, "score": 0.41, "text": "...", "chunk_id": 88}, ...]

hits = lit_search("正则化", k=5, files="传热")   # 只在文件名含「传热」的文档里找
```

要**回答问题**的话用 `lit_context`，它把片段连同引用标记一起排好，并附上「只准用这些片段作答」的指令：

```python
ctx = lit_context("稀疏采样下怎么选正则化参数？", k=6)
print(ctx["context"])
```

然后**只根据 `ctx["context"]` 写答案**，每条结论后面跟 `[文件名 p.页码]`，并把原文片段一起给出，方便你翻回去核对。

## 检索不到的时候

`lit_search` 返回空列表，`lit_context` 返回一段明确写着「本地库里没有匹配内容，不要凭记忆作答、不要引用」的提示。这就是答案本身——**说库里没有**，然后建议改用 `literature-review` 去查实时文献。

页码同理：输出的每个 `[文件名 p.页码]` 都必须来自 `lit_search` 真实返回的命中，不许调整、不许猜、不许插值。

## 中英文混合

`lit_analyzer` 对拉丁词照常分词，对中日文连续字符段同时产出**单字**和**二元组**（bigram）。所以「传热」这种词不用分词器也能命中，也就不必引入 `jieba`。

取舍说清楚：字符二元组比真正的分词粗，中文**召回好、精度略逊**于用分词器的方案。想升级的话看下面一节，或者装了 `jieba` 之后把 `lit_analyzer` 换掉——它只被 `lit_encode` 一处使用。

## 跨会话保留

索引写在工作区的 `literature-index/index.json`，同时注册成名为 `leo-literature-index.json` 的 artifact。工作区是**每个会话一份**的，所以换会话之后：

```python
lit_index_load("<在工作台 artifact 列表里看到的 version_id>")
```

仅限**同一个项目**内（这是 OpenAI4S 的 artifact 隔离规则）。不传参数时 `lit_index_load()` 读工作区里的那份。

## 以后升级成语义检索

TF-IDF 匹配的是词，不是意思：提问用词和论文用词不一样就会漏。要换成语义检索，只需要改一个地方——`lit_encode`：

```python
LIT_STATE["encoder"] = my_embedding_fn   # (texts, fit) -> 稠密向量矩阵
```

`lit_search` / `lit_context` / 缓存都会自动走新的编码器，索引格式不用变（分块是以文本形式存的，加载时才向量化）。

---
name: local-env-check
description: Questions about this machine or sandbox (pip list/show, package or Python versions, GPU/CPU/disk/memory, workspace files): run one host.bash or file call. Never web_search or web_fetch for these.
origin: leo
license: MIT
---

# Local environment check

"Which packages are installed?", "what version of numpy?", "is there a GPU?", "how much disk is left?", "what is in this folder?" are questions about **this machine**, not about the outside world. The answer is one command away and the web cannot know it.

The general rule to look external facts up before answering applies to facts *outside* the sandbox: papers, datasets, accession numbers, other people's software. It does not apply here. A web search for `pip list` returns tutorials, not the packages that are installed, and costs a round trip and a possible failure before the real work starts.

## Do this

Run the command directly, once, and read its output:

| Question | Command |
|---|---|
| installed packages | `host.bash("pip list")` |
| one package's version | `host.bash("pip show numpy")` or `import numpy; print(numpy.__version__)` |
| Python version | `host.bash("python --version")` |
| conda environments | `host.bash("conda env list")` |
| GPU | `host.bash("nvidia-smi")`, or `host.accelerator_status()` when the task needs a GPU |
| CPU / memory / disk | `host.bash("nproc")`, `host.bash("free -h")`, `host.bash("df -h")` |
| files in the workspace | `host.list_dir(".")`, `host.glob(...)`, `host.read_file(path)` |

Report what the command printed. If it fails, say so and show the error; do not fill the gap from memory or from a search.

## When the web is right

Only when the question is about something that is not on this machine: whether a newer release of a package exists, what an error message means in general, how a library's API is documented. Answer the local part first, then look up the outside part.

## Boundaries

- Read-only checks only. Installing, upgrading or removing a package is a separate step that needs its own approval.

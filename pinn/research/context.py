"""Explicit execution locations, scoped to one runner invocation (never os.chdir)."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    code_root: Path
    data_root: Path
    executor: str = "Leo AI research worker"

    def document(self):
        return {"codeRoot": str(self.code_root.resolve()), "dataRoot": str(self.data_root.resolve()),
                "executor": self.executor}

    @classmethod
    def from_document(cls, doc):
        return cls(Path(doc["codeRoot"]).resolve(), Path(doc["dataRoot"]).resolve(), doc["executor"])


CURRENT = ContextVar("leo_research_run_context", default=None)


@contextmanager
def using(context):
    token = CURRENT.set(context)
    try:
        yield context
    finally:
        CURRENT.reset(token)


def data_path(legacy):
    context = CURRENT.get()
    return context.data_root / legacy if context else legacy


def actor(legacy):
    context = CURRENT.get()
    return context.executor if context else legacy

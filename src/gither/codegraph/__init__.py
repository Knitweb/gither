"""Code knowledge graph for Gither.

Phase 1: multilingual code bridges built from a clean seed corpus
(Rosetta Code). Phase 2 adds tree-sitter depth and an incremental snapshot
layer for repo-local codegraph updates. Each record is content-addressed so it
can live in the Gither hashgraph canonical layer (see docs/HASHGRAPH_NAVIGATION.md).
"""

from .models import CodeChunk, LangBridge, TaskConcept, content_hash
from .store import FileSnapshot, RepoSnapshot, build_repo_snapshot, load_repo_snapshot, save_repo_snapshot

__all__ = [
    "CodeChunk",
    "FileSnapshot",
    "LangBridge",
    "RepoSnapshot",
    "TaskConcept",
    "build_repo_snapshot",
    "content_hash",
    "load_repo_snapshot",
    "save_repo_snapshot",
]

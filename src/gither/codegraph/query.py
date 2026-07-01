"""In-memory query layer over the content-addressed code corpus.

Loads the JSONL files written by the Rosetta importer and answers the
questions a vibe coder actually asks:

- which languages solve this task?              (the multilingual bridge)
- show me the code for this task in language X;
- which tasks are tagged with feature Y?        (the topic / metadata layer)
- find tasks by free text;
- which tasks have the widest language coverage?

The corpus is small enough to hold in memory. If it grows past a few hundred
MB we will move to an on-disk index, but not before that is measured.
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter
from dataclasses import dataclass, field

from .models import CodeChunk, TaskConcept


@dataclass
class Corpus:
    """Loaded code corpus with query helpers."""

    tasks: dict[str, TaskConcept] = field(default_factory=dict)
    chunks: list[CodeChunk] = field(default_factory=list)

    @classmethod
    def load(cls, directory: str | pathlib.Path) -> "Corpus":
        """Load ``tasks.jsonl`` and ``chunks.jsonl`` from a directory."""
        root = pathlib.Path(directory)
        corpus = cls()
        tasks_path = root / "tasks.jsonl"
        if tasks_path.exists():
            for line in tasks_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                concept = TaskConcept.from_json(json.loads(line))
                corpus.tasks[concept.task] = concept
        chunks_path = root / "chunks.jsonl"
        if chunks_path.exists():
            for line in chunks_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                corpus.chunks.append(CodeChunk.from_json(json.loads(line)))
        return corpus

    def stats(self) -> dict[str, object]:
        """Return a compact summary of the loaded corpus."""
        lang_counter = Counter(chunk.language for chunk in self.chunks)
        per_task = Counter(chunk.task for chunk in self.chunks)
        return {
            "tasks": len(self.tasks),
            "chunks": len(self.chunks),
            "languages": len(lang_counter),
            "top_languages": lang_counter.most_common(10),
            "median_chunks_per_task": (
                sorted(per_task.values())[len(per_task) // 2] if per_task else 0
            ),
            "max_chunks_per_task": max(per_task.values()) if per_task else 0,
        }

    def languages_for_task(self, task: str) -> list[str]:
        """Distinct languages that have at least one chunk for ``task``."""
        return sorted({c.language for c in self.chunks if c.task == task})

    def chunks_for_task(self, task: str, language: str | None = None) -> list[CodeChunk]:
        """Return chunks for a task, optionally filtered to one language."""
        return [
            c
            for c in self.chunks
            if c.task == task and (language is None or c.language == language)
        ]

    def tasks_by_feature(self, feature: str) -> list[TaskConcept]:
        """Tasks whose ``task_features`` contain ``feature`` (case-insensitive)."""
        needle = feature.strip().lower()
        return [
            concept
            for concept in self.tasks.values()
            if any(needle in feat.lower() for feat in concept.task_features)
        ]

    def tasks_by_category(self, category: str) -> list[TaskConcept]:
        """Tasks whose ``categories`` contain ``category`` (case-insensitive)."""
        needle = category.strip().lower()
        return [
            concept
            for concept in self.tasks.values()
            if any(needle in cat.lower() for cat in concept.categories)
        ]

    def search_tasks(self, query: str, limit: int = 20) -> list[TaskConcept]:
        """Free-text search over task titles and descriptions."""
        needle = query.strip().lower()
        if not needle:
            return []
        hits: list[TaskConcept] = []
        for concept in self.tasks.values():
            haystack = (concept.task + " " + concept.description).lower()
            if needle in haystack:
                hits.append(concept)
            if len(hits) >= limit:
                break
        return hits

    def top_tasks_by_language_count(self, limit: int = 10) -> list[tuple[str, int]]:
        """Tasks ranked by how many distinct languages solve them."""
        per_task: dict[str, set[str]] = {}
        for chunk in self.chunks:
            per_task.setdefault(chunk.task, set()).add(chunk.language)
        ranked = sorted(per_task.items(), key=lambda kv: len(kv[1]), reverse=True)
        return [(task, len(langs)) for task, langs in ranked[:limit]]

    def features_index(self) -> dict[str, int]:
        """All known task features and how many tasks carry each."""
        counter: Counter[str] = Counter()
        for concept in self.tasks.values():
            counter.update(concept.task_features)
        return dict(counter.most_common())

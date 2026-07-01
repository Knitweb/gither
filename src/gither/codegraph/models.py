"""Content-addressed records for the code knowledge graph.

Records mirror the hashgraph canonical-layer rules in
docs/HASHGRAPH_NAVIGATION.md:

- canonical identity is a sha256 over deterministic bytes (never over float
  embeddings);
- code chunks and task concepts become content-addressed nodes;
- relationships (which language solves which task) are derived edges.
"""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field


def content_hash(text: str) -> str:
    """Return a stable sha256 content address for canonical text.

    Trailing whitespace and surrounding newlines are stripped so the same code
    stored with cosmetic differences keeps one identity.
    """
    canonical = "\n".join(line.rstrip() for line in text.splitlines()).strip("\n")
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _normalize_language(raw: str) -> str:
    """Normalize a Rosetta ``{{header|...}}`` language label.

    Rosetta writes display aliases as ``C sharp|C#`` or ``F_Sharp|F#``; we keep
    the display form (the part after the last pipe) when present.
    """
    value = raw.strip()
    if "|" in value:
        value = value.rsplit("|", 1)[-1]
    value = value.replace("_", " ").strip()
    return value


@dataclass(frozen=True)
class TaskConcept:
    """A functional task and its classifying metadata.

    The metadata side (``task_features``, ``categories``) is the over-arching
    topic layer that groups code across tasks and languages.
    """

    task: str
    url: str
    description: str
    task_features: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        """Content address derived from the task title."""
        return content_hash(f"TASK\n{self.task}")

    @property
    def languages(self) -> tuple[str, ...]:
        """Languages are carried by related CodeChunk records, not the concept."""
        return ()

    def to_json(self) -> dict[str, object]:
        """Serialize the task concept to a content-addressed JSON record."""
        return {
            "id": self.id,
            "kind": "task_concept",
            "task": self.task,
            "url": self.url,
            "description": self.description,
            "task_features": list(self.task_features),
            "categories": list(self.categories),
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "TaskConcept":
        """Rebuild a task concept from a serialized JSON record."""
        return cls(
            task=str(value["task"]),
            url=str(value["url"]),
            description=str(value["description"]),
            task_features=tuple(str(item) for item in value.get("task_features", ())),
            categories=tuple(str(item) for item in value.get("categories", ())),
        )


@dataclass(frozen=True)
class CodeChunk:
    """One code block contributed by one language to one task."""

    task: str
    language: str
    code: str
    lang_block_index: int
    source_url: str
    works_with: tuple[str, ...] = ()
    section_note: str = ""

    @property
    def id(self) -> str:
        """Content address derived from the chunk's canonical code bytes."""
        return content_hash(self.code)

    def to_json(self) -> dict[str, object]:
        """Serialize the code chunk to a content-addressed JSON record."""
        return {
            "id": self.id,
            "kind": "code_chunk",
            "task": self.task,
            "language": self.language,
            "lang_block_index": self.lang_block_index,
            "code": self.code,
            "code_lines": len([ln for ln in self.code.splitlines() if ln.strip()]),
            "works_with": list(self.works_with),
            "section_note": self.section_note,
            "source_url": self.source_url,
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "CodeChunk":
        """Rebuild a code chunk from a serialized JSON record."""
        return cls(
            task=str(value["task"]),
            language=str(value["language"]),
            code=str(value["code"]),
            lang_block_index=int(value["lang_block_index"]),
            source_url=str(value["source_url"]),
            works_with=tuple(str(item) for item in value.get("works_with", ())),
            section_note=str(value.get("section_note", "")),
        )


@dataclass(frozen=True)
class LangBridge:
    """Derived edge: how many languages solve one task.

    This is the Phase-1 multilingual bridge. It is computed from CodeChunk
    records rather than stored as a fetched object, so it always reflects the
    chunks that were actually imported.
    """

    task: str
    languages: tuple[str, ...] = field(default_factory=tuple)
    chunk_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        """Content address derived from the task the bridge groups."""
        return content_hash(f"BRIDGE\n{self.task}")

    def to_json(self) -> dict[str, object]:
        """Serialize the language bridge to a content-addressed JSON record."""
        return {
            "id": self.id,
            "kind": "lang_bridge",
            "task": self.task,
            "language_count": len(set(self.languages)),
            "languages": sorted(set(self.languages)),
            "chunk_ids": list(self.chunk_ids),
        }


# --- wikitext extraction helpers (pure, no network) -------------------------

# A level-2 MediaWiki heading is exactly ``== text ==``. The negative
# assertions on ``=`` reject level-3 (``===``) and deeper headings, which a
# naive ``^==\s*(.+?)\s*==$`` would also match (treating the inner ``=`` as
# heading text).
_HEADER_RE = re.compile(r"(?m)^==(?![=])\s*(.+?)\s*==(?![=])$")
_FEATURE_RE = re.compile(r"\[\[task feature::([^\]|]+?)(?:\|[^\]]*)?\]\]")
_WORKS_RE = re.compile(r"\{\{works with\|([^}]+)\}\}")
_CAT_RE = re.compile(r"\[\[Category:([^\]|]+?)(?:\|[^\]]*)?\]\]")
_LANG_HEADER_RE = re.compile(r"\{\{header\|([^}]+)\}\}")
_CODE_RE = re.compile(
    r"<syntaxhighlight\b[^>]*?lang=\"([^\"]+)\"[^>]*?>(.*?)</syntaxhighlight>",
    re.DOTALL,
)


def split_language_sections(wikitext: str) -> list[tuple[str, str]]:
    """Split wikitext into ``(language, section_text)`` pairs.

    A language section is a ``== ... ==`` heading whose text contains a
    ``{{header|LANG}}`` marker. Anything before the first such heading is not a
    language section and is ignored here (the task description is extracted
    separately).
    """
    matches = list(_HEADER_RE.finditer(wikitext))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading = match.group(1)
        header = _LANG_HEADER_RE.search(heading)
        if not header:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(wikitext)
        language = _normalize_language(header.group(1))
        sections.append((language, wikitext[start:end]))
    return sections


def extract_task_features(wikitext: str) -> tuple[str, ...]:
    """Pull semantic ``[[task feature::...]]`` properties and shorten them."""
    found: list[str] = []
    for raw in _FEATURE_RE.findall(wikitext):
        short = raw.split(":", 1)[-1].strip()
        if short and short not in found:
            found.append(short)
    return tuple(found)


def extract_categories(wikitext: str) -> tuple[str, ...]:
    """Pull ``[[Category:...]]`` memberships."""
    found: list[str] = []
    for raw in _CAT_RE.findall(wikitext):
        if raw and raw not in found:
            found.append(raw)
    return tuple(found)


def extract_works_with(section: str) -> tuple[str, ...]:
    """Pull ``{{works with|Tool|version}}`` markers from one section."""
    found: list[str] = []
    for raw in _WORKS_RE.findall(section):
        parts = [part.strip() for part in raw.split("|") if part.strip()]
        # Regex already stripped the leading "works with|", so every part is
        # signal: parts[0] is the tool/language, the rest is version info.
        label = " ".join(parts) if parts else ""
        if not label:
            continue
        if label not in found:
            found.append(label)
    return tuple(found)


def extract_code_blocks(section: str) -> list[tuple[str, str]]:
    """Return ``(lang, code)`` for each ``<syntaxhighlight>`` block."""
    blocks: list[tuple[str, str]] = []
    for lang, code in _CODE_RE.findall(section):
        blocks.append((_normalize_language(lang), code.strip("\n")))
    return blocks


def extract_description(wikitext: str) -> str:
    """Best-effort task description: text before the first ``==`` heading.

    HTML tags and entities are removed and whitespace collapsed so the
    description is safe to index. Some MediaWiki admin asides may survive;
    removing those by content-matching is intentionally avoided to keep the
    extractor robust.
    """
    cut = re.search(r"(?m)^==", wikitext)
    head = wikitext[: cut.start()] if cut else wikitext
    # Drop leading templates like {{task}} and collapse whitespace.
    head = re.sub(r"\{\{[^}]*\}\}", " ", head)
    head = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", head)
    head = re.sub(r"'''|''", "", head)
    # Strip HTML (e.g. <sup>nd</sup>, <br>) and unescape entities.
    head = re.sub(r"<[^>]+>", " ", head)
    head = html.unescape(head)
    text = re.sub(r"\n{3,}", "\n\n", head).strip()
    return text[:1200]

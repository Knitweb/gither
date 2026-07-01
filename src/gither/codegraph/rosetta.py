"""Rosetta Code importer for the code knowledge graph.

Rosetta Code is the Phase-1 seed corpus: every task is a self-contained
functional unit solved in many languages, with semantic ``task feature``
metadata that classifies the task. That gives us:

- clean, human-crafted code (not AI output);
- a natural multilingual bridge (same task, many languages);
- over-arching topic metadata (``task feature`` / ``Category``) for grouping.

This module is deliberately stdlib-only to match the project's
``dependencies = []`` policy. Network access goes through one swappable
``http_get`` callable so the parser can be unit-tested without network.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.parse
from typing import Callable, Iterable

from .models import (
    CodeChunk,
    LangBridge,
    TaskConcept,
    extract_categories,
    extract_code_blocks,
    extract_description,
    extract_task_features,
    extract_works_with,
    split_language_sections,
)

API_BASE = "https://rosettacode.org/w/api.php"
PAGE_BASE = "https://rosettacode.org/wiki/"
ROOT_CATEGORY = "Category:Solutions_by_Programming_Task"


def curl_get(url: str, timeout: float = 30.0) -> str:
    """Fetch a URL as text via curl.

    Python's urllib on some macOS framework builds lacks CA certs; curl is
    present and verified-working on this environment, so we shell out here.
    Failures raise ``RuntimeError`` with the curl stderr for diagnostics.
    """
    result = subprocess.run(
        ["curl", "-fsSL", "--max-time", str(int(timeout)), "--retry", "2", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}) for {url}: {result.stderr.strip()}")
    return result.stdout


def list_tasks(
    limit: int | None = None,
    http_get: Callable[[str], str] = curl_get,
    pause: float = 0.0,
) -> list[str]:
    """Return canonical Rosetta task titles under the programming-task root.

    Pages the MediaWiki ``categorymembers`` API. ``cmtype=page`` skips
    sub-categories so we only get actual task articles.
    """
    titles: list[str] = []
    cont = ""
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": ROOT_CATEGORY,
            "cmlimit": "200",
            "cmtype": "page",
            "format": "json",
        }
        if cont:
            params["cmcontinue"] = cont
        url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
        payload = json.loads(http_get(url))
        for member in payload["query"]["categorymembers"]:
            titles.append(member["title"])
        if limit and len(titles) >= limit:
            return titles[:limit]
        cont = (payload.get("continue") or {}).get("cmcontinue", "")
        if not cont:
            break
        if pause:
            time.sleep(pause)
    return titles


def fetch_task_wikitext(
    title: str,
    http_get: Callable[[str], str] = curl_get,
) -> str:
    """Return the raw wikitext source of one task page."""
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "titles": title,
        "format": "json",
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    payload = json.loads(http_get(url))
    pages = payload["query"]["pages"]
    page = next(iter(pages.values()))
    return page["revisions"][0]["slots"]["main"]["*"]


def parse_task(title: str, wikitext: str) -> tuple[TaskConcept, list[CodeChunk]]:
    """Parse one task's wikitext into a concept plus its code chunks."""
    safe_title = urllib.parse.quote(title.replace(" ", "_"))
    url = f"{PAGE_BASE}{safe_title}"
    concept = TaskConcept(
        task=title,
        url=url,
        description=extract_description(wikitext),
        task_features=extract_task_features(wikitext),
        categories=extract_categories(wikitext),
    )
    chunks: list[CodeChunk] = []
    for language, section in split_language_sections(wikitext):
        works_with = extract_works_with(section)
        blocks = extract_code_blocks(section)
        if not blocks:
            continue
        for index, (_lang, code) in enumerate(blocks):
            chunks.append(
                CodeChunk(
                    task=title,
                    language=language,
                    code=code,
                    lang_block_index=index,
                    source_url=url,
                    works_with=works_with,
                    section_note="",
                )
            )
    return concept, chunks


def build_bridges(chunks: Iterable[CodeChunk]) -> list[LangBridge]:
    """Group chunks by task into multilingual bridge edges."""
    by_task: dict[str, list[CodeChunk]] = {}
    for chunk in chunks:
        by_task.setdefault(chunk.task, []).append(chunk)
    bridges: list[LangBridge] = []
    for task, group in by_task.items():
        bridges.append(
            LangBridge(
                task=task,
                languages=tuple(chunk.language for chunk in group),
                chunk_ids=tuple(chunk.id for chunk in group),
            )
        )
    return bridges


def import_tasks(
    titles: Iterable[str],
    http_get: Callable[[str], str] = curl_get,
    pause: float = 0.5,
    log: Callable[[str], None] = lambda msg: None,
) -> tuple[list[TaskConcept], list[CodeChunk]]:
    """Fetch and parse many tasks, skipping and logging failures."""
    concepts: list[TaskConcept] = []
    chunks: list[CodeChunk] = []
    for title in titles:
        try:
            wikitext = fetch_task_wikitext(title, http_get=http_get)
            if pause:
                time.sleep(pause)
        except Exception as exc:  # noqa: BLE001 - network is best-effort here
            log(f"skip {title!r}: {exc}")
            continue
        concept, task_chunks = parse_task(title, wikitext)
        concepts.append(concept)
        chunks.extend(task_chunks)
        log(f"ok   {title!r}: {len(task_chunks)} chunks / {len(set(c.language for c in task_chunks))} langs")
    return concepts, chunks


def write_jsonl(path: str, records: Iterable[object]) -> int:
    """Append-friendly JSONL writer. Returns the number of records written."""
    count = 0
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_json(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def run_import(
    limit: int = 0,
    output_dir: str = "artifacts/codegraph",
    pause: float = 0.5,
    http_get: Callable[[str], str] = curl_get,
    log: Callable[[str], None] = lambda msg: print(msg, file=sys.stderr),
) -> dict[str, object]:
    """End-to-end importer used by the CLI. Returns a small summary.

    ``limit=0`` (or a falsy value) means no cap: page until the category is
    exhausted.
    """
    import pathlib

    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    titles = list_tasks(limit=limit, http_get=http_get, pause=pause)
    log(f"listed {len(titles)} tasks (limit={limit})")
    concepts, chunks = import_tasks(titles, http_get=http_get, pause=pause, log=log)
    bridges = build_bridges(chunks)
    tasks_path = out / "tasks.jsonl"
    chunks_path = out / "chunks.jsonl"
    bridges_path = out / "bridges.jsonl"
    written_tasks = write_jsonl(str(tasks_path), concepts)
    written_chunks = write_jsonl(str(chunks_path), chunks)
    written_bridges = write_jsonl(str(bridges_path), bridges)
    summary = {
        "tasks_listed": len(titles),
        "tasks_written": written_tasks,
        "chunks_written": written_chunks,
        "bridges_written": written_bridges,
        "languages_seen": sorted({chunk.language for chunk in chunks}),
        "output_dir": str(out),
    }
    log(
        "wrote "
        f"{written_tasks} tasks, {written_chunks} chunks, {written_bridges} bridges "
        f"-> {out}"
    )
    return summary

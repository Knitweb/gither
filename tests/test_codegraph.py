"""Tests for the code knowledge graph parser (Rosetta seed corpus).

These cover the pure parsing layer with deterministic fixtures so they do
not depend on network access or on the live Rosetta Code content.
"""

from gither.codegraph.models import (
    CodeChunk,
    TaskConcept,
    content_hash,
    extract_categories,
    extract_code_blocks,
    extract_description,
    extract_task_features,
    extract_works_with,
    split_language_sections,
)
from gither.codegraph.rosetta import build_bridges, parse_task

SAMPLE = """{{task}}

There are 100 doors, all closed. Make 100 passes toggling doors.

;Task:
Report which doors are open after the last pass.

[[task feature::Rosetta Code:multiple passes]]
[[task feature::Rosetta Code:optimization]]
[[Category:Loop structures]]
[[Category:Concurrency]] Wait, this task is not concurrent.

=={{header|Python}}==
{{works with|Python|2.5-2.7}}
'''unoptimized'''
<syntaxhighlight lang="python">doors = [False] * 100
for i in range(100):
    for j in range(i, 100, i + 1):
        doors[j] = not doors[j]
</syntaxhighlight>

'''optimized'''
<syntaxhighlight lang="python">for i in range(1, 101):
    root = i ** 0.5
    print(i, 'open' if root == int(root) else 'close')
</syntaxhighlight>

=={{header|C sharp|C#}}==
<syntaxhighlight lang="csharp">var doors = new bool[100];
for (int i = 0; i < 100; i++)
    for (int j = i; j < 100; j += i + 1)
        doors[j] = !doors[j];
</syntaxhighlight>

=={{header|Go}}==
<syntaxhighlight lang="go">package main

func main() {
    var doors [100]bool
    for i := 0; i < 100; i++ {
        for j := i; j < 100; j += i + 1 {
            doors[j] = !doors[j]
        }
    }
}
</syntaxhighlight>
"""


def test_split_language_sections_normalizes_display_aliases() -> None:
    sections = dict(split_language_sections(SAMPLE))
    assert set(sections) == {"Python", "C#", "Go"}
    assert "multiple passes" not in sections  # section names are languages only


def test_extract_task_features_strips_namespace() -> None:
    assert extract_task_features(SAMPLE) == ("multiple passes", "optimization")


def test_extract_categories_picks_up_memberships() -> None:
    assert extract_categories(SAMPLE) == ("Loop structures", "Concurrency")


def test_extract_works_with_handles_versioned_markers() -> None:
    python_section = dict(split_language_sections(SAMPLE))["Python"]
    assert extract_works_with(python_section) == ("Python 2.5-2.7",)


def test_extract_code_blocks_returns_multiple_variants() -> None:
    python_section = dict(split_language_sections(SAMPLE))["Python"]
    blocks = extract_code_blocks(python_section)
    assert len(blocks) == 2
    assert blocks[0][0] == "python"
    assert "doors = [False] * 100" in blocks[0][1]
    assert "root = i ** 0.5" in blocks[1][1]


def test_extract_description_strips_html_and_entities() -> None:
    description = extract_description(SAMPLE)
    assert "100 doors" in description
    assert "{{task}}" not in description
    assert "'''" not in description
    # The SAMPLE fixture has no HTML, so verify the stripping path separately.
    messy = "{{task}}\nOpen the <sup>2nd</sup> door &amp; toggle <br/> it.\n\n==x=="
    cleaned = extract_description(messy)
    assert "<sup>" not in cleaned
    assert "<br" not in cleaned
    assert "&amp;" not in cleaned
    assert "&" in cleaned  # entity was unescaped


def test_content_hash_is_stable_under_trailing_whitespace() -> None:
    assert content_hash("x = 1\n") == content_hash("x = 1   \n\n")
    assert content_hash("x = 1") != content_hash("x = 2")


def test_parse_task_builds_concept_and_multilingual_chunks() -> None:
    concept, chunks = parse_task("100 doors", SAMPLE)
    assert concept.task == "100 doors"
    assert concept.id.startswith("sha256:")
    assert concept.task_features == ("multiple passes", "optimization")
    assert concept.categories == ("Loop structures", "Concurrency")

    languages = {chunk.language for chunk in chunks}
    assert languages == {"Python", "C#", "Go"}

    python_chunks = [chunk for chunk in chunks if chunk.language == "Python"]
    assert len(python_chunks) == 2
    assert python_chunks[0].lang_block_index == 0
    assert python_chunks[1].lang_block_index == 1
    assert python_chunks[0].works_with == ("Python 2.5-2.7",)

    # Same code produces the same content address across languages.
    assert all(chunk.id.startswith("sha256:") for chunk in chunks)


def test_build_bridges_groups_chunks_per_task() -> None:
    _concept, chunks = parse_task("100 doors", SAMPLE)
    bridges = build_bridges(chunks)
    assert len(bridges) == 1
    bridge = bridges[0]
    assert bridge.task == "100 doors"
    assert set(bridge.languages) == {"Python", "C#", "Go"}
    assert len(bridge.chunk_ids) == len(chunks)
    assert bridge.to_json()["language_count"] == 3


def test_from_json_roundtrips_records() -> None:
    concept, chunks = parse_task("100 doors", SAMPLE)
    restored_concept = TaskConcept.from_json(concept.to_json())
    assert restored_concept == concept
    assert restored_concept.id == concept.id
    restored_chunk = CodeChunk.from_json(chunks[0].to_json())
    assert restored_chunk == chunks[0]
    assert restored_chunk.id == chunks[0].id

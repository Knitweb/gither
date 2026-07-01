import json

from gither.popularity import (
    RepoRecord,
    ScriptRecord,
    bucket_star_ranges,
    dominant_language_percent,
    language_percentages,
    rank_script_entries,
)
from gither.web3fork import web3_fork_feature_json


def test_language_percentages_and_dominant_percent() -> None:
    payload = {
        "totalSize": 1000,
        "edges": [
            {"size": 700, "node": {"name": "Python"}},
            {"size": 300, "node": {"name": "Shell"}},
        ],
    }

    percentages = language_percentages(payload)

    assert percentages == {"Python": 70.0, "Shell": 30.0}
    assert dominant_language_percent(percentages, "Python") == 70.0


def test_bucket_star_ranges_splits_until_threshold() -> None:
    counts = {
        (0, 100): 1600,
        (0, 50): 800,
        (51, 100): 800,
    }

    buckets = bucket_star_ranges(100, lambda low, high: counts[(low, high)], threshold=1000)

    assert buckets == [(0, 50, 800), (51, 100, 800)]


def test_rank_script_entries_prefers_real_scripts() -> None:
    tree = [
        {"path": "README.md", "type": "blob", "size": 5000},
        {"path": "tools/sync.py", "type": "blob", "size": 2000},
        {"path": "src/main.py", "type": "blob", "size": 3000},
        {"path": "vendor/ignored.py", "type": "blob", "size": 9999},
        {"path": "scripts/run.sh", "type": "blob", "size": 800},
    ]

    ranked = rank_script_entries(tree, limit=3)

    assert [item.path for item in ranked] == [
        "tools/sync.py",
        "scripts/run.sh",
        "src/main.py",
    ]


def test_repo_record_json_includes_script_and_language_fields() -> None:
    repo = RepoRecord(
        rank=1,
        full_name="octo/example",
        node_id="node-1",
        stars=100,
        description="Example repo",
        html_url="https://github.com/octo/example",
        default_branch="main",
        dominant_language="Python",
        language_percentages={"Python": 80.0, "Shell": 20.0},
        top_scripts=[ScriptRecord(path="main.py", language="Python", size=100)],
    )

    payload = repo.to_json()

    assert payload["dominant_language_percent"] == 80.0
    assert payload["top_scripts"][0]["path"] == "main.py"


def test_web3_fork_feature_has_stitch_name_and_translations() -> None:
    payload = json.loads(web3_fork_feature_json())

    assert payload["slug"] == "chain-stitch"
    assert payload["feature_flag"] == "web3_fork"
    assert payload["translations"]["nl"] == "kettingsteek"
    assert payload["translations"]["fr"] == "point de chaînette"

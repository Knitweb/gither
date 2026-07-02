import json

from gither.enrichment import (
    PullRequestEvidence,
    load_pull_request_evidence,
    pull_request_points,
    score_contributors,
)


def test_enrichment_score_uses_merged_pr_evidence(tmp_path) -> None:
    export = {
        "pull_requests": [
            {
                "repo": "Knitweb/gither",
                "number": 12,
                "title": "Add enrichment docs",
                "user": {"login": "ada"},
                "merged_at": "2026-07-01T10:00:00Z",
                "additions": 220,
                "deletions": 40,
                "changed_files": 4,
                "reviews": [{"state": "APPROVED"}, {"state": "COMMENTED"}],
                "labels": [{"name": "gither:gate-ok"}],
                "usage_receipts": 3,
                "files": [
                    {"filename": "docs/enrichment-score.html"},
                    {"filename": "src/gither/enrichment.py"},
                    {"filename": "tests/test_enrichment.py"},
                    {"filename": "pyproject.toml"},
                ],
            },
            {
                "repo": "Knitweb/gither",
                "number": 13,
                "title": "Unmerged noise",
                "author": {"login": "bob"},
                "state": "open",
                "additions": 9000,
                "files": [{"filename": "src/generated.py"}],
            },
        ]
    }
    path = tmp_path / "prs.json"
    path.write_text(json.dumps(export), encoding="utf-8")

    scores = score_contributors(load_pull_request_evidence(path))

    assert [score.author for score in scores] == ["ada"]
    assert scores[0].score == 126
    assert scores[0].merged_prs == 1
    assert scores[0].reviewed_prs == 1
    assert scores[0].gate_passed_prs == 1
    assert scores[0].docs_prs == 1
    assert scores[0].test_prs == 1
    assert scores[0].dependency_prs == 1
    assert scores[0].usage_receipts == 3
    assert scores[0].repos == ("Knitweb/gither",)


def test_unmerged_pull_requests_do_not_score() -> None:
    pr = PullRequestEvidence(
        repo="Knitweb/gither",
        number=14,
        title="Draft",
        author="bot",
        state="open",
        additions=200,
        deletions=10,
        changed_files=2,
    )

    assert pull_request_points(pr) == 0
    assert score_contributors([pr]) == []


def test_graphql_style_review_count_and_file_names_are_normalized() -> None:
    pr = PullRequestEvidence.from_json(
        {
            "repository": "Knitweb/pulse",
            "number": 9,
            "title": "Add usage receipt tests",
            "author": {"login": "grace"},
            "state": "MERGED",
            "reviews": {"totalCount": 5},
            "checks": [{"conclusion": "success"}],
            "files": [{"path": "tests/test_receipts.py"}],
        }
    )

    assert pr.is_merged
    assert pr.review_count == 5
    assert pr.gate_passed
    assert pr.tests_touched
    assert pull_request_points(pr) == 40 + 24 + 18 + 12 + 2

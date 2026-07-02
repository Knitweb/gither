"""Contributor enrichment scoring from merged pull-request evidence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "ContributorScore",
    "PullRequestEvidence",
    "load_pull_request_evidence",
    "pull_request_points",
    "score_contributors",
]

DEPENDENCY_FILES = {
    "cargo.lock",
    "cargo.toml",
    "composer.json",
    "gemfile",
    "go.mod",
    "go.sum",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
    "yarn.lock",
}


@dataclass(frozen=True)
class PullRequestEvidence:
    """Normalized evidence for one pull request from a forge export."""

    repo: str
    number: int
    title: str
    author: str
    merged_at: str | None = None
    state: str = ""
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    review_count: int = 0
    gate_passed: bool = False
    usage_receipts: int = 0
    labels: tuple[str, ...] = ()
    files: tuple[str, ...] = ()

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "PullRequestEvidence":
        """Build normalized PR evidence from a GitHub-like JSON object."""
        files = _string_values(value.get("files"), keys=("filename", "path", "name"))
        labels = _string_values(value.get("labels"), keys=("name",))
        changed_files = _positive_int(value.get("changed_files"))
        return cls(
            repo=str(value.get("repo") or value.get("repository") or ""),
            number=_positive_int(value.get("number")),
            title=str(value.get("title") or ""),
            author=_author_login(value),
            merged_at=_optional_str(value.get("merged_at") or value.get("mergedAt")),
            state=str(value.get("state") or ""),
            additions=_positive_int(value.get("additions")),
            deletions=_positive_int(value.get("deletions")),
            changed_files=changed_files or len(files),
            review_count=_review_count(value),
            gate_passed=_gate_passed(value, labels),
            usage_receipts=_positive_int(value.get("usage_receipts")),
            labels=tuple(labels),
            files=tuple(files),
        )

    @property
    def is_merged(self) -> bool:
        """Return whether this PR is accepted into the target branch."""
        return bool(self.merged_at) or self.state.lower() == "merged"

    @property
    def docs_touched(self) -> bool:
        """Return whether the PR touched documentation."""
        return any(_is_docs_path(path) for path in self.files) or _has_label(self.labels, "docs")

    @property
    def tests_touched(self) -> bool:
        """Return whether the PR touched tests or test fixtures."""
        return any(_is_test_path(path) for path in self.files) or _has_label(self.labels, "tests")

    @property
    def dependency_touched(self) -> bool:
        """Return whether the PR touched dependency or integration surfaces."""
        return any(_is_dependency_path(path) for path in self.files) or _has_label(self.labels, "dependency")


@dataclass(frozen=True)
class ContributorScore:
    """Aggregated enrichment score for one contributor."""

    author: str
    score: int
    merged_prs: int
    reviewed_prs: int
    gate_passed_prs: int
    docs_prs: int
    test_prs: int
    dependency_prs: int
    usage_receipts: int
    repos: tuple[str, ...]
    last_merged_at: str | None

    def to_json(self) -> dict[str, object]:
        """Serialize the contributor score to JSON-compatible data."""
        return {
            "author": self.author,
            "score": self.score,
            "merged_prs": self.merged_prs,
            "reviewed_prs": self.reviewed_prs,
            "gate_passed_prs": self.gate_passed_prs,
            "docs_prs": self.docs_prs,
            "test_prs": self.test_prs,
            "dependency_prs": self.dependency_prs,
            "usage_receipts": self.usage_receipts,
            "repos": list(self.repos),
            "last_merged_at": self.last_merged_at,
        }


def load_pull_request_evidence(path: Path) -> tuple[PullRequestEvidence, ...]:
    """Load normalized PR evidence from a JSON export."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(PullRequestEvidence.from_json(item) for item in _record_items(payload))


def score_contributors(pull_requests: Iterable[PullRequestEvidence]) -> list[ContributorScore]:
    """Score contributors from merged pull-request evidence."""
    buckets: dict[str, list[PullRequestEvidence]] = {}
    for pr in pull_requests:
        if pr.is_merged and pr.author:
            buckets.setdefault(pr.author, []).append(pr)
    scores = [_score_author(author, records) for author, records in buckets.items()]
    return sorted(scores, key=lambda item: (-item.score, item.author.lower()))


def pull_request_points(pr: PullRequestEvidence) -> int:
    """Return enrichment points for one merged pull request."""
    if not pr.is_merged:
        return 0
    points = 40
    points += min(pr.review_count, 4) * 6
    points += 18 if pr.gate_passed else 0
    points += 8 if pr.docs_touched else 0
    points += 12 if pr.tests_touched else 0
    points += 14 if pr.dependency_touched else 0
    points += min(pr.usage_receipts, 12) * 4
    points += _bounded_footprint_points(pr)
    return points


def _score_author(author: str, records: list[PullRequestEvidence]) -> ContributorScore:
    repos = sorted({pr.repo for pr in records if pr.repo})
    return ContributorScore(
        author=author,
        score=sum(pull_request_points(pr) for pr in records),
        merged_prs=len(records),
        reviewed_prs=sum(1 for pr in records if pr.review_count > 0),
        gate_passed_prs=sum(1 for pr in records if pr.gate_passed),
        docs_prs=sum(1 for pr in records if pr.docs_touched),
        test_prs=sum(1 for pr in records if pr.tests_touched),
        dependency_prs=sum(1 for pr in records if pr.dependency_touched),
        usage_receipts=sum(pr.usage_receipts for pr in records),
        repos=tuple(repos),
        last_merged_at=max((pr.merged_at or "" for pr in records), default="") or None,
    )


def _record_items(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise ValueError("PR evidence JSON must be a list or object")
    for key in ("pull_requests", "pullRequests", "items", "nodes"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    raise ValueError("PR evidence JSON does not contain pull request records")


def _bounded_footprint_points(pr: PullRequestEvidence) -> int:
    changed_files = pr.changed_files or len(pr.files)
    churn = pr.additions + pr.deletions
    return min(changed_files, 6) * 2 + min(churn // 100, 6)


def _author_login(value: dict[str, Any]) -> str:
    author = value.get("author") or value.get("user")
    if isinstance(author, dict):
        return str(author.get("login") or author.get("name") or "")
    if isinstance(author, str):
        return author
    return str(value.get("author_login") or value.get("login") or "")


def _review_count(value: dict[str, Any]) -> int:
    explicit = _positive_int(value.get("review_count"))
    if explicit:
        return explicit
    reviews = value.get("reviews")
    if isinstance(reviews, list):
        return len(reviews)
    if isinstance(reviews, dict):
        return _positive_int(reviews.get("totalCount"))
    return 0


def _gate_passed(value: dict[str, Any], labels: list[str]) -> bool:
    if "gate_passed" in value:
        return bool(value["gate_passed"])
    states = _string_values(value.get("checks"), keys=("conclusion", "state", "status"))
    normalized = {item.lower() for item in states + labels}
    return bool({"success", "passed", "gate-ok", "gither:gate-ok"} & normalized)


def _string_values(value: object, *, keys: tuple[str, ...]) -> list[str]:
    if isinstance(value, list):
        return [_string_item(item, keys) for item in value if _string_item(item, keys)]
    return []


def _string_item(value: object, keys: tuple[str, ...]) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in keys:
            item = value.get(key)
            if isinstance(item, str) and item:
                return item
    return ""


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None


def _positive_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _has_label(labels: tuple[str, ...], needle: str) -> bool:
    return any(needle in label.lower() for label in labels)


def _is_docs_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("docs/") or lowered in {"readme.md", "changelog.md"}


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("tests/") or "/tests/" in lowered or "test_" in lowered


def _is_dependency_path(path: str) -> bool:
    return Path(path).name.lower() in DEPENDENCY_FILES

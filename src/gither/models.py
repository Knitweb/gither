"""Data models for Gither workspaces and routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepoSpec:
    """Repository metadata used for routing and test planning."""

    name: str
    path: str
    roles: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    test_commands: tuple[str, ...] = ()
    docs: tuple[str, ...] = ()
    remote: str | None = None
    optional: bool = False

    @classmethod
    def from_json(cls, value: dict[str, Any], base_dir: Path | None = None) -> "RepoSpec":
        """Build a repository specification from JSON data."""
        path = str(value["path"])
        if base_dir is not None and not Path(path).is_absolute():
            path = str((base_dir / path).resolve())
        return cls(
            name=str(value["name"]),
            path=path,
            roles=tuple(str(item) for item in value.get("roles", ())),
            keywords=tuple(str(item) for item in value.get("keywords", ())),
            test_commands=tuple(str(item) for item in value.get("test_commands", ())),
            docs=tuple(str(item) for item in value.get("docs", ())),
            remote=value.get("remote"),
            optional=bool(value.get("optional", False)),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialize the repository specification to JSON data."""
        value: dict[str, Any] = {
            "name": self.name,
            "path": self.path,
            "roles": list(self.roles),
            "keywords": list(self.keywords),
            "test_commands": list(self.test_commands),
            "docs": list(self.docs),
            "optional": self.optional,
        }
        if self.remote:
            value["remote"] = self.remote
        return value


@dataclass(frozen=True)
class Workspace:
    """Collection of repositories managed as one Gither workspace."""

    name: str
    repos: tuple[RepoSpec, ...] = field(default_factory=tuple)

    @classmethod
    def from_json(cls, value: dict[str, Any], base_dir: Path | None = None) -> "Workspace":
        """Build a workspace from JSON data."""
        return cls(
            name=str(value.get("workspace", "gither-workspace")),
            repos=tuple(RepoSpec.from_json(item, base_dir=base_dir) for item in value.get("repos", ())),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialize the workspace to JSON data."""
        return {"workspace": self.name, "repos": [repo.to_json() for repo in self.repos]}


@dataclass(frozen=True)
class RouteScore:
    """Routing score for one candidate repository."""

    repo: RepoSpec
    score: int
    matched_terms: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        """Serialize the route score to JSON data."""
        return {
            "repo": self.repo.name,
            "path": self.repo.path,
            "score": self.score,
            "matched_terms": list(self.matched_terms),
            "reasons": list(self.reasons),
            "test_commands": list(self.repo.test_commands),
        }

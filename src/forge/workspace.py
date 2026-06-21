from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from .models import RepoSpec, Workspace

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}


def load_workspace(path: Path) -> Workspace:
    return Workspace.from_json(json.loads(path.read_text()), base_dir=path.parent)


def save_workspace(workspace: Workspace, path: Path) -> None:
    path.write_text(json.dumps(workspace.to_json(), indent=2, sort_keys=True) + "\n")


def discover_workspace(root: Path, name: str = "knitweb") -> Workspace:
    repos = tuple(sorted(_discover_repos(root), key=lambda repo: repo.name.lower()))
    return Workspace(name=name, repos=repos)


def _discover_repos(root: Path) -> list[RepoSpec]:
    found: list[RepoSpec] = []
    for dirpath, dirnames, _filenames in os.walk(root):
        dirnames[:] = [item for item in dirnames if item not in SKIP_DIRS]
        current = Path(dirpath)
        if (current / ".git").exists():
            found.append(_repo_from_path(current))
            dirnames[:] = []
    return found


def _repo_from_path(path: Path) -> RepoSpec:
    name = path.name
    remote = _git_output(path, ["remote", "get-url", "origin"])
    roles, keywords, tests, docs = infer_repo_metadata(name)
    return RepoSpec(
        name=name,
        path=str(path),
        remote=remote or None,
        roles=roles,
        keywords=keywords,
        test_commands=tests,
        docs=docs,
    )


def _git_output(path: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=5,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def infer_repo_metadata(name: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    lower = name.lower()
    defaults = {
        "roles": ("repository",),
        "keywords": (lower,),
        "tests": ("python -m pytest -q",),
        "docs": ("README.md",),
    }
    catalogue = {
        "knitweb": {
            "roles": ("relation fabric", "content addressing", "hashgraph"),
            "keywords": ("knit", "cid", "hash", "relation", "graph", "fabric", "p2p"),
        },
        "pulse": {
            "roles": ("token", "live state", "wallet"),
            "keywords": ("pulse", "token", "wallet", "beat", "live", "pls"),
        },
        "lens": {
            "roles": ("reasoning", "query", "LRM"),
            "keywords": ("lens", "query", "reason", "lightrag", "rag", "benchmark"),
        },
        "knitweb-monitor": {
            "roles": ("activity monitor", "repository telemetry"),
            "keywords": ("monitor", "github", "activity", "repo", "telemetry", "location"),
        },
        "vbank": {
            "roles": ("governance", "time series", "VoteBank"),
            "keywords": ("vbank", "votebank", "governance", "timeseries", "time-series", "float"),
        },
        "bt": {
            "roles": ("DEX", "basket trust", "market"),
            "keywords": ("bt", "dex", "market", "basket", "trade", "pulse", "stablecoin"),
        },
        "molgang": {
            "roles": ("game", "node", "3D graph", "deployment"),
            "keywords": ("molgang", "game", "node", "server", "3d", "graph", "5mart"),
        },
        "forge": {
            "roles": ("multi-repo router", "agent workflow", "build planner"),
            "keywords": ("forge", "workflow", "agent", "router", "benchmark", "multi-repo"),
        },
    }
    selected = catalogue.get(lower, defaults)
    roles = tuple(selected.get("roles", defaults["roles"]))
    keywords = tuple(dict.fromkeys((*selected.get("keywords", defaults["keywords"]), lower)))
    tests = tuple(selected.get("tests", defaults["tests"]))
    docs = tuple(selected.get("docs", defaults["docs"]))
    return roles, keywords, tests, docs

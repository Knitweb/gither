"""Repository relation graph export for Gither workspaces."""

from __future__ import annotations

import json
from itertools import combinations

from .models import Workspace


def build_repo_graph(workspace: Workspace) -> dict[str, object]:
    """Build a simple graph from shared workspace keywords."""
    nodes = [
        {
            "id": repo.name,
            "label": repo.name,
            "path": repo.path,
            "roles": list(repo.roles),
            "keywords": list(repo.keywords),
            "optional": repo.optional,
        }
        for repo in workspace.repos
    ]
    links = []
    for left, right in combinations(workspace.repos, 2):
        overlap = sorted(set(left.keywords) & set(right.keywords))
        if not overlap:
            continue
        links.append(
            {
                "source": left.name,
                "target": right.name,
                "kind": "shared-keyword",
                "weight": len(overlap),
                "terms": overlap,
            }
        )
    return {"workspace": workspace.name, "nodes": nodes, "links": links}


def graph_json(workspace: Workspace) -> str:
    """Serialize the workspace graph as stable JSON."""
    return json.dumps(build_repo_graph(workspace), indent=2, sort_keys=True) + "\n"

from gither.graph import build_repo_graph
from gither.models import RepoSpec, Workspace


def test_graph_links_repos_with_shared_keywords() -> None:
    workspace = Workspace(
        name="test",
        repos=(
            RepoSpec(name="knitweb", path="/repo/knitweb", keywords=("graph", "cid")),
            RepoSpec(name="molgang", path="/repo/molgang", keywords=("graph", "game")),
            RepoSpec(name="bt", path="/repo/bt", keywords=("dex",)),
        ),
    )

    graph = build_repo_graph(workspace)

    assert len(graph["nodes"]) == 3
    assert graph["links"] == [
        {
            "source": "knitweb",
            "target": "molgang",
            "kind": "shared-keyword",
            "weight": 1,
            "terms": ["graph"],
        }
    ]

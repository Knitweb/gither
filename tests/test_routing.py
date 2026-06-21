from gither.models import RepoSpec, Workspace
from gither.routing import route_change


def test_route_change_prefers_lens_for_lightrag_benchmark() -> None:
    workspace = Workspace(
        name="test",
        repos=(
            RepoSpec(
                name="lens",
                path="/repo/lens",
                roles=("reasoning", "query"),
                keywords=("lens", "lightrag", "benchmark", "query"),
            ),
            RepoSpec(
                name="bt",
                path="/repo/bt",
                roles=("DEX",),
                keywords=("dex", "market", "trade"),
            ),
        ),
    )

    scores = route_change(workspace, "benchmark Lens against LightRAG query output")

    assert scores[0].repo.name == "lens"
    assert len(scores) == 1
    assert scores[0].score > 0


def test_route_change_returns_empty_for_unmatched_request() -> None:
    workspace = Workspace(name="test", repos=(RepoSpec(name="bt", path="/repo/bt"),))

    assert route_change(workspace, "unrelated words") == []

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read_doc(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_instructive_pages_exist_and_are_linked_from_home() -> None:
    home = read_doc("index.html")

    for page in (
        "getting-started.html",
        "wiki.html",
        "operator-playbook.html",
        "enrichment-score.html",
        "repository-gitbooks.html",
    ):
        assert (DOCS / page).is_file()
        assert f'./{page}' in home


def test_instructive_pages_cover_operational_gither_workflow() -> None:
    expected = {
        "getting-started.html": (
            "gither repo-snapshot --repo .",
            "gither gate --repo . --python-root src",
            "https://www.5mart.ml/gither/",
        ),
        "wiki.html": (
            "Repository snapshot",
            "Change note",
            "P2P manifest",
            "Troubleshooting",
        ),
        "operator-playbook.html": (
            "Review checklist",
            "Release checklist",
            "Mirror checklist",
            "https://knitweb.github.io/gither/",
        ),
        "enrichment-score.html": (
            "gither enrichment-score --input artifacts/merged-prs.json",
            "Only accepted work counts.",
            "https://www.5mart.ml/gither/enrichment-score.html",
        ),
        "repository-gitbooks.html": (
            "Every repository in the Knitweb workspace should have a living gitbook",
            "libp2p docs",
            "./gitbooks/gither.html",
            "https://gither.github.io/repository-gitbooks.html",
        ),
    }

    for page, snippets in expected.items():
        body = read_doc(page)
        for snippet in snippets:
            assert snippet in body


def test_public_links_are_documented_in_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "https://knitweb.github.io/gither/getting-started.html" in readme
    assert "https://www.5mart.ml/gither/getting-started.html" in readme
    assert "https://gither.github.io/enrichment-score.html" in readme
    assert "https://www.5mart.ml/gither/enrichment-score.html" in readme
    assert "https://gither.github.io/repository-gitbooks.html" in readme
    assert "https://www.5mart.ml/gither/gitbooks/" in readme


def test_repository_gitbooks_exist_for_workspace_repos() -> None:
    index = read_doc("gitbooks/index.html")
    pages = (
        "knitweb.html",
        "pulse.html",
        "lens.html",
        "knitweb-monitor.html",
        "vang.html",
        "bt.html",
        "molgang.html",
        "gither.html",
    )

    for page in pages:
        assert f"./{page}" in index
        body = read_doc(f"gitbooks/{page}")
        assert "Start" in body
        assert "Concepts" in body
        assert "Guides" in body
        assert "Reference" in body
        assert "Evidence" in body
        assert "Recovery" in body


def test_docs_pages_do_not_add_inline_script_handlers() -> None:
    for page in DOCS.rglob("*.html"):
        body = page.read_text(encoding="utf-8").lower()
        assert "<script" not in body
        assert "onclick=" not in body

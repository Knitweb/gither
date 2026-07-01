from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read_doc(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_instructive_pages_exist_and_are_linked_from_home() -> None:
    home = read_doc("index.html")

    for page in ("getting-started.html", "wiki.html", "operator-playbook.html"):
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
    }

    for page, snippets in expected.items():
        body = read_doc(page)
        for snippet in snippets:
            assert snippet in body


def test_public_links_are_documented_in_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "https://knitweb.github.io/gither/" in readme
    assert "https://www.5mart.ml/gither/" in readme
    assert "https://gither.github.io/" in readme


def test_docs_pages_do_not_add_inline_script_handlers() -> None:
    for page in DOCS.glob("*.html"):
        body = page.read_text(encoding="utf-8").lower()
        assert "<script" not in body
        assert "onclick=" not in body

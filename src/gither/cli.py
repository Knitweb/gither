"""Command line interface for the Gither code forge."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .audit import audit_python
from .benchmark import benchmark_plan
from .changebook import write_change_note
from .codegraph.analyze import analyze_python_repo
from .codegraph.query import Corpus
from .codegraph.rosetta import run_import as rosetta_run_import
from .codegraph.store import build_repo_snapshot, load_repo_snapshot, save_repo_snapshot
from .gitops import snapshot_repo
from .gossip import announce_inventory, announce_refs
from .graph import graph_json
from .identity import IdentityDoc, SignedIdentity, collect_signatures
from .popularity import popular_repo_report
from .licenses import license_protocol_json_text, license_protocol_markdown
from .peer import PeerIdentity
from .p2p import build_p2p_manifest, load_p2p_manifest, verify_p2p_manifest, write_p2p_manifest
from .review import build_review_pack, review_pack_markdown
from .routing import route_change
from .sigrefs import SignedRefs, sign_repo_refs
from .value import value_model
from .web3fork import web3_fork_feature_json, web3_fork_feature_markdown
from .workspace import discover_workspace, load_workspace, save_workspace


def main(argv: list[str] | None = None) -> int:
    """Run the Gither command line interface."""
    args = build_parser().parse_args(argv)
    handlers = {
        "discover": handle_discover,
        "route": handle_route,
        "test-plan": handle_test_plan,
        "graph": handle_graph,
        "repo-snapshot": handle_repo_snapshot,
        "python-audit": handle_python_audit,
        "change-note": handle_change_note,
        "gate": handle_gate,
        "review-pack": handle_review_pack,
        "license-protocol": handle_license_protocol,
        "popular-repos": handle_popular_repos,
        "rosetta-import": handle_rosetta_import,
        "rosetta-query": handle_rosetta_query,
        "analyze-python": handle_analyze_python,
        "value-model": handle_value_model,
        "web3-fork-feature": handle_web3_fork_feature,
        "p2p-manifest": handle_p2p_manifest,
        "p2p-verify": handle_p2p_verify,
        "benchmark-plan": handle_benchmark_plan,
        "peer": handle_peer,
        "rad-id": handle_rad_id,
        "sigrefs": handle_sigrefs,
        "announce": handle_announce,
        "explain": handle_explain,
    }
    return handlers[args.command](args)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without executing any command."""
    parser = argparse.ArgumentParser(description="Knitweb Gither codebase control plane")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_workspace_commands(subparsers)
    _add_review_commands(subparsers)
    _add_codegraph_commands(subparsers)
    _add_peer_commands(subparsers)
    _add_misc_commands(subparsers)
    subparsers.add_parser("explain", help="explain the Gither workflow")
    return parser


def _add_workspace_commands(subparsers) -> None:
    discover = subparsers.add_parser("discover", help="discover Git repositories")
    discover.add_argument("--root", default=".", help="root directory to scan")
    discover.add_argument("--name", default="knitweb", help="workspace name")
    discover.add_argument("--output", help="write workspace manifest")
    discover.add_argument("--json", action="store_true", help="print JSON")

    route = subparsers.add_parser("route", help="route a request to likely repositories")
    route.add_argument("query", nargs="+", help="plain-language request")
    route.add_argument("--workspace", default="examples/knitweb.workspace.json")
    route.add_argument("--limit", type=int, default=5)
    route.add_argument("--json", action="store_true")

    test_plan = subparsers.add_parser("test-plan", help="print cross-repo test commands")
    test_plan.add_argument("--workspace", default="examples/knitweb.workspace.json")

    graph = subparsers.add_parser("graph", help="export repository relation graph")
    graph.add_argument("--workspace", default="examples/knitweb.workspace.json")
    graph.add_argument("--output", help="write graph JSON")

    repo_snapshot = subparsers.add_parser("repo-snapshot", help="inspect Git state")
    repo_snapshot.add_argument("--repo", default=".", help="repository path")
    repo_snapshot.add_argument("--json", action="store_true")


def _add_review_commands(subparsers) -> None:
    python_audit = subparsers.add_parser("python-audit", help="audit Python code discipline")
    python_audit.add_argument("--root", default=".", help="source root")
    python_audit.add_argument("--json", action="store_true")
    python_audit.add_argument("--strict", action="store_true", help="return non-zero on issues")

    change_note = subparsers.add_parser("change-note", help="write a versioned change note")
    change_note.add_argument("--repo", default=".", help="repository path")
    change_note.add_argument("--summary", required=True)
    change_note.add_argument("--why", required=True)
    change_note.add_argument("--test", action="append", default=[])
    change_note.add_argument("--programmer-notes", default="")

    gate = subparsers.add_parser("gate", help="run local Gither review gate")
    gate.add_argument("--repo", default=".", help="repository path")
    gate.add_argument("--python-root", default="src", help="Python source root inside repo")
    gate.add_argument("--json", action="store_true")
    gate.add_argument("--strict", action="store_true", help="return non-zero on audit issues")

    review_pack = subparsers.add_parser("review-pack", help="build a portable review packet")
    review_pack.add_argument("--repo", default=".", help="repository path")
    review_pack.add_argument("--python-root", default="src", help="Python source root inside repo")
    review_pack.add_argument("--max-change-notes", type=int, default=5)
    review_pack.add_argument("--output", help="write packet to this path")
    review_pack.add_argument("--json", action="store_true")
    review_pack.add_argument("--strict", action="store_true", help="return non-zero when blocked")

    license_protocol = subparsers.add_parser("license-protocol", help="print mirror license protocol")
    license_protocol.add_argument("--json", action="store_true")


def _add_codegraph_commands(subparsers) -> None:
    popular_repos = subparsers.add_parser("popular-repos", help="scan popular repositories and build PDFs")
    popular_repos.add_argument("--output-dir", default="artifacts/popularity")
    popular_repos.add_argument("--limit", type=int, default=20000)
    popular_repos.add_argument("--summary-limit", type=int, default=100)
    popular_repos.add_argument("--min-python-share", type=float, default=50.0)
    popular_repos.add_argument("--pause-seconds", type=float, default=0.0)
    popular_repos.add_argument("--json", action="store_true")

    rosetta = subparsers.add_parser(
        "rosetta-import",
        help="import Rosetta Code tasks into the code knowledge graph",
    )
    rosetta.add_argument("--limit", type=int, default=20, help="number of tasks to import")
    rosetta.add_argument("--output-dir", default="artifacts/codegraph", help="output directory")
    rosetta.add_argument("--pause", type=float, default=0.5, help="seconds between task fetches")
    rosetta.add_argument("--json", action="store_true")

    query = subparsers.add_parser(
        "rosetta-query",
        help="query the loaded Rosetta code corpus",
    )
    query.add_argument("--dir", default="artifacts/codegraph", help="corpus directory")
    query.add_argument(
        "--action",
        choices=["stats", "languages", "chunks", "feature", "category", "search", "top", "features"],
        default="stats",
    )
    query.add_argument("--task", help="task title (for languages/chunks actions)")
    query.add_argument("--language", help="filter chunks to one language")
    query.add_argument("--feature", help="task feature to filter on")
    query.add_argument("--category", help="task category to filter on")
    query.add_argument("--query", help="free-text search over task titles/descriptions")
    query.add_argument("--limit", type=int, default=10)
    query.add_argument("--json", action="store_true")

    analyze = subparsers.add_parser(
        "analyze-python",
        help="Phase-2 tree-sitter analysis of a Python repository",
    )
    analyze.add_argument("--root", default=".", help="repository root to analyze")
    analyze.add_argument("--glob", default="**/*.py", help="file glob relative to root")
    analyze.add_argument(
        "--snapshot-file",
        help="JSON snapshot cache to read and refresh for incremental analysis",
    )
    analyze.add_argument("--json", action="store_true")


def _add_peer_commands(subparsers) -> None:
    peer = subparsers.add_parser("peer", help="show or create this node's peer identity")
    peer.add_argument("--repo", default=".", help="repository path holding .gither")
    peer.add_argument("--new", action="store_true", help="generate a fresh identity, overwriting any existing key")
    peer.add_argument("--json", action="store_true")

    rad_id = subparsers.add_parser("rad-id", help="init or show the repository identity (RID)")
    rad_id.add_argument("--repo", default=".", help="repository path holding .gither")
    rad_id.add_argument("--name", help="repository name (required to initialize)")
    rad_id.add_argument("--description", default="", help="repository description")
    rad_id.add_argument("--delegate", action="append", default=[], help="delegate DID (repeatable; defaults to this node)")
    rad_id.add_argument("--threshold", type=int, default=1, help="delegate signatures required for updates")
    rad_id.add_argument("--json", action="store_true")

    sigrefs = subparsers.add_parser("sigrefs", help="sign or verify this node's published refs")
    sigrefs.add_argument("--repo", default=".", help="repository path holding .gither")
    sigrefs.add_argument("--pattern", default="refs/heads/", help="ref pattern to publish")
    sigrefs.add_argument("--verify", action="store_true", help="verify the stored sigrefs instead of signing")
    sigrefs.add_argument("--json", action="store_true")

    announce = subparsers.add_parser("announce", help="emit the signed gossip announcements for this repo")
    announce.add_argument("--repo", default=".", help="repository path holding .gither")
    announce.add_argument("--pattern", default="refs/heads/", help="ref pattern to publish")


def _add_misc_commands(subparsers) -> None:
    subparsers.add_parser("benchmark-plan", help="print benchmark plan")
    subparsers.add_parser("value-model", help="print knowledge ownership model")

    web3_fork = subparsers.add_parser("web3-fork-feature", help="print the web3 fork feature spec")
    web3_fork.add_argument("--json", action="store_true")
    p2p_manifest = subparsers.add_parser(
        "p2p-manifest",
        help="export workspace repositories as a content-addressed p2p manifest",
    )
    p2p_manifest.add_argument("--workspace", default="examples/knitweb.workspace.json")
    p2p_manifest.add_argument("--output", help="write manifest JSON to this path")
    p2p_manifest.add_argument("--json", action="store_true")

    p2p_verify = subparsers.add_parser(
        "p2p-verify",
        help="verify a p2p repository manifest offline",
    )
    p2p_verify.add_argument("--manifest", required=True)
    p2p_verify.add_argument("--json", action="store_true")


def handle_discover(args: argparse.Namespace) -> int:
    """Discover repositories and optionally write the workspace manifest."""
    workspace = discover_workspace(Path(args.root).resolve(), name=args.name)
    if args.output:
        save_workspace(workspace, Path(args.output))
    if args.json or not args.output:
        print(json.dumps(workspace.to_json(), indent=2, sort_keys=True))
    else:
        print(f"wrote {args.output} with {len(workspace.repos)} repositories")
    return 0


def handle_route(args: argparse.Namespace) -> int:
    """Route a natural-language request to likely repositories."""
    workspace = load_workspace(Path(args.workspace))
    scores = route_change(workspace, " ".join(args.query), limit=args.limit)
    if args.json:
        print(json.dumps([score.to_json() for score in scores], indent=2, sort_keys=True))
        return 0
    if not scores:
        print("No route found. Add keywords or repo roles to the workspace manifest.")
        return 1
    for score in scores:
        print(f"{score.repo.name}: score {score.score}")
        print(f"  path: {score.repo.path}")
        print(f"  matched: {', '.join(score.matched_terms)}")
        print(f"  tests: {', '.join(score.repo.test_commands) or '(none)'}")
    return 0


def handle_test_plan(args: argparse.Namespace) -> int:
    """Print repository test commands from the workspace manifest."""
    workspace = load_workspace(Path(args.workspace))
    for repo in workspace.repos:
        print(f"{repo.name} ({repo.path})")
        if repo.optional:
            print("  optional: true")
        for command in repo.test_commands:
            print(f"  - {command}")
    return 0


def handle_graph(args: argparse.Namespace) -> int:
    """Export the workspace relation graph."""
    workspace = load_workspace(Path(args.workspace))
    output = graph_json(workspace)
    if args.output:
        Path(args.output).write_text(output)
        print(f"wrote {args.output}")
    else:
        print(output, end="")
    return 0


def handle_repo_snapshot(args: argparse.Namespace) -> int:
    """Print a repository state snapshot."""
    snapshot = snapshot_repo(Path(args.repo))
    if args.json:
        print(json.dumps(snapshot.to_json(), indent=2, sort_keys=True))
    else:
        _print_repo_snapshot(snapshot.to_json())
    return 0


def handle_python_audit(args: argparse.Namespace) -> int:
    """Audit Python source quality and optionally fail on issues."""
    audit = audit_python(Path(args.root))
    if args.json:
        print(json.dumps(audit.to_json(), indent=2, sort_keys=True))
    else:
        _print_python_audit(audit.to_json())
    return 1 if args.strict and not audit.ok else 0


def handle_change_note(args: argparse.Namespace) -> int:
    """Write a versioned Gither change note."""
    note = write_change_note(
        repo_path=Path(args.repo),
        summary=args.summary,
        why=args.why,
        tests=tuple(args.test),
        programmer_notes=args.programmer_notes,
    )
    print(f"wrote {note}")
    return 0


def handle_gate(args: argparse.Namespace) -> int:
    """Run the local repository review gate."""
    repo = Path(args.repo).resolve()
    snapshot = snapshot_repo(repo)
    python_root = repo / args.python_root
    audit = audit_python(python_root if python_root.exists() else repo)
    result = {"repo": snapshot.to_json(), "python_audit": audit.to_json(), "ok": audit.ok}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_repo_snapshot(result["repo"])
        _print_python_audit(result["python_audit"])
        print(f"gate: {'ok' if result['ok'] else 'blocked'}")
    return 1 if args.strict and not result["ok"] else 0


def handle_review_pack(args: argparse.Namespace) -> int:
    """Build a portable review packet for the current repository state."""
    pack = build_review_pack(
        Path(args.repo),
        python_root=args.python_root,
        max_change_notes=args.max_change_notes,
    )
    if args.json:
        output = json.dumps(pack.to_json(), indent=2, sort_keys=True) + "\n"
    else:
        output = review_pack_markdown(pack)
    if args.output:
        Path(args.output).write_text(output)
        print(f"wrote {args.output}")
    else:
        print(output, end="")
    return 1 if args.strict and not pack.ok else 0


def handle_benchmark_plan(_args: argparse.Namespace) -> int:
    """Print the benchmark plan."""
    print(benchmark_plan())
    return 0


def handle_license_protocol(args: argparse.Namespace) -> int:
    """Print the Gither license mirror protocol."""
    if args.json:
        print(license_protocol_json_text(), end="")
    else:
        print(license_protocol_markdown())
    return 0


def handle_popular_repos(args: argparse.Namespace) -> int:
    """Run the repository popularity scan and build local artifacts."""
    outputs = popular_repo_report(
        Path(args.output_dir),
        limit=args.limit,
        summary_limit=args.summary_limit,
        min_python_share=args.min_python_share,
        pause_seconds=args.pause_seconds,
    )
    if args.json:
        print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2, sort_keys=True))
    else:
        for key, value in outputs.items():
            print(f"{key}: {value}")
    return 0


def handle_rosetta_import(args: argparse.Namespace) -> int:
    """Import Rosetta Code tasks into the content-addressed code graph."""
    summary = rosetta_run_import(
        limit=args.limit,
        output_dir=args.output_dir,
        pause=args.pause,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for key, value in summary.items():
            if isinstance(value, list):
                print(f"{key}: {len(value)}")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")
    return 0


def handle_rosetta_query(args: argparse.Namespace) -> int:
    """Answer queries against the loaded code corpus."""
    corpus = Corpus.load(args.dir)
    if args.action == "stats":
        result = corpus.stats()
    elif args.action == "languages":
        if not args.task:
            print("--task is required for languages", file=sys.stderr)
            return 2
        result = corpus.languages_for_task(args.task)
    elif args.action == "chunks":
        if not args.task:
            print("--task is required for chunks", file=sys.stderr)
            return 2
        chunks = corpus.chunks_for_task(args.task, language=args.language)
        result = [chunk.to_json() for chunk in chunks[: args.limit]]
    elif args.action == "feature":
        if not args.feature:
            print("--feature is required for feature", file=sys.stderr)
            return 2
        result = [concept.to_json() for concept in corpus.tasks_by_feature(args.feature)]
    elif args.action == "category":
        if not args.category:
            print("--category is required for category", file=sys.stderr)
            return 2
        result = [concept.to_json() for concept in corpus.tasks_by_category(args.category)]
    elif args.action == "search":
        if not args.query:
            print("--query is required for search", file=sys.stderr)
            return 2
        result = [concept.to_json() for concept in corpus.search_tasks(args.query, limit=args.limit)]
    elif args.action == "top":
        result = corpus.top_tasks_by_language_count(limit=args.limit)
    elif args.action == "features":
        result = corpus.features_index()
    else:
        print(f"unknown action: {args.action}", file=sys.stderr)
        return 2
    if args.json or isinstance(result, (list, dict)):
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(result)
    return 0


def handle_analyze_python(args: argparse.Namespace) -> int:
    """Run Phase-2 tree-sitter analysis on a repository and print stats."""
    try:
        if args.snapshot_file:
            snapshot_path = Path(args.snapshot_file)
            previous = load_repo_snapshot(snapshot_path) if snapshot_path.exists() else None
            snapshot = build_repo_snapshot(args.root, glob=args.glob, previous=previous)
            save_repo_snapshot(snapshot, snapshot_path)
            stats = snapshot.stats()
            stats["snapshot_file"] = str(snapshot_path)
        else:
            repo = analyze_python_repo(args.root, glob=args.glob)
            stats = repo.stats()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(stats, indent=2, sort_keys=True))
    else:
        for key, value in stats.items():
            print(f"{key}: {value}")
    return 0


def handle_value_model(_args: argparse.Namespace) -> int:
    """Print the Gither knowledge ownership model."""
    print(value_model())
    return 0


def handle_peer(args: argparse.Namespace) -> int:
    """Show this node's peer identity, creating one on first use or with --new."""
    key_path = Path(args.repo).resolve() / ".gither" / "identity" / "node.key"
    created = False
    if args.new or not key_path.exists():
        identity = PeerIdentity.generate()
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(identity.seed_hex() + "\n")
        key_path.chmod(0o600)
        created = True
    else:
        identity = PeerIdentity.from_seed_hex(key_path.read_text())
    payload = {
        "did": identity.did(),
        "node_id": identity.node_id(),
        "public_key": identity.public.hex(),
        "key_path": str(key_path),
        "created": created,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"{'created' if created else 'loaded'} peer identity at {key_path}")
    print(f"did:      {payload['did']}")
    print(f"node id:  {payload['node_id']}")
    return 0


def _load_or_create_node(repo: Path) -> PeerIdentity:
    """Load this node's identity from .gither/identity/node.key, creating it if absent."""
    key_path = repo / ".gither" / "identity" / "node.key"
    if key_path.exists():
        return PeerIdentity.from_seed_hex(key_path.read_text())
    identity = PeerIdentity.generate()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(identity.seed_hex() + "\n")
    key_path.chmod(0o600)
    return identity


def handle_rad_id(args: argparse.Namespace) -> int:
    """Initialize the repository identity (with --name) or show the existing one."""
    repo = Path(args.repo).resolve()
    rad_path = repo / ".gither" / "identity" / "rad.json"
    node = _load_or_create_node(repo)
    if args.name:
        delegates = tuple(args.delegate) or (node.did(),)
        doc = IdentityDoc(args.name, args.description, delegates, args.threshold)
        signers = (node,) if node.did() in delegates else ()
        signed = collect_signatures(doc, signers)
        rad_path.write_text(json.dumps(signed.to_json(), indent=2, sort_keys=True) + "\n")
    elif rad_path.exists():
        signed = SignedIdentity.from_json(json.loads(rad_path.read_text()))
    else:
        print("no repository identity yet; initialize with: gither rad-id --name <name>")
        return 1
    payload = {
        "rid": signed.doc.rid(),
        "name": signed.doc.name,
        "delegates": list(signed.doc.delegates),
        "threshold": signed.doc.threshold,
        "valid_signatures": signed.valid_signature_count(),
        "verified": signed.is_verified(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"rid:       {payload['rid']}")
    print(f"name:      {payload['name']}")
    print(f"delegates: {payload['threshold']}-of-{len(payload['delegates'])} threshold")
    print(f"verified:  {payload['verified']} ({payload['valid_signatures']} valid signature(s))")
    return 0 if payload["verified"] else 1


def handle_sigrefs(args: argparse.Namespace) -> int:
    """Sign this node's published refs, or verify the stored signed-ref set."""
    repo = Path(args.repo).resolve()
    sigrefs_path = repo / ".gither" / "identity" / "sigrefs.json"
    if args.verify:
        if not sigrefs_path.exists():
            print("no sigrefs yet; publish with: gither sigrefs")
            return 1
        signed = SignedRefs.from_json(json.loads(sigrefs_path.read_text()))
    else:
        node = _load_or_create_node(repo)
        signed = sign_repo_refs(repo, node, args.pattern)
        sigrefs_path.write_text(json.dumps(signed.to_json(), indent=2, sort_keys=True) + "\n")
    payload = {
        "node_id": signed.node_id,
        "ref_count": len(signed.refs),
        "refs": signed.as_dict(),
        "verified": signed.is_verified(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"node id:  {signed.node_id}")
    print(f"refs:     {payload['ref_count']} published")
    for name, oid in signed.refs:
        print(f"  {name} {oid[:12]}")
    print(f"verified: {payload['verified']}")
    return 0 if payload["verified"] else 1


def handle_announce(args: argparse.Namespace) -> int:
    """Emit the signed gossip announcements (inventory + refs) a peer would broadcast."""
    repo = Path(args.repo).resolve()
    rad_path = repo / ".gither" / "identity" / "rad.json"
    if not rad_path.exists():
        print("no repository identity yet; initialize with: gither rad-id --name <name>")
        return 1
    rid = SignedIdentity.from_json(json.loads(rad_path.read_text())).doc.rid()
    node = _load_or_create_node(repo)
    signed = sign_repo_refs(repo, node, args.pattern)
    timestamp = int(time.time())
    refs_ann = announce_refs(signed, rid, node, timestamp)
    inv_ann = announce_inventory((rid,), node, timestamp)
    print(json.dumps({"refs": refs_ann.to_json(), "inventory": inv_ann.to_json()}, indent=2, sort_keys=True))
    return 0


def handle_web3_fork_feature(args: argparse.Namespace) -> int:
    """Print the named Web3 fork feature spec."""
    if args.json:
        print(web3_fork_feature_json(), end="")
    else:
        print(web3_fork_feature_markdown())
    return 0


def handle_p2p_manifest(args: argparse.Namespace) -> int:
    """Export a content-addressed p2p repository manifest."""
    workspace = load_workspace(Path(args.workspace))
    manifest = build_p2p_manifest(workspace)
    if args.output:
        write_p2p_manifest(Path(args.output), manifest)
    if args.json or not args.output:
        print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        available = sum(1 for record in manifest["records"] if record["state"]["available"])
        print(
            f"wrote {args.output}: {manifest['count']} repos, "
            f"{available} available, id {manifest['manifestId']}"
        )
    return 0


def handle_p2p_verify(args: argparse.Namespace) -> int:
    """Verify a content-addressed p2p repository manifest."""
    report = verify_p2p_manifest(load_p2p_manifest(Path(args.manifest)))
    if args.json:
        print(json.dumps(report.to_json(), indent=2, sort_keys=True))
    else:
        print(f"manifest: {report.manifest_id or '(missing)'}")
        print(f"records: {report.record_count}")
        print(f"verify: {'ok' if report.ok else 'FAILED'}")
        for error in report.errors:
            print(f"  - {error}")
    return 0 if report.ok else 1


def handle_explain(_args: argparse.Namespace) -> int:
    """Print the Gither workflow explanation."""
    print(EXPLAIN_TEXT)
    return 0


def _print_repo_snapshot(value: dict[str, object]) -> None:
    print(f"repo: {value['name']}")
    print(f"path: {value['path']}")
    print(f"branch: {value['branch']}")
    print(f"head: {str(value['head'])[:12]}")
    print(f"dirty: {value['dirty']}")
    changed = value.get("changed_files", [])
    if changed:
        print("changed files:")
        for item in changed:
            print(f"  - {item}")


def _print_python_audit(value: dict[str, object]) -> None:
    print(f"python root: {value['root']}")
    print(f"files checked: {value['files_checked']}")
    print(f"python audit: {'ok' if value['ok'] else 'issues'}")
    for error in value["syntax_errors"]:
        print(f"  syntax: {error}")
    for symbol in value["symbols"]:
        if symbol["ok"]:
            continue
        missing = ", ".join(symbol["missing_annotations"]) or "none"
        print(
            f"  {symbol['file']}:{symbol['line']} {symbol['kind']} {symbol['name']} "
            f"docstring={symbol['has_docstring']} missing_annotations={missing} "
            f"body_lines={symbol['body_lines']}"
        )


EXPLAIN_TEXT = """Gither workflow:

1. Own the codebase in Gither, not in GitHub or GitLab.
2. Discover or maintain a workspace manifest.
3. Route a user request to the most likely repository.
4. Inspect the repository state before editing.
5. Make the smallest coherent code change.
6. Write a versioned change note with background and tests.
7. Run repo-local tests and the Gither gate.
8. Attach accepted code to Knitweb dependency records and Pulse usage receipts.
9. Mirror outward only after Gither accepts the change.

Git remains a low-level object store and transport for now.
GitHub and GitLab are optional mirrors, not the source of authority.
Gither rewards actual software usage, not commit volume.
"""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

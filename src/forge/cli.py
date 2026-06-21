from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .benchmark import benchmark_plan
from .graph import graph_json
from .routing import route_change
from .workspace import discover_workspace, load_workspace, save_workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Knitweb Forge multi-repo navigator")
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    subparsers.add_parser("benchmark-plan", help="print benchmark plan")
    subparsers.add_parser("explain", help="explain the Forge workflow")

    args = parser.parse_args(argv)

    if args.command == "discover":
        workspace = discover_workspace(Path(args.root).resolve(), name=args.name)
        if args.output:
            save_workspace(workspace, Path(args.output))
        if args.json or not args.output:
            print(json.dumps(workspace.to_json(), indent=2, sort_keys=True))
        else:
            print(f"wrote {args.output} with {len(workspace.repos)} repositories")
        return 0

    if args.command == "route":
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

    if args.command == "test-plan":
        workspace = load_workspace(Path(args.workspace))
        for repo in workspace.repos:
            print(f"{repo.name} ({repo.path})")
            if repo.optional:
                print("  optional: true")
            for command in repo.test_commands:
                print(f"  - {command}")
        return 0

    if args.command == "graph":
        workspace = load_workspace(Path(args.workspace))
        output = graph_json(workspace)
        if args.output:
            Path(args.output).write_text(output)
            print(f"wrote {args.output}")
        else:
            print(output, end="")
        return 0

    if args.command == "benchmark-plan":
        print(benchmark_plan())
        return 0

    if args.command == "explain":
        print(EXPLAIN_TEXT)
        return 0

    return 2


EXPLAIN_TEXT = """Forge workflow:

1. Discover or maintain a workspace manifest.
2. Route a user request to the most likely repository.
3. Read that repo's docs and local conventions.
4. Make the smallest coherent change in that repo.
5. Run the repo-level tests.
6. Run the cross-repo test plan when contracts changed.
7. Export graph metadata so Lens and Monitor can reason over the portfolio.

The agent should not keep nine projects in its head.
Forge gives it a deterministic map first.
"""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

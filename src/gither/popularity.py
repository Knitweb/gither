"""GitHub popularity scan and PDF reporting for Gither research."""

from __future__ import annotations

from dataclasses import dataclass, field
import csv
import json
from pathlib import Path
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

__all__ = [
    "RepoRecord",
    "ScriptRecord",
    "GitHubPopularityClient",
    "bucket_star_ranges",
    "dominant_language_percent",
    "language_percentages",
    "popular_repo_report",
    "rank_script_entries",
]

SCRIPT_LANGUAGES = {
    ".py": "Python",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".sql": "SQL",
    ".scala": "Scala",
    ".r": "R",
    ".rb": "Ruby",
    ".php": "PHP",
    ".pl": "Perl",
    ".lua": "Lua",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".zig": "Zig",
}

EXCLUDED_PATH_PARTS = {
    ".git",
    ".github",
    ".claude",
    "__pycache__",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    ".venv",
}

PREFERRED_SCRIPT_DIRS = ("tools/", "scripts/", "bin/", "src/", "app/", "examples/")


@dataclass(frozen=True)
class ScriptRecord:
    """One ranked script-like file inside a repository tree."""

    path: str
    language: str
    size: int

    def to_json(self) -> dict[str, object]:
        return {"path": self.path, "language": self.language, "size": self.size}


@dataclass
class RepoRecord:
    """Popularity and enrichment record for one repository."""

    rank: int
    full_name: str
    node_id: str
    stars: int
    description: str
    html_url: str
    default_branch: str
    dominant_language: str | None
    language_percentages: dict[str, float] = field(default_factory=dict)
    top_scripts: list[ScriptRecord] = field(default_factory=list)

    @property
    def dominant_language_percent(self) -> float:
        return dominant_language_percent(self.language_percentages, self.dominant_language)

    def to_json(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "full_name": self.full_name,
            "node_id": self.node_id,
            "stars": self.stars,
            "description": self.description,
            "html_url": self.html_url,
            "default_branch": self.default_branch,
            "dominant_language": self.dominant_language,
            "dominant_language_percent": self.dominant_language_percent,
            "language_percentages": self.language_percentages,
            "top_scripts": [record.to_json() for record in self.top_scripts],
        }


class GitHubPopularityClient:
    """Authenticated GitHub client for popularity and language analysis."""

    def __init__(self, token: str | None = None, pause_seconds: float = 0.0) -> None:
        self._token = token or _gh_auth_token()
        self._pause_seconds = pause_seconds

    def max_stars(self) -> int:
        """Return the current star count of the most-starred public repository."""
        response = self.rest_json(
            "search/repositories",
            {
                "q": "stars:>1",
                "sort": "stars",
                "order": "desc",
                "per_page": 1,
                "page": 1,
            },
        )
        items = response.get("items", [])
        if not isinstance(items, list) or not items:
            raise ValueError("GitHub search returned no repositories")
        top = items[0]
        if not isinstance(top, dict):
            raise ValueError("GitHub search item is not a mapping")
        return int(top["stargazers_count"])

    def search_count(self, low: int, high: int) -> int:
        """Return GitHub search total_count for a star bucket."""
        response = self.rest_json(
            "search/repositories",
            {
                "q": f"stars:{low}..{high}",
                "sort": "stars",
                "order": "desc",
                "per_page": 1,
                "page": 1,
            },
        )
        return int(response["total_count"])

    def fetch_bucket(self, low: int, high: int) -> list[dict[str, object]]:
        """Fetch all repositories inside a <=1000-result star bucket."""
        results: list[dict[str, object]] = []
        for page in range(1, 11):
            response = self.rest_json(
                "search/repositories",
                {
                    "q": f"stars:{low}..{high}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 100,
                    "page": page,
                },
            )
            items = response.get("items", [])
            if not isinstance(items, list) or not items:
                break
            for item in items:
                if isinstance(item, dict):
                    results.append(item)
            if len(items) < 100:
                break
        return results

    def batch_language_percentages(
        self,
        node_ids: list[str],
    ) -> dict[str, tuple[str | None, dict[str, float]]]:
        """Return dominant language and percentages keyed by repository node_id."""
        query = """
        query($ids: [ID!]!) {
          nodes(ids: $ids) {
            ... on Repository {
              id
              nameWithOwner
              languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
                totalCount
                totalSize
                edges {
                  size
                  node { name }
                }
              }
            }
          }
        }
        """
        payload = self.graphql_json(query, {"ids": node_ids})
        nodes = payload.get("data", {}).get("nodes", [])
        if not isinstance(nodes, list):
            return {}
        result: dict[str, tuple[str | None, dict[str, float]]] = {}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str):
                continue
            language_info = node.get("languages", {})
            if not isinstance(language_info, dict):
                result[node_id] = (None, {})
                continue
            percentages = language_percentages(language_info)
            dominant = next(iter(percentages), None)
            result[node_id] = (dominant, percentages)
        return result

    def repository_tree(self, full_name: str, default_branch: str) -> list[dict[str, object]]:
        """Return the recursive Git tree for one repository branch."""
        response = self.rest_json(
            f"repos/{full_name}/git/trees/{default_branch}",
            {"recursive": 1},
        )
        tree = response.get("tree", [])
        if not isinstance(tree, list):
            return []
        return [item for item in tree if isinstance(item, dict)]

    def rest_json(self, path: str, params: dict[str, object] | None = None) -> dict[str, object]:
        """GET one GitHub REST endpoint and decode JSON."""
        query = f"?{urlencode(params)}" if params else ""
        url = f"https://api.github.com/{path}{query}"
        return self._request_json(url, method="GET")

    def graphql_json(
        self,
        query: str,
        variables: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """POST one GitHub GraphQL query and decode JSON."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        return self._request_json(
            "https://api.github.com/graphql",
            method="POST",
            payload=payload,
        )

    def _request_json(
        self,
        url: str,
        *,
        method: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, method=method)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", f"Bearer {self._token}")
        request.add_header("User-Agent", "GitherPopularity/1.0")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        for attempt in range(3):
            try:
                with urlopen(request) as response:
                    raw = response.read().decode("utf-8")
                    self._pause()
                    return json.loads(raw)
            except HTTPError as exc:
                if exc.code in {403, 429} and attempt < 2:
                    time.sleep(2.0 + attempt)
                    continue
                raise
            except URLError:
                if attempt < 2:
                    time.sleep(1.0 + attempt)
                    continue
                raise
        raise RuntimeError(f"request failed: {url}")

    def _pause(self) -> None:
        if self._pause_seconds > 0:
            time.sleep(self._pause_seconds)


def popular_repo_report(
    output_dir: Path,
    *,
    limit: int = 20_000,
    summary_limit: int = 100,
    min_python_share: float = 50.0,
    pause_seconds: float = 0.0,
) -> dict[str, Path]:
    """Collect popularity data, enrich it, and build the requested artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    client = GitHubPopularityClient(pause_seconds=pause_seconds)

    cache_path = output_dir / "top_repositories.json"
    repos = collect_top_repositories(client, limit=limit, cache_path=cache_path)

    enrich_language_percentages(client, repos, cache_path=output_dir / "language_enriched.json")
    enrich_top_scripts(
        client,
        repos[:summary_limit],
        cache_path=output_dir / "top100_scripts.json",
    )

    json_path = output_dir / "top20000_repositories.json"
    csv_path = output_dir / "top20000_repositories.csv"
    top100_pdf = output_dir / "top100_repositories.pdf"
    python_pdf = output_dir / "python_majority_repositories.pdf"

    write_json_report(repos, json_path)
    write_csv_report(repos, csv_path)
    write_top100_pdf(repos[:summary_limit], top100_pdf)
    write_python_pdf(repos, python_pdf, min_python_share=min_python_share)
    return {
        "json": json_path,
        "csv": csv_path,
        "top100_pdf": top100_pdf,
        "python_pdf": python_pdf,
    }


def collect_top_repositories(
    client: GitHubPopularityClient,
    *,
    limit: int,
    cache_path: Path | None = None,
) -> list[RepoRecord]:
    """Collect the top ``limit`` public repositories by stars."""
    if cache_path and cache_path.exists():
        return _load_repo_records(cache_path)

    max_stars = client.max_stars()
    buckets = bucket_star_ranges(max_stars, client.search_count)
    repos: list[RepoRecord] = []
    seen: set[str] = set()

    for low, high, _count in sorted(buckets, key=lambda item: item[1], reverse=True):
        for item in client.fetch_bucket(low, high):
            full_name = str(item["full_name"])
            if full_name in seen:
                continue
            seen.add(full_name)
            repos.append(
                RepoRecord(
                    rank=0,
                    full_name=full_name,
                    node_id=str(item["node_id"]),
                    stars=int(item["stargazers_count"]),
                    description=str(item.get("description") or ""),
                    html_url=str(item["html_url"]),
                    default_branch=str(item.get("default_branch") or "main"),
                    dominant_language=str(item.get("language") or "") or None,
                )
            )
            if len(repos) >= limit:
                break
        if len(repos) >= limit:
            break

    repos.sort(key=lambda repo: (-repo.stars, repo.full_name.lower()))
    for index, repo in enumerate(repos, start=1):
        repo.rank = index
    if cache_path:
        write_json_report(repos, cache_path)
    return repos


def enrich_language_percentages(
    client: GitHubPopularityClient,
    repos: list[RepoRecord],
    *,
    cache_path: Path | None = None,
    batch_size: int = 100,
) -> None:
    """Populate language percentage fields for every repo."""
    cached = _load_enrichment_cache(cache_path)
    missing = [repo for repo in repos if repo.node_id not in cached]

    for repo in repos:
        if repo.node_id in cached:
            dominant, percentages = cached[repo.node_id]
            repo.dominant_language = dominant
            repo.language_percentages = percentages

    for offset in range(0, len(missing), batch_size):
        batch = missing[offset : offset + batch_size]
        data = client.batch_language_percentages([repo.node_id for repo in batch])
        for repo in batch:
            dominant, percentages = data.get(repo.node_id, (repo.dominant_language, {}))
            repo.dominant_language = dominant
            repo.language_percentages = percentages
            cached[repo.node_id] = (dominant, percentages)
        if cache_path:
            _write_enrichment_cache(cache_path, cached)


def enrich_top_scripts(
    client: GitHubPopularityClient,
    repos: list[RepoRecord],
    *,
    cache_path: Path | None = None,
) -> None:
    """Populate top-script heuristics for the selected repositories."""
    cached: dict[str, list[dict[str, object]]] = {}
    if cache_path and cache_path.exists():
        cached = json.loads(cache_path.read_text())

    for repo in repos:
        if repo.full_name in cached:
            repo.top_scripts = [
                ScriptRecord(
                    path=str(item["path"]),
                    language=str(item["language"]),
                    size=int(item["size"]),
                )
                for item in cached[repo.full_name]
            ]
            continue
        tree = client.repository_tree(repo.full_name, repo.default_branch)
        repo.top_scripts = rank_script_entries(tree)
        cached[repo.full_name] = [item.to_json() for item in repo.top_scripts]
        if cache_path:
            cache_path.write_text(json.dumps(cached, indent=2, sort_keys=True) + "\n")


def bucket_star_ranges(
    max_stars: int,
    count_fn,
    *,
    threshold: int = 1000,
) -> list[tuple[int, int, int]]:
    """Split the star space into GitHub-search-compatible buckets."""
    return _split_star_range(0, max_stars, count_fn, threshold)


def dominant_language_percent(
    percentages: dict[str, float],
    language: str | None,
) -> float:
    """Return the dominant-language percentage if available."""
    if language is None:
        return 0.0
    return float(percentages.get(language, 0.0))


def language_percentages(language_info: dict[str, object]) -> dict[str, float]:
    """Convert GitHub GraphQL language sizes into percentages."""
    total_size = int(language_info.get("totalSize") or 0)
    total_count = int(language_info.get("totalCount") or 0)
    edges = language_info.get("edges", [])
    if total_size <= 0 or not isinstance(edges, list):
        return {}
    percentages: dict[str, float] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        node = edge.get("node", {})
        if not isinstance(node, dict):
            continue
        name = node.get("name")
        size = edge.get("size")
        if not isinstance(name, str) or not isinstance(size, int):
            continue
        percentages[name] = round(size * 100.0 / total_size, 2)
    if total_count > len(percentages):
        remainder = round(max(0.0, 100.0 - sum(percentages.values())), 2)
        if remainder > 0:
            percentages["Other"] = remainder
    return dict(sorted(percentages.items(), key=lambda item: (-item[1], item[0].lower())))


def rank_script_entries(
    tree: list[dict[str, object]],
    *,
    limit: int = 10,
) -> list[ScriptRecord]:
    """Rank script-like files from a recursive Git tree."""
    candidates: list[tuple[tuple[int, int, int, str], ScriptRecord]] = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item.get("path")
        size = item.get("size")
        if not isinstance(path, str) or not isinstance(size, int):
            continue
        if any(part in EXCLUDED_PATH_PARTS for part in path.split("/")):
            continue
        suffix = Path(path).suffix.lower()
        language = SCRIPT_LANGUAGES.get(suffix)
        if language is None:
            continue
        depth = path.count("/")
        dir_rank = _script_dir_rank(path)
        script = ScriptRecord(path=path, language=language, size=size)
        score = (dir_rank, depth, -size, path.lower())
        candidates.append((score, script))
    candidates.sort(key=lambda item: item[0])
    return [item[1] for item in candidates[:limit]]


def write_json_report(repos: list[RepoRecord], path: Path) -> None:
    """Write repo records as formatted JSON."""
    payload = [repo.to_json() for repo in repos]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv_report(repos: list[RepoRecord], path: Path) -> None:
    """Write repo records as CSV."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rank",
                "full_name",
                "stars",
                "dominant_language",
                "dominant_language_percent",
                "description",
                "html_url",
                "default_branch",
                "language_percentages_json",
            ],
        )
        writer.writeheader()
        for repo in repos:
            writer.writerow(
                {
                    "rank": repo.rank,
                    "full_name": repo.full_name,
                    "stars": repo.stars,
                    "dominant_language": repo.dominant_language or "",
                    "dominant_language_percent": f"{repo.dominant_language_percent:.2f}",
                    "description": repo.description,
                    "html_url": repo.html_url,
                    "default_branch": repo.default_branch,
                    "language_percentages_json": json.dumps(
                        repo.language_percentages,
                        sort_keys=True,
                    ),
                }
            )


def write_top100_pdf(repos: list[RepoRecord], path: Path) -> None:
    """Write the top-100 summary PDF."""
    reportlab = _load_reportlab()
    colors = reportlab["colors"]
    A4 = reportlab["A4"]
    mm = reportlab["mm"]
    Paragraph = reportlab["Paragraph"]
    SimpleDocTemplate = reportlab["SimpleDocTemplate"]
    Spacer = reportlab["Spacer"]
    Table = reportlab["Table"]
    TableStyle = reportlab["TableStyle"]
    styles = _pdf_styles()
    story: list[object] = [
        Paragraph("Top 100 Popular GitHub Repositories", styles["title"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "Summary, dominant language percentages, and top script heuristics.",
            styles["body"],
        ),
        Spacer(1, 6 * mm),
    ]
    for repo in repos:
        story.append(
            Paragraph(
                f"{repo.rank}. {repo.full_name} -- {repo.stars} stars",
                styles["heading"],
            )
        )
        dominant = repo.dominant_language or "Unknown"
        story.append(
            Paragraph(
                f"Does: {repo.description or 'No GitHub description.'}",
                styles["body"],
            )
        )
        story.append(
            Paragraph(
                f"Dominant language: {dominant} ({repo.dominant_language_percent:.2f}%)",
                styles["body"],
            )
        )
        story.append(
            Paragraph(
                f"Top language mix: {_language_mix_text(repo.language_percentages, 5)}",
                styles["body"],
            )
        )
        script_rows = [["path", "language", "bytes"]]
        for script in repo.top_scripts[:10]:
            script_rows.append(
                [
                    Paragraph(script.path, styles["table"]),
                    Paragraph(script.language, styles["table"]),
                    Paragraph(str(script.size), styles["table"]),
                ]
            )
        if len(script_rows) == 1:
            script_rows.append([Paragraph("(no ranked script files)", styles["table"]), "", ""])
        table = Table(script_rows, colWidths=[105 * mm, 35 * mm, 18 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d8e8f2")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#8aa8b8")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 5 * mm))
    _build_pdf(path, story)


def write_python_pdf(
    repos: list[RepoRecord],
    path: Path,
    *,
    min_python_share: float,
) -> None:
    """Write the Python-majority repository list PDF."""
    reportlab = _load_reportlab()
    colors = reportlab["colors"]
    mm = reportlab["mm"]
    Paragraph = reportlab["Paragraph"]
    Spacer = reportlab["Spacer"]
    Table = reportlab["Table"]
    TableStyle = reportlab["TableStyle"]
    styles = _pdf_styles()
    filtered = [
        repo
        for repo in repos
        if repo.dominant_language == "Python" and repo.dominant_language_percent > min_python_share
    ]
    story: list[object] = [
        Paragraph("Python-Majority Popular Repositories", styles["title"]),
        Spacer(1, 4 * mm),
        Paragraph(
            f"Repositories where Python accounts for more than {min_python_share:.0f}% of the detected code bytes.",
            styles["body"],
        ),
        Spacer(1, 6 * mm),
    ]
    rows = [["rank", "repo", "stars", "python %", "does"]]
    for repo in filtered:
        rows.append(
            [
                Paragraph(str(repo.rank), styles["table"]),
                Paragraph(repo.full_name, styles["table"]),
                Paragraph(str(repo.stars), styles["table"]),
                Paragraph(f"{repo.dominant_language_percent:.2f}", styles["table"]),
                Paragraph(repo.description or "No GitHub description.", styles["table"]),
            ]
        )
    if len(rows) == 1:
        rows.append(["", Paragraph("(no matching repositories)", styles["table"]), "", "", ""])
    table = Table(rows, colWidths=[12 * mm, 55 * mm, 20 * mm, 18 * mm, 80 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d8e8f2")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#8aa8b8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    _build_pdf(path, story)


def _split_star_range(
    low: int,
    high: int,
    count_fn,
    threshold: int,
) -> list[tuple[int, int, int]]:
    if low > high:
        return []
    count = count_fn(low, high)
    if count == 0:
        return []
    if count <= threshold or low == high:
        return [(low, high, count)]
    mid = (low + high) // 2
    if mid >= high:
        mid = high - 1
    return _split_star_range(low, mid, count_fn, threshold) + _split_star_range(
        mid + 1,
        high,
        count_fn,
        threshold,
    )


def _gh_auth_token() -> str:
    result = subprocess.run(
        ["gh", "auth", "token"],
        check=True,
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    if not token:
        raise ValueError("gh auth token returned an empty token")
    return token


def _load_repo_records(path: Path) -> list[RepoRecord]:
    payload = json.loads(path.read_text())
    return [_repo_from_json(item) for item in payload]


def _load_enrichment_cache(
    path: Path | None,
) -> dict[str, tuple[str | None, dict[str, float]]]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text())
    return {
        str(node_id): (
            value[0],
            {str(name): float(percent) for name, percent in value[1].items()},
        )
        for node_id, value in payload.items()
    }


def _write_enrichment_cache(
    path: Path,
    cache: dict[str, tuple[str | None, dict[str, float]]],
) -> None:
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")


def _repo_from_json(value: dict[str, object]) -> RepoRecord:
    scripts = [
        ScriptRecord(
            path=str(item["path"]),
            language=str(item["language"]),
            size=int(item["size"]),
        )
        for item in value.get("top_scripts", [])
        if isinstance(item, dict)
    ]
    percentages = {
        str(name): float(percent)
        for name, percent in value.get("language_percentages", {}).items()
    }
    return RepoRecord(
        rank=int(value["rank"]),
        full_name=str(value["full_name"]),
        node_id=str(value["node_id"]),
        stars=int(value["stars"]),
        description=str(value.get("description") or ""),
        html_url=str(value["html_url"]),
        default_branch=str(value["default_branch"]),
        dominant_language=str(value.get("dominant_language") or "") or None,
        language_percentages=percentages,
        top_scripts=scripts,
    )


def _language_mix_text(percentages: dict[str, float], limit: int) -> str:
    items = list(percentages.items())[:limit]
    if not items:
        return "unknown"
    return ", ".join(f"{name} {percent:.2f}%" for name, percent in items)


def _pdf_styles() -> dict[str, ParagraphStyle]:
    reportlab = _load_reportlab()
    styles = reportlab["getSampleStyleSheet"]()
    table = styles["BodyText"].clone("TableBody")
    table.fontSize = 8
    table.leading = 10
    table.splitLongWords = 1
    return {
        "title": styles["Title"],
        "heading": styles["Heading3"],
        "body": styles["BodyText"],
        "table": table,
    }


def _build_pdf(path: Path, story: list[object]) -> None:
    reportlab = _load_reportlab()
    A4 = reportlab["A4"]
    mm = reportlab["mm"]
    SimpleDocTemplate = reportlab["SimpleDocTemplate"]
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    doc.build(story)


def _load_reportlab() -> dict[str, object]:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ModuleNotFoundError as exc:
        raise RuntimeError("reportlab is required to generate PDFs") from exc
    return {
        "colors": colors,
        "A4": A4,
        "getSampleStyleSheet": getSampleStyleSheet,
        "mm": mm,
        "Paragraph": Paragraph,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
    }


def _script_dir_rank(path: str) -> int:
    for index, prefix in enumerate(PREFERRED_SCRIPT_DIRS):
        if path.startswith(prefix):
            return index
    return len(PREFERRED_SCRIPT_DIRS)

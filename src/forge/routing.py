from __future__ import annotations

import re

from .models import RepoSpec, RouteScore, Workspace

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:/-]*", re.IGNORECASE)


def route_change(workspace: Workspace, query: str, limit: int = 5) -> list[RouteScore]:
    tokens = set(token.lower() for token in TOKEN_RE.findall(query))
    scores = [_score_repo(repo, tokens, query.lower()) for repo in workspace.repos]
    return [score for score in sorted(scores, key=lambda item: (-item.score, item.repo.name))[:limit] if score.score > 0]


def _score_repo(repo: RepoSpec, tokens: set[str], lowered_query: str) -> RouteScore:
    score = 0
    matched: list[str] = []
    reasons: list[str] = []

    repo_name = repo.name.lower()
    if repo_name in lowered_query:
        score += 8
        matched.append(repo.name)
        reasons.append("repo name appears in request")

    for keyword in repo.keywords:
        term = keyword.lower()
        if term in tokens or term in lowered_query:
            score += 4
            matched.append(keyword)
            reasons.append(f"keyword match: {keyword}")

    for role in repo.roles:
        role_tokens = set(TOKEN_RE.findall(role.lower()))
        overlap = sorted(role_tokens & tokens)
        if overlap:
            score += 2 * len(overlap)
            matched.extend(overlap)
            reasons.append(f"role overlap: {role}")

    for doc in repo.docs:
        doc_name = doc.lower()
        if doc_name in lowered_query:
            score += 3
            matched.append(doc)
            reasons.append(f"doc reference: {doc}")

    return RouteScore(
        repo=repo,
        score=score,
        matched_terms=tuple(dict.fromkeys(matched)),
        reasons=tuple(dict.fromkeys(reasons)),
    )

"""Feature spec for the Web3 fork option in Gither."""

from __future__ import annotations

import json

__all__ = ["web3_fork_feature_json", "web3_fork_feature_markdown"]

FEATURE = {
    "slug": "chain-stitch",
    "feature_flag": "web3_fork",
    "display_name": "Chain Stitch",
    "summary": (
        "Portable Web3 fork and mirror mode for Gither, turning a hosted-forge "
        "repository into a p2p, versioned, content-addressed fork state."
    ),
    "translations": {
        "en": "chain stitch",
        "nl": "kettingsteek",
        "de": "Kettenstich",
        "fr": "point de chaînette",
        "es": "punto de cadeneta",
        "it": "punto catenella",
    },
}


def web3_fork_feature_json() -> str:
    """Return the feature spec as stable JSON."""
    return json.dumps(FEATURE, indent=2, sort_keys=True) + "\n"


def web3_fork_feature_markdown() -> str:
    """Return the feature spec as operator-readable Markdown."""
    lines = [
        "# Web3 Fork Feature",
        "",
        "Feature flag: `web3_fork`",
        f"Feature name: `{FEATURE['display_name']}`",
        f"Slug: `{FEATURE['slug']}`",
        "",
        FEATURE["summary"],
        "",
        "## Stitch Term",
        "",
    ]
    for language, term in FEATURE["translations"].items():
        lines.append(f"- `{language}`: {term}")
    lines.extend(
        [
            "",
            "## Intent",
            "",
            "- mirror repository state into p2p/Web3-addressable records;",
            "- keep Git compatibility while moving authority into portable records;",
            "- treat hosted forges as optional mirrors, not the root of trust.",
        ]
    )
    return "\n".join(lines)

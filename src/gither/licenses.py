"""License protocol records for Gither mirror policy."""

from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class LicenseTemplate:
    """Platform license template normalized for Gither mirror policy."""

    key: str
    name: str
    platforms: tuple[str, ...]
    category: str
    mirror_policy: str
    conditions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        """Serialize the license template record."""
        return {
            "key": self.key,
            "name": self.name,
            "platforms": list(self.platforms),
            "category": self.category,
            "mirror_policy": self.mirror_policy,
            "conditions": list(self.conditions),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ClauseDefinition:
    """Reusable clause term for Gither p2p license records."""

    key: str
    definition: str
    p2p_effect: str

    def to_json(self) -> dict[str, str]:
        """Serialize the clause definition."""
        return {
            "key": self.key,
            "definition": self.definition,
            "p2p_effect": self.p2p_effect,
        }


@dataclass(frozen=True)
class CustomLicenseProfile:
    """Source-available or custom license profile used by major software projects."""

    key: str
    name: str
    used_by: tuple[str, ...]
    classification: str
    mirror_policy: str
    clauses: tuple[str, ...]
    source_url: str

    def to_json(self) -> dict[str, object]:
        """Serialize the custom license profile."""
        return {
            "key": self.key,
            "name": self.name,
            "used_by": list(self.used_by),
            "classification": self.classification,
            "mirror_policy": self.mirror_policy,
            "clauses": list(self.clauses),
            "source_url": self.source_url,
        }


GITHUB_TEMPLATE_KEYS = (
    "agpl-3.0",
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "bsl-1.0",
    "cc0-1.0",
    "epl-2.0",
    "gpl-2.0",
    "gpl-3.0",
    "lgpl-2.1",
    "mit",
    "mpl-2.0",
    "unlicense",
)


PLATFORM_LICENSES = (
    ("0bsd", "BSD Zero Clause License", ("gitlab",), "permissive-zero", "code_archive_ok", (), ("liability", "warranty")),
    ("afl-3.0", "Academic Free License v3.0", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright", "document-changes"), ("trademark-use", "liability", "warranty")),
    ("agpl-3.0", "GNU Affero General Public License v3.0", ("github", "gitlab"), "network-copyleft", "code_archive_ok_service_restricted", ("include-copyright", "document-changes", "disclose-source", "network-use-disclose", "same-license"), ("liability", "warranty")),
    ("apache-2.0", "Apache License 2.0", ("github", "gitlab"), "permissive-patent", "code_archive_ok", ("include-copyright", "document-changes"), ("trademark-use", "liability", "warranty")),
    ("artistic-2.0", "Artistic License 2.0", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright", "document-changes"), ("liability", "trademark-use", "warranty")),
    ("blueoak-1.0.0", "Blue Oak Model License 1.0.0", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("bsd-2-clause", "BSD 2-Clause Simplified License", ("github", "gitlab"), "permissive", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("bsd-2-clause-patent", "BSD-2-Clause Plus Patent License", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("bsd-3-clause", "BSD 3-Clause New or Revised License", ("github", "gitlab"), "permissive", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("bsd-3-clause-clear", "BSD 3-Clause Clear License", ("gitlab",), "permissive", "code_archive_ok_scan_patents", ("include-copyright",), ("liability", "patent-use", "warranty")),
    ("bsd-4-clause", "BSD 4-Clause Original or Old License", ("gitlab",), "permissive-advertising", "code_archive_ok_advertising_notice", ("include-copyright",), ("liability", "warranty")),
    ("bsl-1.0", "Boost Software License 1.0", ("github", "gitlab"), "permissive", "code_archive_ok", ("include-copyright--source",), ("liability", "warranty")),
    ("cc-by-4.0", "Creative Commons Attribution 4.0 International", ("gitlab",), "content-attribution", "content_archive_ok_attribution", ("include-copyright", "document-changes"), ("liability", "trademark-use", "patent-use", "warranty")),
    ("cc-by-sa-4.0", "Creative Commons Attribution Share Alike 4.0 International", ("gitlab",), "content-sharealike", "content_archive_ok_sharealike", ("include-copyright", "document-changes", "same-license"), ("liability", "trademark-use", "patent-use", "warranty")),
    ("cc0-1.0", "Creative Commons Zero v1.0 Universal", ("github", "gitlab"), "public-domain-style", "code_archive_ok", (), ("liability", "trademark-use", "patent-use", "warranty")),
    ("cecill-2.1", "CeCILL Free Software License Agreement v2.1", ("gitlab",), "network-copyleft", "code_archive_ok_service_restricted", ("include-copyright", "network-use-disclose", "disclose-source", "same-license"), ("liability", "warranty")),
    ("cern-ohl-p-2.0", "CERN Open Hardware Licence Version 2 - Permissive", ("gitlab",), "hardware-permissive", "hardware_archive_ok", ("include-copyright", "document-changes"), ("liability", "warranty")),
    ("cern-ohl-s-2.0", "CERN Open Hardware Licence Version 2 - Strongly Reciprocal", ("gitlab",), "hardware-strong-reciprocal", "hardware_archive_ok_reciprocal", ("include-copyright", "document-changes", "disclose-source", "same-license"), ("liability", "warranty")),
    ("cern-ohl-w-2.0", "CERN Open Hardware Licence Version 2 - Weakly Reciprocal", ("gitlab",), "hardware-weak-reciprocal", "hardware_archive_ok_reciprocal", ("include-copyright", "document-changes", "disclose-source", "same-license--library"), ("liability", "warranty")),
    ("ecl-2.0", "Educational Community License v2.0", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright", "document-changes"), ("trademark-use", "liability", "warranty")),
    ("epl-1.0", "Eclipse Public License 1.0", ("gitlab",), "weak-copyleft", "code_archive_ok_file_reciprocal", ("disclose-source", "include-copyright", "same-license"), ("liability", "warranty")),
    ("epl-2.0", "Eclipse Public License 2.0", ("github", "gitlab"), "weak-copyleft", "code_archive_ok_file_reciprocal", ("disclose-source", "include-copyright", "same-license"), ("liability", "warranty")),
    ("eupl-1.1", "European Union Public License 1.1", ("gitlab",), "network-copyleft", "code_archive_ok_service_restricted", ("include-copyright", "disclose-source", "document-changes", "network-use-disclose", "same-license"), ("liability", "trademark-use", "warranty")),
    ("eupl-1.2", "European Union Public License 1.2", ("gitlab",), "network-copyleft", "code_archive_ok_service_restricted", ("include-copyright", "disclose-source", "document-changes", "network-use-disclose", "same-license"), ("liability", "trademark-use", "warranty")),
    ("gfdl-1.3", "GNU Free Documentation License v1.3", ("gitlab",), "documentation-copyleft", "content_archive_ok_sharealike", ("include-copyright", "disclose-source", "same-license", "document-changes"), ("liability", "warranty")),
    ("gpl-2.0", "GNU General Public License v2.0", ("github", "gitlab"), "strong-copyleft", "code_archive_ok_distribution_restricted", ("include-copyright", "document-changes", "disclose-source", "same-license"), ("liability", "warranty")),
    ("gpl-3.0", "GNU General Public License v3.0", ("github", "gitlab"), "strong-copyleft", "code_archive_ok_distribution_restricted", ("include-copyright", "document-changes", "disclose-source", "same-license"), ("liability", "warranty")),
    ("isc", "ISC License", ("gitlab",), "permissive", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("lgpl-2.1", "GNU Lesser General Public License v2.1", ("github", "gitlab"), "weak-copyleft", "code_archive_ok_library_reciprocal", ("include-copyright", "disclose-source", "document-changes", "same-license--library"), ("liability", "warranty")),
    ("lgpl-3.0", "GNU Lesser General Public License v3.0", ("gitlab",), "weak-copyleft", "code_archive_ok_library_reciprocal", ("include-copyright", "disclose-source", "document-changes", "same-license--library"), ("liability", "warranty")),
    ("lppl-1.3c", "LaTeX Project Public License v1.3c", ("gitlab",), "managed-modification", "code_archive_ok_name_change_required", ("include-copyright", "document-changes", "disclose-source"), ("liability", "warranty")),
    ("mit", "MIT License", ("github", "gitlab"), "permissive", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("mit-0", "MIT No Attribution", ("gitlab",), "permissive-zero", "code_archive_ok", (), ("liability", "warranty")),
    ("mpl-2.0", "Mozilla Public License 2.0", ("github", "gitlab"), "weak-copyleft", "code_archive_ok_file_reciprocal", ("disclose-source", "include-copyright", "same-license--file"), ("liability", "trademark-use", "warranty")),
    ("ms-pl", "Microsoft Public License", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright",), ("warranty", "trademark-use")),
    ("ms-rl", "Microsoft Reciprocal License", ("gitlab",), "weak-copyleft", "code_archive_ok_file_reciprocal", ("disclose-source", "include-copyright", "same-license--file"), ("warranty", "trademark-use")),
    ("mulanpsl-2.0", "Mulan Permissive Software License, Version 2", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright",), ("liability", "trademark-use", "warranty")),
    ("ncsa", "University of Illinois/NCSA Open Source License", ("gitlab",), "permissive", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("odbl-1.0", "Open Data Commons Open Database License v1.0", ("gitlab",), "database-sharealike", "data_archive_ok_sharealike", ("disclose-source", "include-copyright", "same-license"), ("liability", "patent-use", "trademark-use", "warranty")),
    ("ofl-1.1", "SIL Open Font License 1.1", ("gitlab",), "font-copyleft", "font_archive_ok_reserved_name_scan", ("include-copyright", "same-license"), ("liability", "warranty")),
    ("osl-3.0", "Open Software License 3.0", ("gitlab",), "network-copyleft", "code_archive_ok_service_restricted", ("include-copyright", "disclose-source", "document-changes", "network-use-disclose", "same-license"), ("trademark-use", "liability", "warranty")),
    ("postgresql", "PostgreSQL License", ("gitlab",), "permissive", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("unlicense", "The Unlicense", ("github", "gitlab"), "public-domain-style", "code_archive_ok", (), ("liability", "warranty")),
    ("upl-1.0", "Universal Permissive License v1.0", ("gitlab",), "permissive-patent", "code_archive_ok", ("include-copyright",), ("liability", "warranty")),
    ("vim", "Vim License", ("gitlab",), "charityware-copyleft", "code_archive_ok_manual_review", ("include-copyright", "document-changes", "disclose-source", "same-license"), ()),
    ("zlib", "zlib License", ("gitlab",), "permissive", "code_archive_ok", ("include-copyright--source", "document-changes"), ("liability", "warranty")),
)


CLAUSES = (
    ClauseDefinition("include-copyright", "Keep copyright and license notices with every mirrored copy.", "Gither p2p nodes must pin notice files and expose them with the object graph."),
    ClauseDefinition("document-changes", "Mark modified files or derivative versions.", "Mirror manifests must distinguish verbatim mirrors from Gither-modified forks."),
    ClauseDefinition("disclose-source", "Provide corresponding source when distributing covered binaries or derivatives.", "Executable mirrors require source availability receipts."),
    ClauseDefinition("network-use-disclose", "Network service use can trigger source disclosure.", "Serverless deployments must attach service-source obligations before launch."),
    ClauseDefinition("same-license", "Derivative or covered works must remain under the same license.", "P2P forks must carry reciprocal-license constraints in dependency records."),
    ClauseDefinition("same-license--file", "Reciprocity applies at file level.", "Gither can isolate modified files instead of tainting the whole repository."),
    ClauseDefinition("same-license--library", "Reciprocity applies to the covered library or linked component.", "Dependency graph must preserve library boundaries."),
    ClauseDefinition("trademark-use", "The license does not grant broad trademark rights.", "Mirror UI cannot imply endorsement by upstream owners."),
    ClauseDefinition("patent-use", "Patent grant is absent, limited, or terminated under some conditions.", "Policy engine must mark patent risk before executable distribution."),
    ClauseDefinition("managed-service-restriction", "Offering the software as a hosted or managed service is restricted.", "P2P code archive may be allowed; Gither-hosted execution is blocked without consent."),
    ClauseDefinition("license-key-restriction", "Changing license-key checks or feature-lock controls is restricted.", "Executable mirrors must block patched licensing controls unless the owner consents."),
    ClauseDefinition("notice-preservation", "License, source-available, and attribution notices must remain visible.", "P2P records must pin upstream notice payloads beside mirrored objects."),
    ClauseDefinition("field-of-use", "Use is restricted to specific purposes, users, revenue, scale, or environments.", "License records must include allowed and forbidden use contexts."),
    ClauseDefinition("change-date", "A source-available license converts to another license on a defined date.", "P2P nodes can schedule automatic policy downgrade when the change date arrives."),
    ClauseDefinition("no-selling", "Selling the licensed software or substantially similar commercial offering is restricted.", "Economic mirrors cannot create paid distribution without owner consent."),
    ClauseDefinition("noncommercial", "Commercial use is restricted.", "Gither royalty and marketplace features must be disabled unless separately licensed."),
    ClauseDefinition("source-available-not-open-source", "Source is visible but the license is not OSI-style open source.", "Catalog mirror is safe; code archive or execution requires policy-specific review."),
)


CUSTOM_LICENSES = (
    CustomLicenseProfile(
        key="elastic-2.0",
        name="Elastic License 2.0",
        used_by=("Elastic", "Elasticsearch", "Kibana"),
        classification="source-available-not-open-source",
        mirror_policy="catalog_ok_code_archive_requires_clause_review",
        clauses=("managed-service-restriction", "license-key-restriction", "notice-preservation", "source-available-not-open-source"),
        source_url="https://www.elastic.co/licensing/elastic-license",
    ),
    CustomLicenseProfile(
        key="sspl-1.0",
        name="Server Side Public License 1.0",
        used_by=("MongoDB", "Graylog", "historical Elastic option"),
        classification="source-available-network-copyleft",
        mirror_policy="catalog_ok_code_archive_ok_no_service_without_full_service_source",
        clauses=("network-use-disclose", "managed-service-restriction", "same-license", "source-available-not-open-source"),
        source_url="https://www.mongodb.com/licensing/server-side-public-license",
    ),
    CustomLicenseProfile(
        key="busl-1.1",
        name="Business Source License 1.1",
        used_by=("MariaDB MaxScale", "HashiCorp Terraform lineage", "CockroachDB"),
        classification="source-available-time-delayed-open",
        mirror_policy="catalog_ok_code_archive_requires_additional_use_grant_and_change_date",
        clauses=("field-of-use", "change-date", "source-available-not-open-source"),
        source_url="https://mariadb.com/bsl11/",
    ),
    CustomLicenseProfile(
        key="commons-clause",
        name="Commons Clause",
        used_by=("historical Redis Labs modules", "source-available commercial addenda"),
        classification="source-available-no-selling-addendum",
        mirror_policy="catalog_ok_code_archive_requires_underlying_license_and_no_selling_check",
        clauses=("no-selling", "source-available-not-open-source"),
        source_url="https://commonsclause.com/",
    ),
    CustomLicenseProfile(
        key="polyform-noncommercial-1.0.0",
        name="PolyForm Noncommercial License 1.0.0",
        used_by=("source-available commercial projects", "noncommercial shared code"),
        classification="source-available-noncommercial",
        mirror_policy="catalog_ok_noncommercial_code_archive_only",
        clauses=("noncommercial", "field-of-use", "source-available-not-open-source"),
        source_url="https://polyformproject.org/licenses/noncommercial/1.0.0/",
    ),
)


def platform_license_templates(platform: str | None = None) -> tuple[LicenseTemplate, ...]:
    """Return normalized GitHub and GitLab license templates."""
    records = tuple(LicenseTemplate(*item) for item in PLATFORM_LICENSES)
    if platform is None:
        return records
    return tuple(record for record in records if platform in record.platforms)


def custom_license_profiles() -> tuple[CustomLicenseProfile, ...]:
    """Return custom source-available license profiles."""
    return CUSTOM_LICENSES


def clause_definitions() -> tuple[ClauseDefinition, ...]:
    """Return Gither clause vocabulary definitions."""
    return CLAUSES


def license_protocol_json() -> dict[str, object]:
    """Return the Gither license protocol as plain JSON data."""
    return {
        "snapshot": {
            "github_templates": len(platform_license_templates("github")),
            "gitlab_templates": len(platform_license_templates("gitlab")),
            "union_templates": len(platform_license_templates()),
            "custom_profiles": len(CUSTOM_LICENSES),
        },
        "p2p_records": (
            "license_record",
            "clause_record",
            "notice_record",
            "consent_record",
            "mirror_manifest",
        ),
        "platform_templates": [record.to_json() for record in platform_license_templates()],
        "clauses": [clause.to_json() for clause in CLAUSES],
        "custom_profiles": [profile.to_json() for profile in CUSTOM_LICENSES],
    }


def license_protocol_markdown() -> str:
    """Return the Gither license protocol as Markdown."""
    return "\n".join(_license_protocol_lines())


def license_protocol_json_text() -> str:
    """Return the Gither license protocol as stable JSON text."""
    return json.dumps(license_protocol_json(), indent=2, sort_keys=True) + "\n"


def _license_protocol_lines() -> list[str]:
    lines = [
        "# Gither License Protocol",
        "",
        "Gither mirrors metadata by default and mirrors code only when license records allow it.",
        "",
        "## Snapshot",
        "",
        f"- GitHub templates: {len(platform_license_templates('github'))}",
        f"- GitLab templates: {len(platform_license_templates('gitlab'))}",
        f"- Union templates: {len(platform_license_templates())}",
        f"- Custom profiles: {len(CUSTOM_LICENSES)}",
        "",
        "## P2P Records",
        "",
        "- license_record: normalized platform or custom license identity.",
        "- clause_record: extracted obligations, restrictions, and definitions.",
        "- notice_record: copyright, attribution, NOTICE, and license-text payloads.",
        "- consent_record: maintainer permission beyond the public license.",
        "- mirror_manifest: policy decision for catalog, archive, executable, and economic mirrors.",
        "",
        "## Platform Templates",
        "",
    ]
    lines.extend(_template_lines())
    lines.extend(["", "## Custom Source-Available Profiles", ""])
    lines.extend(_custom_lines())
    lines.extend(["", "## Clause Vocabulary", ""])
    lines.extend(_clause_lines())
    return lines


def _template_lines() -> list[str]:
    return [
        f"- `{record.key}` ({', '.join(record.platforms)}): {record.mirror_policy}; {record.name}"
        for record in platform_license_templates()
    ]


def _custom_lines() -> list[str]:
    return [
        f"- `{profile.key}`: {profile.mirror_policy}; clauses={', '.join(profile.clauses)}"
        for profile in CUSTOM_LICENSES
    ]


def _clause_lines() -> list[str]:
    return [
        f"- `{clause.key}`: {clause.definition} P2P effect: {clause.p2p_effect}"
        for clause in CLAUSES
    ]

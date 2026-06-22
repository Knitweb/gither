import json

from gither.licenses import (
    clause_definitions,
    custom_license_profiles,
    license_protocol_json_text,
    platform_license_templates,
)


def test_platform_license_protocol_covers_github_and_gitlab_templates() -> None:
    github = platform_license_templates("github")
    gitlab = platform_license_templates("gitlab")
    union = platform_license_templates()

    assert len(github) == 13
    assert len(gitlab) == 46
    assert len(union) == 46
    assert {record.key for record in github} <= {record.key for record in gitlab}


def test_custom_license_profiles_break_out_restrictive_clauses() -> None:
    profiles = {profile.key: profile for profile in custom_license_profiles()}

    assert "managed-service-restriction" in profiles["elastic-2.0"].clauses
    assert "network-use-disclose" in profiles["sspl-1.0"].clauses
    assert "change-date" in profiles["busl-1.1"].clauses
    assert "no-selling" in profiles["commons-clause"].clauses
    assert "noncommercial" in profiles["polyform-noncommercial-1.0.0"].clauses


def test_clause_definitions_include_p2p_effects() -> None:
    clauses = {clause.key: clause for clause in clause_definitions()}

    assert "mirror manifests" in clauses["document-changes"].p2p_effect.lower()
    assert "royalty" in clauses["noncommercial"].p2p_effect.lower()


def test_custom_profile_clauses_are_defined() -> None:
    clauses = {clause.key for clause in clause_definitions()}
    custom_clauses = {
        clause
        for profile in custom_license_profiles()
        for clause in profile.clauses
    }

    assert custom_clauses <= clauses


def test_license_protocol_json_is_stable() -> None:
    payload = json.loads(license_protocol_json_text())

    assert payload["snapshot"]["github_templates"] == 13
    assert payload["snapshot"]["gitlab_templates"] == 46
    assert "mirror_manifest" in payload["p2p_records"]

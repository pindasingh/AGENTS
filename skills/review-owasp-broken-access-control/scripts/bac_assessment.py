#!/usr/bin/env python3
"""Validate and render OWASP A01:2025 Broken Access Control assessments."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_renderers import render_html_report, render_markdown_report, resolve_output_format

SCHEMA_VERSION = "1.3"
PROFILE = "OWASP A01:2025"
CV_IDS = tuple(f"A01-CV-{number:02d}" for number in range(1, 9))
PR_IDS = tuple(f"A01-PR-{number:02d}" for number in range(1, 12))
REQUIRED_COVERAGE_IDS = CV_IDS + PR_IDS
COVERAGE_NAMES = {
    "A01-CV-01": "Least privilege and deny-by-default failure",
    "A01-CV-02": "URL, parameter, state, HTML, or API-request bypass",
    "A01-CV-03": "IDOR and object-level authorization",
    "A01-CV-04": "Missing API operation controls",
    "A01-CV-05": "Anonymous, horizontal, or vertical privilege escalation",
    "A01-CV-06": "Authorization metadata manipulation or replay",
    "A01-CV-07": "CORS trust-policy failure",
    "A01-CV-08": "Force browsing",
    "A01-PR-01": "Trusted server-side enforcement",
    "A01-PR-02": "Deny by default",
    "A01-PR-03": "Consistent reusable mechanisms and minimal CORS",
    "A01-PR-04": "Record ownership",
    "A01-PR-05": "Domain business limits",
    "A01-PR-06": "Directory listing and exposed metadata/backups",
    "A01-PR-07": "Failure logging and alerting",
    "A01-PR-08": "Rate limits against automated abuse",
    "A01-PR-09": "Session and token invalidation",
    "A01-PR-10": "Established declarative controls",
    "A01-PR-11": "Functional authorization tests",
}
COVERAGE_STATUSES = {"finding", "reviewed-no-finding", "not-applicable", "not-assessed"}
FINDING_STATUSES = {"confirmed", "likely", "needs-validation"}
SEVERITIES = {"critical", "high", "medium", "low", "informational"}
CONFIDENCES = {"high", "medium", "low"}
AUTHORIZATION_MODES = {"static-only", "supplied-evidence", "live-authorized"}
EVIDENCE_KINDS = {
    "source", "config", "test", "request", "response", "runtime", "documentation", "other"
}
OFFICIAL_CWES = {
    "CWE-22", "CWE-23", "CWE-36", "CWE-59", "CWE-61", "CWE-65", "CWE-200", "CWE-201",
    "CWE-219", "CWE-276", "CWE-281", "CWE-282", "CWE-283", "CWE-284", "CWE-285",
    "CWE-352", "CWE-359", "CWE-377", "CWE-379", "CWE-402", "CWE-424", "CWE-425",
    "CWE-441", "CWE-497", "CWE-538", "CWE-540", "CWE-548", "CWE-552", "CWE-566",
    "CWE-601", "CWE-615", "CWE-639", "CWE-668", "CWE-732", "CWE-749", "CWE-862",
    "CWE-863", "CWE-918", "CWE-922", "CWE-1275",
}
SUPPLEMENTAL_API_CWES = {"CWE-213", "CWE-915"}
ALLOWED_CWES = OFFICIAL_CWES | SUPPLEMENTAL_API_CWES
SELECTED_WSTG_IDS = {
    "WSTG-INFO-06", "WSTG-INFO-07", "WSTG-INFO-10",
    "WSTG-CONF-03", "WSTG-CONF-04", "WSTG-CONF-05", "WSTG-CONF-06", "WSTG-CONF-09", "WSTG-CONF-11",
    "WSTG-IDNT-01", "WSTG-IDNT-03", "WSTG-ATHN-04", "WSTG-ATHN-10",
    "WSTG-ATHZ-01", "WSTG-ATHZ-02", "WSTG-ATHZ-03", "WSTG-ATHZ-04",
    "WSTG-SESS-01", "WSTG-SESS-02", "WSTG-SESS-05", "WSTG-SESS-06", "WSTG-SESS-07",
    "WSTG-INPV-03", "WSTG-INPV-04", "WSTG-INPV-19", "WSTG-ERRH-01",
    "WSTG-BUSL-02", "WSTG-BUSL-03", "WSTG-BUSL-05", "WSTG-BUSL-06", "WSTG-BUSL-07",
    "WSTG-CLNT-07", "WSTG-CLNT-12", "WSTG-APIT-01",
}
ALLOWED_WSTG_MAPPINGS = {f"WSTG v4.2-{value.removeprefix('WSTG-')}" for value in SELECTED_WSTG_IDS}
MODEL_FIELDS = ("actors", "resources", "actions", "contexts", "enforcementPoints", "policyStatements")
AFFECTED_IMPLEMENTATION_FIELDS = ("controllers", "classes", "methods", "endpoints", "filesOrArtifacts")
ISSUE_BLOCK_FIELDS = ("expectedAccessRule", "exercise", "failureProof", "impact", "remediation")
SNIPPET_LANGUAGES = {"text", "pseudo", "http", "graphql", "yaml", "json"}
MAX_SNIPPET_LINES = 12
MAX_SNIPPET_CHARS = 1600
TRACE_STATUSES = {"complete", "partial", "blocked"}
TIER_STATUSES = {"verified", "partial", "unverified"}
TIER_TYPES = {
    "identity", "client", "edge", "gateway", "bff", "application", "policy", "domain", "data",
    "cache", "downstream", "async", "external", "other",
}
GAP_REQUEST_STATUSES = {"awaiting-user", "excluded-by-user", "confirmed-unavailable"}


class ValidationError(Exception):
    """Raised when an assessment violates the report contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"assessment does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValidationError("assessment root must be a JSON object")
    return data


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_object(parent: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def require_list(parent: dict[str, Any], key: str, errors: list[str]) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        errors.append(f"{key} must be an array")
        return []
    return value


def require_strings(parent: dict[str, Any], keys: tuple[str, ...], prefix: str, errors: list[str]) -> None:
    for key in keys:
        if not nonempty_string(parent.get(key)):
            errors.append(f"{prefix}.{key} must be a non-empty string")


def validate_evidence(items: Any, prefix: str, errors: list[str], *, required: bool = False) -> None:
    if not isinstance(items, list):
        errors.append(f"{prefix} must be an array")
        return
    if required and not items:
        errors.append(f"{prefix} must contain at least one evidence item")
    for index, item in enumerate(items):
        item_prefix = f"{prefix}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_prefix} must be an object")
            continue
        require_strings(item, ("kind", "location", "observation", "revision"), item_prefix, errors)
        if item.get("kind") not in EVIDENCE_KINDS:
            errors.append(f"{item_prefix}.kind must be one of {sorted(EVIDENCE_KINDS)}")


def validate_issue_block(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be an object")
        return
    require_strings(value, ("summary", "language", "pseudocode"), prefix, errors)
    language = value.get("language")
    if language not in SNIPPET_LANGUAGES:
        errors.append(f"{prefix}.language must be one of {sorted(SNIPPET_LANGUAGES)}")
    pseudocode = value.get("pseudocode")
    if nonempty_string(pseudocode):
        if "```" in pseudocode:
            errors.append(f"{prefix}.pseudocode must not contain Markdown fences")
        nonblank_lines = [line for line in pseudocode.splitlines() if line.strip()]
        if len(nonblank_lines) > MAX_SNIPPET_LINES:
            errors.append(f"{prefix}.pseudocode must not exceed {MAX_SNIPPET_LINES} non-blank lines")
        if len(pseudocode) > MAX_SNIPPET_CHARS:
            errors.append(f"{prefix}.pseudocode must not exceed {MAX_SNIPPET_CHARS} characters")


def validate_assessment(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION!r}")

    assessment = require_object(data, "assessment", errors)
    require_strings(
        assessment,
        ("title", "subject", "revision", "environment", "assessmentDate", "profile", "authorizationMode", "summary"),
        "assessment",
        errors,
    )
    if assessment.get("profile") != PROFILE:
        errors.append(f"assessment.profile must be {PROFILE!r}")
    mode = assessment.get("authorizationMode")
    if mode not in AUTHORIZATION_MODES:
        errors.append(f"assessment.authorizationMode must be one of {sorted(AUTHORIZATION_MODES)}")
    for key in ("authorizedTargets", "scope", "exclusions", "limitations"):
        values = require_list(assessment, key, errors)
        if any(not nonempty_string(value) for value in values):
            errors.append(f"assessment.{key} must contain only non-empty strings")
    if mode == "live-authorized" and not assessment.get("authorizedTargets"):
        errors.append("assessment.authorizedTargets must not be empty for live-authorized assessments")

    model = require_object(data, "authorizationModel", errors)
    for key in MODEL_FIELDS:
        values = require_list(model, key, errors)
        if any(not nonempty_string(value) for value in values):
            errors.append(f"authorizationModel.{key} must contain only non-empty strings")
    access_paths = require_list(model, "accessPaths", errors)
    access_path_ids: set[str] = set()
    access_paths_by_id: dict[str, dict[str, Any]] = {}
    for index, access_path in enumerate(access_paths):
        prefix = f"authorizationModel.accessPaths[{index}]"
        if not isinstance(access_path, dict):
            errors.append(f"{prefix} must be an object")
            continue
        require_strings(
            access_path,
            ("id", "entryPoint", "channel", "authentication", "resource", "traceStatus"),
            prefix,
            errors,
        )
        access_path_id = access_path.get("id")
        if nonempty_string(access_path_id):
            if access_path_id in access_path_ids:
                errors.append(f"duplicate access path id: {access_path_id}")
            access_path_ids.add(access_path_id)
            access_paths_by_id[access_path_id] = access_path
        trace_status = access_path.get("traceStatus")
        if trace_status not in TRACE_STATUSES:
            errors.append(f"{prefix}.traceStatus must be one of {sorted(TRACE_STATUSES)}")
        for key in ("methodsOrOperations", "actors", "actions", "inputVectors"):
            values = access_path.get(key)
            if not isinstance(values, list) or not values or any(not nonempty_string(value) for value in values):
                errors.append(f"{prefix}.{key} must be a non-empty array of non-empty strings")
        gap_ids = access_path.get("gapIds")
        if not isinstance(gap_ids, list) or any(not nonempty_string(value) for value in gap_ids):
            errors.append(f"{prefix}.gapIds must be an array of non-empty strings")
            gap_ids = []
        if trace_status == "complete" and gap_ids:
            errors.append(f"{prefix}.gapIds must be empty when traceStatus is complete")
        if trace_status in {"partial", "blocked"} and not gap_ids:
            errors.append(f"{prefix}.gapIds must identify blocking evidence when traceStatus is {trace_status}")

        tiers = access_path.get("tiers")
        if not isinstance(tiers, list) or not tiers:
            errors.append(f"{prefix}.tiers must be a non-empty array")
            tiers = []
        for tier_index, tier in enumerate(tiers):
            tier_prefix = f"{prefix}.tiers[{tier_index}]"
            if not isinstance(tier, dict):
                errors.append(f"{tier_prefix} must be an object")
                continue
            require_strings(
                tier,
                ("name", "type", "component", "entryIdentity", "exitIdentity", "decision", "status"),
                tier_prefix,
                errors,
            )
            if tier.get("type") not in TIER_TYPES:
                errors.append(f"{tier_prefix}.type must be one of {sorted(TIER_TYPES)}")
            tier_status = tier.get("status")
            if tier_status not in TIER_STATUSES:
                errors.append(f"{tier_prefix}.status must be one of {sorted(TIER_STATUSES)}")
            for key in ("credentials", "policies", "resourceContext"):
                values = tier.get(key)
                if not isinstance(values, list) or any(not nonempty_string(value) for value in values):
                    errors.append(f"{tier_prefix}.{key} must be an array of non-empty strings")
            validate_evidence(
                tier.get("evidence"),
                f"{tier_prefix}.evidence",
                errors,
                required=tier_status == "verified",
            )
        tier_statuses = {tier.get("status") for tier in tiers if isinstance(tier, dict)}
        if trace_status == "complete" and any(status != "verified" for status in tier_statuses):
            errors.append(f"{prefix}.tiers must all be verified when traceStatus is complete")
        if trace_status in {"partial", "blocked"} and tier_statuses == {"verified"}:
            errors.append(f"{prefix}.tiers must expose at least one partial or unverified material tier")
        validate_evidence(access_path.get("evidence"), f"{prefix}.evidence", errors, required=True)

    coverage = require_list(data, "coverage", errors)
    coverage_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(coverage):
        prefix = f"coverage[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        branch_id = item.get("id")
        if not nonempty_string(branch_id):
            errors.append(f"{prefix}.id must be a non-empty string")
            continue
        if branch_id in coverage_by_id:
            errors.append(f"duplicate coverage id: {branch_id}")
        coverage_by_id[branch_id] = item
        if item.get("status") not in COVERAGE_STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(COVERAGE_STATUSES)}")
        if not nonempty_string(item.get("rationale")):
            errors.append(f"{prefix}.rationale must be a non-empty string")
        validate_evidence(
            item.get("evidence"),
            f"{prefix}.evidence",
            errors,
            required=item.get("status") == "reviewed-no-finding",
        )
        finding_ids = item.get("findingIds")
        if not isinstance(finding_ids, list) or any(not nonempty_string(value) for value in finding_ids):
            errors.append(f"{prefix}.findingIds must be an array of non-empty strings")
        if item.get("status") == "finding" and not finding_ids:
            errors.append(f"{prefix}.findingIds must not be empty when status is finding")
        if item.get("status") != "finding" and finding_ids:
            errors.append(f"{prefix}.findingIds must be empty unless status is finding")

    actual_ids = set(coverage_by_id)
    required_ids = set(REQUIRED_COVERAGE_IDS)
    missing_ids = sorted(required_ids - actual_ids)
    extra_ids = sorted(actual_ids - required_ids)
    if missing_ids:
        errors.append(f"missing required coverage ids: {', '.join(missing_ids)}")
    if extra_ids:
        errors.append(f"unknown coverage ids: {', '.join(extra_ids)}")

    findings = require_list(data, "findings", errors)
    findings_by_id: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(findings):
        prefix = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        require_strings(
            finding,
            (
                "id", "title", "category", "component", "classification", "status", "severity", "confidence",
                "summary", "actor", "resource", "action", "severityRationale",
            ),
            prefix,
            errors,
        )
        finding_id = finding.get("id")
        if nonempty_string(finding_id):
            if finding_id in findings_by_id:
                errors.append(f"duplicate finding id: {finding_id}")
            findings_by_id[finding_id] = finding
        status = finding.get("status")
        if status not in FINDING_STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(FINDING_STATUSES)}")
        severity = finding.get("severity")
        if severity not in SEVERITIES:
            errors.append(f"{prefix}.severity must be one of {sorted(SEVERITIES)}")
        if status == "needs-validation" and severity in {"critical", "high"}:
            errors.append(f"{prefix}.severity cannot be critical or high when status is needs-validation")
        if finding.get("confidence") not in CONFIDENCES:
            errors.append(f"{prefix}.confidence must be one of {sorted(CONFIDENCES)}")

        affected = finding.get("affectedImplementation")
        if not isinstance(affected, dict):
            errors.append(f"{prefix}.affectedImplementation must be an object")
        else:
            affected_count = 0
            for key in AFFECTED_IMPLEMENTATION_FIELDS:
                values = affected.get(key)
                if not isinstance(values, list) or any(not nonempty_string(value) for value in values):
                    errors.append(f"{prefix}.affectedImplementation.{key} must be an array of non-empty strings")
                else:
                    affected_count += len(values)
            if affected_count == 0:
                errors.append(f"{prefix}.affectedImplementation must identify at least one code or endpoint location")

        for key in ISSUE_BLOCK_FIELDS:
            validate_issue_block(finding.get(key), f"{prefix}.{key}", errors)

        branch_ids = finding.get("coverageIds")
        if not isinstance(branch_ids, list) or not branch_ids or any(value not in required_ids for value in branch_ids):
            errors.append(f"{prefix}.coverageIds must be a non-empty array of required coverage ids")

        finding_path_ids = finding.get("accessPathIds")
        if (
            not isinstance(finding_path_ids, list)
            or not finding_path_ids
            or any(value not in access_path_ids for value in finding_path_ids)
        ):
            errors.append(f"{prefix}.accessPathIds must be a non-empty array of known access path ids")

        attack_path = finding.get("attackPath")
        if not isinstance(attack_path, list) or len(attack_path) < 2 or any(not nonempty_string(step) for step in attack_path):
            errors.append(f"{prefix}.attackPath must contain at least two non-empty steps")
        validate_evidence(finding.get("evidence"), f"{prefix}.evidence", errors, required=True)

        mappings = finding.get("mappings")
        if not isinstance(mappings, dict):
            errors.append(f"{prefix}.mappings must be an object")
        else:
            for key in ("owasp", "asvs", "wstg", "apiTop10", "cwe"):
                values = mappings.get(key)
                if not isinstance(values, list) or any(not nonempty_string(value) for value in values):
                    errors.append(f"{prefix}.mappings.{key} must be an array of non-empty strings")
            if "A01:2025" not in mappings.get("owasp", []):
                errors.append(f"{prefix}.mappings.owasp must include A01:2025")
            cwes = set(mappings.get("cwe", []))
            unknown_cwes = sorted(cwes - ALLOWED_CWES)
            if unknown_cwes:
                errors.append(
                    f"{prefix}.mappings.cwe contains CWE(s) outside the bundled A01/API cross-references: "
                    f"{', '.join(unknown_cwes)}"
                )
            supplemental_cwes = cwes & SUPPLEMENTAL_API_CWES
            if supplemental_cwes and "API3:2023" not in mappings.get("apiTop10", []):
                errors.append(
                    f"{prefix}.mappings.cwe uses API3 supplemental CWE(s) without API3:2023: "
                    f"{', '.join(sorted(supplemental_cwes))}"
                )
            unknown_wstg = sorted(set(mappings.get("wstg", [])) - ALLOWED_WSTG_MAPPINGS)
            if unknown_wstg:
                errors.append(
                    f"{prefix}.mappings.wstg contains unselected or unversioned WSTG mapping(s): "
                    f"{', '.join(unknown_wstg)}"
                )

        regression_tests = finding.get("regressionTests")
        if not isinstance(regression_tests, list) or len(regression_tests) < 2:
            errors.append(f"{prefix}.regressionTests must contain at least an allowed and denied test")
        else:
            if len(regression_tests) > MAX_SNIPPET_LINES:
                errors.append(f"{prefix}.regressionTests must not exceed {MAX_SNIPPET_LINES} concise cases")
            test_types: set[str] = set()
            for test_index, test in enumerate(regression_tests):
                test_prefix = f"{prefix}.regressionTests[{test_index}]"
                if not isinstance(test, dict):
                    errors.append(f"{test_prefix} must be an object")
                    continue
                require_strings(test, ("type", "description", "expected"), test_prefix, errors)
                if test.get("type") not in {"allowed", "denied"}:
                    errors.append(f"{test_prefix}.type must be allowed or denied")
                else:
                    test_types.add(test["type"])
            if test_types != {"allowed", "denied"}:
                errors.append(f"{prefix}.regressionTests must include both allowed and denied types")
        limitations = finding.get("limitations")
        if not isinstance(limitations, list) or any(not nonempty_string(value) for value in limitations):
            errors.append(f"{prefix}.limitations must be an array of non-empty strings")

    # Cross-check coverage-to-finding and finding-to-coverage references.
    for branch_id, item in coverage_by_id.items():
        for finding_id in item.get("findingIds", []) if isinstance(item.get("findingIds"), list) else []:
            finding = findings_by_id.get(finding_id)
            if finding is None:
                errors.append(f"coverage {branch_id} references unknown finding {finding_id}")
            elif finding.get("status") not in {"confirmed", "likely"}:
                errors.append(f"coverage {branch_id} cannot use needs-validation finding {finding_id} for status finding")
            elif branch_id not in finding.get("coverageIds", []):
                errors.append(f"coverage {branch_id} references {finding_id}, but the finding does not reference the branch")
    for finding_id, finding in findings_by_id.items():
        linked_paths = [
            access_paths_by_id[path_id]
            for path_id in finding.get("accessPathIds", [])
            if path_id in access_paths_by_id
        ]
        if finding.get("status") == "confirmed" and not any(
            path.get("traceStatus") == "complete" for path in linked_paths
        ):
            errors.append(f"confirmed finding {finding_id} must reference at least one complete access path")
        if finding.get("status") in {"confirmed", "likely"}:
            for branch_id in finding.get("coverageIds", []):
                branch = coverage_by_id.get(branch_id)
                if branch and (branch.get("status") != "finding" or finding_id not in branch.get("findingIds", [])):
                    errors.append(f"finding {finding_id} is not reciprocally referenced by finding-status coverage {branch_id}")

    gaps = require_list(data, "gaps", errors)
    gap_ids: set[str] = set()
    gaps_by_id: dict[str, dict[str, Any]] = {}
    not_assessed_to_gap: set[str] = set()
    for index, gap in enumerate(gaps):
        prefix = f"gaps[{index}]"
        if not isinstance(gap, dict):
            errors.append(f"{prefix} must be an object")
            continue
        require_strings(
            gap,
            ("id", "title", "whyItMatters", "nextStep", "requestStatus", "userDecision"),
            prefix,
            errors,
        )
        gap_id = gap.get("id")
        if nonempty_string(gap_id):
            if gap_id in gap_ids:
                errors.append(f"duplicate gap id: {gap_id}")
            gap_ids.add(gap_id)
            gaps_by_id[gap_id] = gap
        if gap.get("requestStatus") not in GAP_REQUEST_STATUSES:
            errors.append(f"{prefix}.requestStatus must be one of {sorted(GAP_REQUEST_STATUSES)}")
        for key in ("searched", "requestedArtifacts", "blockedConclusions"):
            values = gap.get(key)
            if not isinstance(values, list) or not values or any(not nonempty_string(value) for value in values):
                errors.append(f"{prefix}.{key} must be a non-empty array of non-empty strings")
        coverage_ids = gap.get("coverageIds")
        if not isinstance(coverage_ids, list) or not coverage_ids or any(value not in required_ids for value in coverage_ids):
            errors.append(f"{prefix}.coverageIds must be a non-empty array of required coverage ids")
        else:
            not_assessed_to_gap.update(coverage_ids)
            for coverage_id in coverage_ids:
                branch = coverage_by_id.get(coverage_id)
                if branch and branch.get("status") == "reviewed-no-finding":
                    errors.append(f"{prefix}.coverageIds cannot treat unresolved {coverage_id} as reviewed-no-finding")
        path_ids = gap.get("accessPathIds")
        if not isinstance(path_ids, list) or any(value not in access_path_ids for value in path_ids):
            errors.append(f"{prefix}.accessPathIds must be an array of known access path ids")

    for path_id, access_path in access_paths_by_id.items():
        path_gap_ids = access_path.get("gapIds", []) if isinstance(access_path.get("gapIds"), list) else []
        for gap_id in path_gap_ids:
            gap = gaps_by_id.get(gap_id)
            if gap is None:
                errors.append(f"access path {path_id} references unknown gap {gap_id}")
            elif path_id not in gap.get("accessPathIds", []):
                errors.append(f"access path {path_id} references {gap_id}, but the gap does not reference the path")
        trace_status = access_path.get("traceStatus")
        referenced_statuses = {
            gaps_by_id[gap_id].get("requestStatus") for gap_id in path_gap_ids if gap_id in gaps_by_id
        }
        if trace_status == "blocked" and "awaiting-user" not in referenced_statuses:
            errors.append(f"blocked access path {path_id} must reference an awaiting-user gap")
        if trace_status == "partial" and referenced_statuses & {"awaiting-user"}:
            errors.append(f"partial access path {path_id} cannot reference an awaiting-user gap; it remains blocked")
        if trace_status == "partial" and not referenced_statuses & {"excluded-by-user", "confirmed-unavailable"}:
            errors.append(f"partial access path {path_id} must reference an explicitly excluded or unavailable gap")

    for gap_id, gap in gaps_by_id.items():
        for path_id in gap.get("accessPathIds", []) if isinstance(gap.get("accessPathIds"), list) else []:
            access_path = access_paths_by_id.get(path_id)
            if access_path and gap_id not in access_path.get("gapIds", []):
                errors.append(f"gap {gap_id} references {path_id}, but the access path does not reference the gap")

    for branch_id, item in coverage_by_id.items():
        if item.get("status") == "not-assessed" and branch_id not in not_assessed_to_gap:
            errors.append(f"not-assessed coverage {branch_id} must be referenced by a gap")

    any_reviewed = any(item.get("status") != "not-assessed" for item in coverage_by_id.values())
    if any_reviewed:
        for key in ("actors", "resources", "actions", "enforcementPoints", "policyStatements", "accessPaths"):
            if not model.get(key):
                errors.append(f"authorizationModel.{key} must not be empty once review coverage is recorded")

    return errors


def md(value: Any) -> str:
    text = str(value if value is not None else "")
    return text.replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()


def bullet_lines(values: list[Any], empty: str = "None recorded.") -> list[str]:
    return [f"- {md(value)}" for value in values] if values else [empty]


def render_evidence(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- None recorded."]
    return [
        f"- **{md(item.get('kind'))}:** `{md(item.get('location'))}` at `{md(item.get('revision'))}` — {md(item.get('observation'))}"
        for item in items
    ]


def grouped_findings(findings: list[dict[str, Any]]) -> list[tuple[str, list[tuple[str, list[dict[str, Any]]]]]]:
    categories: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for finding in findings:
        categories.setdefault(finding["category"], {}).setdefault(finding["component"], []).append(finding)
    return [
        (
            category,
            [
                (component, sorted(items, key=lambda item: item["id"]))
                for component, items in sorted(components.items(), key=lambda pair: pair[0].casefold())
            ],
        )
        for category, components in sorted(categories.items(), key=lambda pair: pair[0].casefold())
    ]


def fenced_block(language: str, content: str) -> list[str]:
    return [f"```{language}", content.rstrip(), "```"]


def classification_pseudocode(finding: dict[str, Any]) -> str:
    mappings = finding["mappings"]
    standards = mappings["owasp"] + mappings["apiTop10"] + mappings["cwe"]
    return "\n".join([
        f"type: {finding['classification']}",
        f"status: {finding['status']}",
        f"severity: {finding['severity']}",
        f"confidence: {finding['confidence']}",
        f"standards: [{', '.join(standards)}]",
    ])


def implementation_pseudocode(finding: dict[str, Any]) -> str:
    affected = finding["affectedImplementation"]
    lines = [f"component: {finding['component']}"]
    labels = {
        "controllers": "controllers",
        "classes": "classes",
        "methods": "methods",
        "endpoints": "endpoints",
        "filesOrArtifacts": "files_or_artifacts",
    }
    for key, label in labels.items():
        lines.append(f"{label}: [{', '.join(affected[key])}]")
    return "\n".join(lines)


def verification_pseudocode(finding: dict[str, Any]) -> str:
    return "\n".join(
        f"{test['type'].upper()}: {test['description']} => {test['expected']}"
        for test in finding["regressionTests"]
    )


def authorization_path_pseudocode(
    finding: dict[str, Any], access_paths_by_id: dict[str, dict[str, Any]]
) -> str:
    lines: list[str] = []
    for path_id in finding["accessPathIds"]:
        access_path = access_paths_by_id[path_id]
        if lines:
            lines.append("")
        lines.append(f"{path_id} [{access_path['traceStatus']}]")
        for tier in access_path["tiers"]:
            authority = ", ".join(tier["credentials"] + tier["policies"]) or "no authority input recorded"
            lines.append(
                f"  -> {tier['component']} / {tier['name']} | {tier['entryIdentity']} -> "
                f"{tier['exitIdentity']} | {authority} | {tier['decision']}"
            )
    return "\n".join(lines)


def _render_legacy_markdown_report(data: dict[str, Any]) -> str:
    assessment = data["assessment"]
    model = data["authorizationModel"]
    coverage = data["coverage"]
    findings = data["findings"]
    gaps = data["gaps"]
    access_paths_by_id = {item["id"]: item for item in model["accessPaths"]}
    counts = Counter(item["status"] for item in coverage)

    lines: list[str] = [
        f"# {md(assessment['title'])}",
        "",
        "## Executive summary",
        "",
        md(assessment["summary"]),
        "",
        f"- **Subject:** {md(assessment['subject'])}",
        f"- **Revision/build:** `{md(assessment['revision'])}`",
        f"- **Environment:** {md(assessment['environment'])}",
        f"- **Assessment date:** {md(assessment['assessmentDate'])}",
        f"- **Profile:** {md(assessment['profile'])}",
        f"- **Evidence mode:** {md(assessment['authorizationMode'])}",
        f"- **Findings:** {len(findings)}",
        f"- **Coverage:** {counts['finding']} finding, {counts['reviewed-no-finding']} reviewed without finding, "
        f"{counts['not-applicable']} not applicable, {counts['not-assessed']} not assessed",
        "",
        "This is an OWASP A01:2025 assessment only; OWASP A02–A10 were not comprehensively assessed.",
        "",
        "## Scope and authority",
        "",
        "### In scope",
        "",
        *bullet_lines(assessment["scope"]),
        "",
        "### Authorized live targets",
        "",
        *bullet_lines(assessment["authorizedTargets"]),
        "",
        "### Exclusions",
        "",
        *bullet_lines(assessment["exclusions"]),
        "",
        "### Limitations",
        "",
        *bullet_lines(assessment["limitations"]),
        "",
        "## Authorization model",
        "",
    ]
    model_labels = {
        "actors": "Actors",
        "resources": "Resources",
        "actions": "Actions",
        "contexts": "Contexts",
        "enforcementPoints": "Trusted enforcement points",
        "policyStatements": "Expected policy statements",
    }
    for key in MODEL_FIELDS:
        lines.extend([f"### {model_labels[key]}", "", *bullet_lines(model[key]), ""])

    lines.extend(["### Access-path inventory", ""])
    if model["accessPaths"]:
        lines.extend([
            "| ID | Trace | Entry point | Method/operation | Channel | Authentication | Resource/action | Enforcement chain |",
            "|---|---|---|---|---|---|---|---|",
        ])
        for access_path in model["accessPaths"]:
            resource_action = f"{access_path['resource']} — {', '.join(access_path['actions'])}"
            lines.append(
                f"| `{md(access_path['id'])}` | {md(access_path['traceStatus'])} | {md(access_path['entryPoint'])} | "
                f"{md(', '.join(access_path['methodsOrOperations']))} | {md(access_path['channel'])} | "
                f"{md(access_path['authentication'])} | {md(resource_action)} | "
                f"{md(' → '.join(tier['name'] for tier in access_path['tiers']))} |"
            )
        lines.append("")
        for access_path in model["accessPaths"]:
            lines.extend([
                f"#### End-to-end tiers for {md(access_path['id'])}",
                "",
                f"**Trace status:** {md(access_path['traceStatus'])}",
                "",
                f"**Inputs and authority vectors:** "
                f"{', '.join(f'`{md(value)}`' for value in access_path['inputVectors'])}",
                "",
            ])
            for tier in access_path["tiers"]:
                lines.extend([
                    f"##### {md(tier['name'])} — {md(tier['component'])}",
                    "",
                    f"- **Type/status:** {md(tier['type'])} / {md(tier['status'])}",
                    f"- **Identity:** {md(tier['entryIdentity'])} → {md(tier['exitIdentity'])}",
                    f"- **Credentials:** {md(', '.join(tier['credentials']) or 'None')}",
                    f"- **Policies:** {md(', '.join(tier['policies']) or 'None')}",
                    f"- **Resource context:** {md(', '.join(tier['resourceContext']) or 'None')}",
                    f"- **Decision:** {md(tier['decision'])}",
                    "",
                    *render_evidence(tier["evidence"]),
                    "",
                ])
            lines.extend(["**Path evidence**", "", *render_evidence(access_path["evidence"]), ""])
    else:
        lines.extend(["No access paths recorded.", ""])

    groups = grouped_findings(findings)
    lines.extend(["## Findings summary", ""])
    if findings:
        lines.append("Findings are organized by primary access-control category and owning component.")
        lines.append("")
        for category, components in groups:
            lines.extend([
                f"### Category: {md(category)}",
                "",
                "| Issue | Severity | Status |",
                "|---|---|---|",
            ])
            for _, component_findings in components:
                for finding in component_findings:
                    lines.append(
                        f"| {md(finding['id'])}: {md(finding['title'])} | "
                        f"{md(finding['severity'])} | {md(finding['status'])} |"
                    )
            lines.append("")
    else:
        lines.extend(["No findings recorded. This does not imply complete coverage; see the coverage matrix and gaps.", ""])

    if findings:
        lines.extend(["## Detailed findings", ""])
    for category, components in groups:
        lines.extend([f"### Category: {md(category)}", ""])
        for component, component_findings in components:
            lines.extend([f"#### Component: {md(component)}", ""])
            for finding in component_findings:
                mappings = finding["mappings"]
                lines.extend([
                    f"##### {md(finding['id'])}: {md(finding['title'])}",
                    "",
                    md(finding["summary"]),
                    "",
                    "**Classification**",
                    "",
                    *fenced_block("yaml", classification_pseudocode(finding)),
                    "",
                    "**Affected implementation**",
                    "",
                    *fenced_block("yaml", implementation_pseudocode(finding)),
                    "",
                    "Evidence anchors: " + ", ".join(f"`{md(item['location'])}`" for item in finding["evidence"]),
                    "",
                    "**End-to-end authorization path**",
                    "",
                    *fenced_block("text", authorization_path_pseudocode(finding, access_paths_by_id)),
                    "",
                ])
                for heading, key in (
                    ("Expected access rule", "expectedAccessRule"),
                    ("Unauthorized scenario", "exercise"),
                    ("Why the check fails", "failureProof"),
                    ("What could happen", "impact"),
                    ("Recommended resolution", "remediation"),
                ):
                    block = finding[key]
                    lines.extend([
                        f"**{heading}**",
                        "",
                        md(block["summary"]),
                        "",
                        *fenced_block(block["language"], block["pseudocode"]),
                        "",
                    ])
                lines.extend([
                    "**How to verify the fix**",
                    "",
                    *fenced_block("text", verification_pseudocode(finding)),
                    "",
                    "<details><summary>Technical evidence, attack path, severity rationale, mappings, and limitations</summary>",
                    "",
                    "**Attack path**",
                    "",
                ])
                for index, step in enumerate(finding["attackPath"], start=1):
                    lines.append(f"{index}. {md(step)}")
                lines.extend([
                    "",
                    "**Evidence**",
                    "",
                    *render_evidence(finding["evidence"]),
                    "",
                    f"**Severity rationale:** {md(finding['severityRationale'])}",
                    "",
                    f"- **Actor:** {md(finding['actor'])}",
                    f"- **Resource:** {md(finding['resource'])}",
                    f"- **Action:** {md(finding['action'])}",
                    f"- **Coverage:** {', '.join(f'`{md(value)}`' for value in finding['coverageIds'])}",
                    f"- **OWASP:** {', '.join(f'`{md(value)}`' for value in mappings['owasp']) or 'None'}",
                    f"- **ASVS:** {', '.join(f'`{md(value)}`' for value in mappings['asvs']) or 'None'}",
                    f"- **WSTG:** {', '.join(f'`{md(value)}`' for value in mappings['wstg']) or 'None'}",
                    f"- **API Security:** {', '.join(f'`{md(value)}`' for value in mappings['apiTop10']) or 'None'}",
                    f"- **CWE:** {', '.join(f'`{md(value)}`' for value in mappings['cwe']) or 'None'}",
                    "",
                    "**Finding limitations**",
                    "",
                    *bullet_lines(finding["limitations"]),
                    "",
                    "</details>",
                    "",
                ])

    lines.extend([
        "## A01 coverage matrix",
        "",
        "| Branch | Review area | Status | Rationale | Findings |",
        "|---|---|---|---|---|",
    ])
    for item in coverage:
        finding_ids = ", ".join(item["findingIds"]) or "—"
        lines.append(
            f"| `{md(item['id'])}` | {md(COVERAGE_NAMES[item['id']])} | {md(item['status'])} | "
            f"{md(item['rationale'])} | {md(finding_ids)} |"
        )
    lines.append("")
    for item in coverage:
        if item["evidence"]:
            lines.extend([
                f"#### Evidence for {md(item['id'])}",
                "",
                *render_evidence(item["evidence"]),
                "",
            ])

    lines.extend(["## Gaps and next steps", ""])
    if gaps:
        for gap in gaps:
            lines.extend([
                f"### {md(gap['id'])}: {md(gap['title'])}",
                "",
                f"**Why it matters:** {md(gap['whyItMatters'])}",
                "",
                f"**Request status:** {md(gap['requestStatus'])}",
                "",
                f"**User direction:** {md(gap['userDecision'])}",
                "",
                f"**Affected paths:** {', '.join(f'`{md(value)}`' for value in gap['accessPathIds']) or 'None recorded'}",
                "",
                f"**Affected coverage:** {', '.join(f'`{md(value)}`' for value in gap['coverageIds'])}",
                "",
                "**Searched or inspected:**",
                "",
                *bullet_lines(gap["searched"]),
                "",
                "**Requested artifacts or access:**",
                "",
                *bullet_lines(gap["requestedArtifacts"]),
                "",
                "**Blocked conclusions:**",
                "",
                *bullet_lines(gap["blockedConclusions"]),
                "",
                f"**Safe next step:** {md(gap['nextStep'])}",
                "",
            ])
    else:
        lines.extend(["No unresolved coverage gaps recorded.", ""])

    lines.extend([
        "## Framework statement",
        "",
        "This report uses OWASP Top 10 A01:2025 as its risk taxonomy, OWASP ASVS 5.0.0 V8 for current verification requirements "
        "with ASVS 4.0.3 V4 legacy mappings when requested, OWASP WSTG 4.2 authorization tests for reproducible test design, "
        "the OWASP Authorization Cheat Sheet for implementation guidance, "
        "and OWASP API Security Top 10:2023 where applicable. A01 coverage does not constitute an A02–A10 assessment or automatic ASVS certification.",
        "",
    ])
    return "\n".join(lines)


def render_report(data: dict[str, Any], output_format: str = "markdown") -> str:
    """Render a validated assessment as navigable Markdown or standalone HTML."""
    if output_format == "markdown":
        return render_markdown_report(data, _render_legacy_markdown_report(data))
    if output_format == "html":
        return render_html_report(data, COVERAGE_NAMES)
    raise ValueError(f"unsupported report format: {output_format}")


def command_validate(path: Path) -> int:
    data = load_json(path)
    errors = validate_assessment(data)
    if errors:
        print(f"INVALID: {path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"VALID: {path}")
    return 0


def command_render(
    path: Path, output: Path, output_format: str = "auto", *, allow_blocked: bool = False
) -> int:
    data = load_json(path)
    errors = validate_assessment(data)
    if errors:
        print(f"INVALID: {path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    awaiting_gaps = [gap for gap in data["gaps"] if gap.get("requestStatus") == "awaiting-user"]
    if awaiting_gaps and not allow_blocked:
        gap_ids = ", ".join(gap["id"] for gap in awaiting_gaps)
        print(
            f"BLOCKED: user direction is required for {gap_ids}; do not render a final report. "
            "Use --allow-blocked only when the user explicitly requests an interim checkpoint report.",
            file=sys.stderr,
        )
        return 3
    try:
        selected_format = resolve_output_format(output, output_format)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(data, selected_format), encoding="utf-8", newline="\n")
    print(f"RENDERED {selected_format.upper()}: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate an assessment JSON file")
    validate_parser.add_argument("assessment", type=Path)
    render_parser = subparsers.add_parser("render", help="validate and render a navigable Markdown or standalone HTML report")
    render_parser.add_argument("assessment", type=Path)
    render_parser.add_argument("--output", type=Path, required=True)
    render_parser.add_argument(
        "--format",
        choices=("auto", "md", "markdown", "html"),
        default="auto",
        help="report format; md is an alias for markdown, and auto infers from the output extension",
    )
    render_parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="render an explicitly requested interim checkpoint even when material gaps await user direction",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            return command_validate(args.assessment)
        return command_render(args.assessment, args.output, args.format, allow_blocked=args.allow_blocked)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

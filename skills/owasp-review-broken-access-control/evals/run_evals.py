#!/usr/bin/env python3
"""Deterministic integrity checks for the A01 skill and its bundled contract."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "bac_assessment.py"
SPEC = importlib.util.spec_from_file_location("bac_assessment", SCRIPT)
assert SPEC and SPEC.loader
bac = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bac)


def fail(message: str) -> None:
    raise AssertionError(message)


def read(relative: str) -> str:
    path = SKILL_DIR / relative
    if not path.exists():
        fail(f"missing required file: {relative}")
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.find(heading)
    if start < 0:
        fail(f"missing section: {heading}")
    if next_heading is None:
        return text[start:]
    end = text.find(next_heading, start + len(heading))
    if end < 0:
        fail(f"missing section boundary: {next_heading}")
    return text[start:end]


def main() -> int:
    skill = read("SKILL.md")
    source = read("references/owasp-a01-source-of-truth.md")
    crosswalk = read("references/asvs-wstg-cheatsheet-crosswalk.md")
    wstg_selection = read("references/wstg-v42-a01-selection.md")
    playbook = read("references/review-playbook.md")
    contract = read("references/report-contract.md")
    metadata = json.loads(read("metadata.json"))
    template = json.loads(read("assets/assessment-template.json"))
    access_path_template = json.loads(read("assets/access-path-template.json"))
    finding_template = json.loads(read("assets/finding-template.json"))
    end_to_end = read("references/end-to-end-authorization-tracing.md")
    architecture_profiles = read("references/architecture-profiles.md")
    evals = json.loads(read("evals/evals.json"))

    if len(skill.splitlines()) >= 500:
        fail("SKILL.md must remain below 500 lines for progressive disclosure")

    for relative in (
        "references/owasp-a01-source-of-truth.md",
        "references/asvs-wstg-cheatsheet-crosswalk.md",
        "references/wstg-v42-a01-selection.md",
        "references/review-playbook.md",
        "references/report-contract.md",
        "references/end-to-end-authorization-tracing.md",
        "references/architecture-profiles.md",
        "assets/assessment-template.json",
        "assets/access-path-template.json",
        "assets/finding-template.json",
        "scripts/bac_assessment.py",
        "scripts/report_renderers.py",
        "evals/evals.json",
    ):
        if relative not in skill:
            fail(f"SKILL.md does not link required resource: {relative}")

    required_urls = (
        "https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/",
        "https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/en/0x17-V8-Authorization.md",
        "https://github.com/OWASP/ASVS/blob/v4.0.3/4.0/en/0x12-V4-Access-Control.md",
        "https://owasp.org/www-project-web-security-testing-guide/v42/",
        "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html",
        "https://owasp.org/API-Security/editions/2023/en/0x11-t10/",
    )
    for url in required_urls:
        if url not in source:
            fail(f"source-of-truth reference omits official URL: {url}")

    for branch_id in bac.REQUIRED_COVERAGE_IDS:
        if branch_id not in skill:
            # The skill uses ranges for the two families, so allow IDs to be carried by linked references.
            if branch_id not in source or branch_id not in playbook:
                fail(f"required A01 branch is not documented: {branch_id}")
        elif branch_id not in source or branch_id not in playbook:
            fail(f"required A01 branch is not consistently documented: {branch_id}")

    source_cwe_section = section(source, "## All 40 CWEs mapped by A01:2025")
    source_cwes = set(re.findall(r"CWE-\d+", source_cwe_section))
    if source_cwes != bac.OFFICIAL_CWES:
        fail(
            "source-of-truth CWE set differs from the official A01 set: "
            f"missing={sorted(bac.OFFICIAL_CWES - source_cwes)}, extra={sorted(source_cwes - bac.OFFICIAL_CWES)}"
        )

    grouped = section(playbook, "## Coverage of all 40 A01 CWEs", "## Static-review heuristics")
    grouped_cwes = set(re.findall(r"CWE-\d+", grouped))
    if grouped_cwes != bac.OFFICIAL_CWES:
        fail(
            "playbook coverage groups do not account for exactly all 40 A01 CWEs: "
            f"missing={sorted(bac.OFFICIAL_CWES - grouped_cwes)}, extra={sorted(grouped_cwes - bac.OFFICIAL_CWES)}"
        )

    template_errors = bac.validate_assessment(template)
    if template_errors:
        fail("assessment template does not validate:\n- " + "\n- ".join(template_errors))

    template_ids = tuple(item["id"] for item in template["coverage"])
    if template_ids != bac.REQUIRED_COVERAGE_IDS:
        fail("assessment template coverage order or branch set differs from the contract")

    if "A02–A10" not in skill or "A02–A10" not in contract:
        fail("skill and report contract must state that A02-A10 are outside this version's scope")
    for required_report_term in (
        "standalone HTML", "Markdown", "Table of contents", "PASS", "FAIL", "REVIEW",
        "COMPLETE", "PARTIAL", "BLOCKED", "End-to-end authorization path",
    ):
        if required_report_term.lower() not in skill.lower() or required_report_term.lower() not in contract.lower():
            fail(f"skill and report contract must document human-report behavior: {required_report_term}")

    for required_scope_term in (
        "Scope eligibility gate", "Bounded structure-first pass", "candidate", "supporting evidence",
        "excluded", "undetermined", "client-only SPA/MFE", "do not enumerate every file",
        "do not generate a full assessment", "Deep-review candidates only",
    ):
        if required_scope_term.lower() not in skill.lower():
            fail(f"skill omits scope-efficiency behavior: {required_scope_term}")
    for required_trace_term in (
        "heavy-lifting discovery", "entryIdentity", "exitIdentity", "awaiting-user", "wait for user direction",
    ):
        if required_trace_term.lower() not in end_to_end.lower() and required_trace_term.lower() not in skill.lower():
            fail(f"end-to-end tracing guidance omits required behavior: {required_trace_term}")
    if "selected candidate scope" not in end_to_end.lower() or "excluded repositories" not in end_to_end.lower():
        fail("end-to-end discovery must remain bounded to selected candidates and material supporting paths")
    for required_profile_term in (
        "architecture-neutral", "Azure API Management", "BFF", "API and subscription keys",
        "Microservices", "Serverless and event-driven",
    ):
        if required_profile_term.lower() not in architecture_profiles.lower():
            fail(f"architecture profiles omit required conditional coverage: {required_profile_term}")

    required_path_fields = {
        "id", "entryPoint", "methodsOrOperations", "channel", "authentication", "actors", "resource", "actions",
        "inputVectors", "traceStatus", "gapIds", "tiers", "evidence",
    }
    if not required_path_fields.issubset(access_path_template):
        fail(f"access-path template omits fields: {sorted(required_path_fields - set(access_path_template))}")
    required_finding_fields = {"category", "component", "classification", "accessPathIds", "affectedImplementation"}
    if not required_finding_fields.issubset(finding_template):
        fail(f"finding template omits fields: {sorted(required_finding_fields - set(finding_template))}")

    if not re.fullmatch(r"\d+\.\d+\.\d+", str(metadata.get("skillVersion", ""))):
        fail("metadata skillVersion must use semantic version form")
    if metadata.get("assessmentSchemaVersion") != bac.SCHEMA_VERSION:
        fail("metadata assessmentSchemaVersion does not match the validator")
    if metadata.get("evalSuiteVersion") != evals.get("eval_suite_version"):
        fail("metadata evalSuiteVersion does not match evals.json")
    metadata_source = metadata.get("sourceProfile", {})
    if metadata_source.get("wstgTagCommit") != "dd33419e10edb22b78d89325a6c2aad9f184e3a2":
        fail("metadata must pin the reviewed WSTG v4.2 commit")
    for relative in metadata.get("runtime", []):
        runtime_path = SKILL_DIR / relative.rstrip("/")
        if not runtime_path.exists():
            fail(f"metadata runtime path does not exist: {relative}")
    for relative in metadata.get("development", []):
        development_path = SKILL_DIR / relative.rstrip("/")
        if not development_path.exists():
            fail(f"metadata development path does not exist: {relative}")

    if evals.get("skill_name") != "owasp-review-broken-access-control":
        fail("eval skill_name does not match SKILL.md")
    if evals.get("skill_contract_version") != bac.SCHEMA_VERSION:
        fail("eval skill_contract_version does not match the assessment schema")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(evals.get("eval_suite_version", ""))):
        fail("eval_suite_version must use semantic version form")
    source_profile = evals.get("source_profile")
    if not isinstance(source_profile, dict) or source_profile.get("owasp_top10") != "A01:2025":
        fail("eval source_profile must pin A01:2025")
    cases = evals.get("evals")
    if not isinstance(cases, list) or len(cases) < 3:
        fail("at least three behavioral evals are required")
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        fail("behavioral eval IDs must be unique")
    official_scenarios = {
        "owasp-a01-scenario-1-account-idor",
        "owasp-a01-scenario-2-force-browsing",
        "owasp-a01-scenario-3-client-only-control",
    }
    if not official_scenarios.issubset(set(ids)):
        fail("behavioral evals must include all three official A01:2025 attack scenarios")
    scope_scenarios = {
        "scope-excluded-static-public-site",
        "scope-client-only-mfe-supporting-not-enforcement",
        "scope-mixed-portfolio-selective-deep-review",
    }
    if not scope_scenarios.issubset(set(ids)):
        fail("behavioral evals must cover excluded static, supporting MFE, and selective portfolio triage")
    enterprise_scenarios = {
        "enterprise-apim-bff-application-identity-loss",
        "enterprise-missing-effective-gateway-policy-checkpoint",
        "architecture-neutral-event-driven-delegation",
    }
    if not enterprise_scenarios.issubset(set(ids)):
        fail("behavioral evals must cover layered enterprise, missing-evidence, and non-APIM architectures")
    for case in cases:
        provenance = case.get("provenance")
        if not isinstance(provenance, dict):
            fail(f"eval {case.get('id')} has no provenance")
        for key in ("source", "url", "adaptation"):
            if not isinstance(provenance.get(key), str) or not provenance[key].strip():
                fail(f"eval {case.get('id')} provenance has no {key}")
        for key in ("prompt", "expected_output"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                fail(f"eval {case.get('id')} has no {key}")
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or len(assertions) < 3:
            fail(f"eval {case.get('id')} needs at least three assertions")
        files = case.get("files")
        if not isinstance(files, list) or any(not isinstance(value, str) or not value.strip() for value in files):
            fail(f"eval {case.get('id')} files must be an array of paths")
        for relative in files:
            if not (SKILL_DIR / relative).is_file():
                fail(f"eval {case.get('id')} references missing fixture: {relative}")

    file_backed_cases = [case for case in cases if case.get("files")]
    if len(file_backed_cases) < 2:
        fail("at least two behavioral evals must use repository-style fixture files")

    selected_wstg_ids = {
        "WSTG-INFO-06", "WSTG-INFO-07", "WSTG-INFO-10",
        "WSTG-CONF-03", "WSTG-CONF-04", "WSTG-CONF-05", "WSTG-CONF-06", "WSTG-CONF-09", "WSTG-CONF-11",
        "WSTG-IDNT-01", "WSTG-IDNT-03", "WSTG-ATHN-04", "WSTG-ATHN-10",
        "WSTG-ATHZ-01", "WSTG-ATHZ-02", "WSTG-ATHZ-03", "WSTG-ATHZ-04",
        "WSTG-SESS-01", "WSTG-SESS-02", "WSTG-SESS-05", "WSTG-SESS-06", "WSTG-SESS-07",
        "WSTG-INPV-03", "WSTG-INPV-04", "WSTG-INPV-19", "WSTG-ERRH-01",
        "WSTG-BUSL-02", "WSTG-BUSL-03", "WSTG-BUSL-05", "WSTG-BUSL-06", "WSTG-BUSL-07",
        "WSTG-CLNT-07", "WSTG-CLNT-12", "WSTG-APIT-01",
    }
    documented_wstg_ids = set(re.findall(r"WSTG-[A-Z]+-\d+", wstg_selection))
    if documented_wstg_ids != selected_wstg_ids:
        fail(
            "WSTG A01 selection drifted: "
            f"missing={sorted(selected_wstg_ids - documented_wstg_ids)}, "
            f"extra={sorted(documented_wstg_ids - selected_wstg_ids)}"
        )
    if "dd33419e10edb22b78d89325a6c2aad9f184e3a2" not in wstg_selection:
        fail("WSTG A01 selection must pin the v4.2 tag commit")

    print(
        f"PASS: skill {metadata['skillVersion']}, schema {metadata['assessmentSchemaVersion']}, and "
        f"eval suite {metadata['evalSuiteVersion']} metadata agree"
    )
    print("PASS: skill links all required resources")
    print("PASS: bounded eligibility triage excludes irrelevant repositories before deep discovery")
    print("PASS: end-to-end evidence gate, architecture-neutral profiles, and tiered templates are documented")
    print("PASS: all 8 vulnerability and 11 prevention branches are documented")
    print("PASS: source and playbook account for exactly all 40 A01:2025 CWEs")
    print("PASS: assessment template validates and preserves coverage order")
    for requirement in ("4.1.1", "4.1.2", "4.1.3", "4.1.5", "4.2.1", "4.2.2", "4.3.1", "4.3.2", "4.3.3"):
        if requirement not in crosswalk:
            fail(f"ASVS 4.0.3 crosswalk omits active V4 requirement {requirement}")
    for recommendation in (
        "least privilege", "Deny by default", "every request", "static resources", "correct location",
        "Log access-control events", "unit and integration tests",
    ):
        if recommendation.lower() not in crosswalk.lower():
            fail(f"Authorization Cheat Sheet crosswalk omits recommendation: {recommendation}")

    print(f"PASS: WSTG v4.2 selection pins and documents {len(selected_wstg_ids)} relevant test IDs")
    print(
        f"PASS: eval suite {evals['eval_suite_version']} has {len(cases)} cases with source provenance, "
        f"including {len(file_backed_cases)} file-backed cases"
    )
    print("PASS: all three official A01 attack scenarios are canonical behavioral evals")
    print("PASS: scope evals cover static exclusion, MFE handoff, and selective multi-repository expansion")
    print("PASS: enterprise evals cover APIM/BFF, evidence checkpoints, and architecture-neutral delegation")
    print("PASS: ASVS 4.0.3, ASVS 5.0.0, WSTG 4.2, and Cheat Sheet crosswalk is present")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Dependency-free preflight validation for architecture skill A/B configs."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

HARNESS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ROOT = HARNESS_ROOT.parents[1]
ARCHITECTURE_FAMILIES = {"monolith", "modular-monolith", "microservices", "event-driven", "mixed", "unknown"}
REQUESTED_VIEWS = {"structural-topology", "logical", "deployment", "sequence", "impact", "event-topology", "state", "er", "class", "format-fit"}
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", "clock$", *(f"com{number}" for number in range(1, 10)), *(f"lpt{number}" for number in range(1, 10))}
REQUIRED_CONTROLS = {
    "same_model",
    "same_system_instructions",
    "same_prompt",
    "same_evidence",
    "same_tool_policy",
    "fresh_session",
    "isolated_candidate_skills",
}


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _validate_finite(value: Any, field: str = "configuration") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field}: non-finite number is not allowed")
    if isinstance(value, dict):
        for key, child in value.items():
            _validate_finite(child, f"{field}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_finite(child, f"{field}[{index}]")


def is_safe_id(value: Any) -> bool:
    return isinstance(value, str) and bool(SAFE_ID.fullmatch(value)) and not value.endswith((".", " ")) and value.split(".", 1)[0].lower() not in WINDOWS_RESERVED


def _reject_unknown(value: dict[str, Any], allowed: set[str], field: str, errors: list[str]) -> None:
    unknown = set(value) - allowed
    if unknown:
        errors.append(f"{field}: unknown fields: {sorted(unknown)}")


def _repo_path(repo_root: Path, value: str, field: str, errors: list[str]) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        errors.append(f"{field}: path must be repository-relative: {value}")
    resolved = (repo_root / raw).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        errors.append(f"{field}: path escapes repository root: {value}")
    return resolved


def _nonempty_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field}: must be a non-empty array")
        return []
    return value


def validate(config_path: Path, repo_root: Path = DEFAULT_REPO_ROOT) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read configuration: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("configuration root must be an object")
    _validate_finite(config)
    _reject_unknown(config, {"schema_version", "benchmark_id", "domain", "description", "candidates", "execution", "evaluation", "cases"}, "configuration", errors)
    missing_root = {"schema_version", "benchmark_id", "domain", "candidates", "execution", "evaluation", "cases"} - set(config)
    if missing_root:
        errors.append(f"configuration: missing fields: {sorted(missing_root)}")
    if "description" in config and not isinstance(config["description"], str):
        errors.append("description: must be a string")
    if config.get("schema_version") != 1:
        errors.append("schema_version: expected 1")
    if config.get("domain") != "architecture":
        errors.append("domain: expected 'architecture'")
    if not is_safe_id(config.get("benchmark_id")):
        errors.append("benchmark_id: must be a safe lowercase ID (letters, digits, dot, underscore, hyphen; max 64)")

    candidates = config.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != {"A", "B"}:
        errors.append("candidates: must contain exactly slots A and B")
        candidates = {}
    candidate_ids: list[str] = []
    for slot in ("A", "B"):
        candidate = candidates.get(slot, {})
        if not isinstance(candidate, dict):
            errors.append(f"candidates.{slot}: must be an object")
            continue
        _reject_unknown(candidate, {"id", "revision", "description", "skill_paths", "authoritative_source_patterns", "artifact_patterns", "native_viewer", "viewer_command", "viewer_checks", "renderer", "validation_commands"}, f"candidates.{slot}", errors)
        candidate_id = candidate.get("id")
        if not is_safe_id(candidate_id):
            errors.append(f"candidates.{slot}.id: must be a safe lowercase ID (max 64)")
        else:
            candidate_ids.append(candidate_id)
        if not isinstance(candidate.get("revision"), str) or not candidate.get("revision", "").strip():
            errors.append(f"candidates.{slot}.revision: must be a non-empty pinned revision")
        skill_paths = _nonempty_list(candidate.get("skill_paths"), f"candidates.{slot}.skill_paths", errors)
        if len(skill_paths) != len(set(value for value in skill_paths if isinstance(value, str))):
            errors.append(f"candidates.{slot}.skill_paths: paths must be unique")
        for index, skill_path in enumerate(skill_paths):
            if not isinstance(skill_path, str) or not skill_path:
                errors.append(f"candidates.{slot}.skill_paths[{index}]: must be a non-empty string")
                continue
            path = _repo_path(repo_root, skill_path, f"candidates.{slot}.skill_paths[{index}]", errors)
            if not (path / "SKILL.md").is_file():
                errors.append(f"candidates.{slot}.skill_paths[{index}]: no SKILL.md at {skill_path}")
        if "description" in candidate and not isinstance(candidate["description"], str):
            errors.append(f"candidates.{slot}.description: must be a string")
        for field in ("authoritative_source_patterns", "artifact_patterns"):
            values = _nonempty_list(candidate.get(field), f"candidates.{slot}.{field}", errors)
            if any(not isinstance(value, str) or not value for value in values):
                errors.append(f"candidates.{slot}.{field}: every pattern must be a non-empty string")
            for value in values:
                if isinstance(value, str) and (Path(value).is_absolute() or ".." in Path(value).parts):
                    errors.append(f"candidates.{slot}.{field}: patterns must be run-relative and cannot contain '..'")
            if len(values) != len(set(value for value in values if isinstance(value, str))):
                errors.append(f"candidates.{slot}.{field}: patterns must be unique")
        if not isinstance(candidate.get("native_viewer"), str) or not candidate.get("native_viewer", "").strip():
            errors.append(f"candidates.{slot}.native_viewer: must be a non-empty string")
        if not isinstance(candidate.get("viewer_command"), str) or not candidate.get("viewer_command", "").strip():
            errors.append(f"candidates.{slot}.viewer_command: must be a non-empty pinned command")
        viewer_checks = _nonempty_list(candidate.get("viewer_checks"), f"candidates.{slot}.viewer_checks", errors)
        if any(not is_safe_id(value) for value in viewer_checks) or len(viewer_checks) != len(set(value for value in viewer_checks if isinstance(value, str))):
            errors.append(f"candidates.{slot}.viewer_checks: checks must be unique safe lowercase IDs")
        renderer = candidate.get("renderer")
        if renderer is not None:
            if not isinstance(renderer, dict) or set(renderer) != {"name", "version", "command"} or any(not isinstance(value, str) or not value for value in renderer.values()):
                errors.append(f"candidates.{slot}.renderer: must be null or contain non-empty name, version, and command strings")
        commands = candidate.get("validation_commands")
        if not isinstance(commands, list) or any(not isinstance(command, str) or not command for command in commands):
            errors.append(f"candidates.{slot}.validation_commands: must be an array of non-empty strings")
    if len(candidate_ids) == 2 and candidate_ids[0] == candidate_ids[1]:
        errors.append("candidates A and B must have distinct ids")

    execution = config.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution: must be an object")
        execution = {}
    _reject_unknown(execution, {"phase", "replicates", "model", "seed_policy", "system_instructions_sha256", "tool_policy_sha256", "controls", "budgets"}, "execution", errors)
    phase = execution.get("phase")
    if phase not in {"historical-pilot", "calibration", "confirmatory"}:
        errors.append("execution.phase: expected historical-pilot, calibration, or confirmatory")
    replicates = execution.get("replicates")
    if not isinstance(replicates, int) or isinstance(replicates, bool) or replicates < 1:
        errors.append("execution.replicates: must be an integer >= 1")
    if not isinstance(execution.get("model"), str) or not execution.get("model", "").strip():
        errors.append("execution.model: must pin a non-empty model/version identifier")
    if not isinstance(execution.get("seed_policy"), str) or not execution.get("seed_policy", "").strip():
        errors.append("execution.seed_policy: must be a non-empty pinned policy")
    for field in ("system_instructions_sha256", "tool_policy_sha256"):
        if not isinstance(execution.get(field), str) or not execution.get(field, "").strip():
            errors.append(f"execution.{field}: must be a non-empty pinned digest or historical marker")
    controls = execution.get("controls")
    if not isinstance(controls, dict) or set(controls) != REQUIRED_CONTROLS or any(not isinstance(value, bool) for value in controls.values()):
        errors.append("execution.controls: must contain exactly the seven boolean fairness controls")
        controls = {}
    budgets = execution.get("budgets")
    if not isinstance(budgets, dict):
        errors.append("execution.budgets: must be an object")
        budgets = {}
    _reject_unknown(budgets, {"equal_across_candidates", "max_total_tokens", "max_wall_time_seconds", "max_tool_calls"}, "execution.budgets", errors)
    budget_fields = ("max_total_tokens", "max_wall_time_seconds", "max_tool_calls")
    if not isinstance(budgets.get("equal_across_candidates"), bool):
        errors.append("execution.budgets.equal_across_candidates: must be boolean")
    for field in budget_fields:
        value = budgets.get(field)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
            errors.append(f"execution.budgets.{field}: must be null or an integer >= 1")

    evaluation = config.get("evaluation")
    if not isinstance(evaluation, dict):
        errors.append("evaluation: must be an object")
        evaluation = {}
    _reject_unknown(evaluation, {"rubric_path", "judge_count", "blind_candidate_identity", "randomize_order_per_judge", "gold_adjudicators"}, "evaluation", errors)
    rubric_path = evaluation.get("rubric_path")
    if not isinstance(rubric_path, str) or not rubric_path:
        errors.append("evaluation.rubric_path: must be a non-empty string")
    elif not _repo_path(repo_root, rubric_path, "evaluation.rubric_path", errors).is_file():
        errors.append(f"evaluation.rubric_path: file not found: {rubric_path}")
    for field in ("judge_count", "gold_adjudicators"):
        value = evaluation.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"evaluation.{field}: must be an integer >= 1")
    for field in ("blind_candidate_identity", "randomize_order_per_judge"):
        if not isinstance(evaluation.get(field), bool):
            errors.append(f"evaluation.{field}: must be boolean")

    cases = _nonempty_list(config.get("cases"), "cases", errors)
    case_ids: set[str] = set()
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        _reject_unknown(case, {"id", "architecture_family", "requested_view", "evidence_paths", "prompt", "gold_path", "confirmation_eligible", "notes"}, prefix, errors)
        case_id = case.get("id")
        if not is_safe_id(case_id):
            errors.append(f"{prefix}.id: must be a safe lowercase filesystem ID (max 64)")
        elif case_id in case_ids:
            errors.append(f"{prefix}.id: duplicate id {case_id}")
        else:
            case_ids.add(case_id)
        if case.get("architecture_family") not in ARCHITECTURE_FAMILIES:
            errors.append(f"{prefix}.architecture_family: unsupported value")
        if case.get("requested_view") not in REQUESTED_VIEWS:
            errors.append(f"{prefix}.requested_view: unsupported value")
        if not isinstance(case.get("prompt"), str) or not case.get("prompt", "").strip():
            errors.append(f"{prefix}.prompt: must be a non-empty string")
        if not isinstance(case.get("confirmation_eligible"), bool):
            errors.append(f"{prefix}.confirmation_eligible: must be boolean")
        if "notes" in case and not isinstance(case["notes"], str):
            errors.append(f"{prefix}.notes: must be a string")
        for evidence_index, evidence_path in enumerate(_nonempty_list(case.get("evidence_paths"), f"{prefix}.evidence_paths", errors)):
            if not isinstance(evidence_path, str) or not evidence_path:
                errors.append(f"{prefix}.evidence_paths[{evidence_index}]: must be a non-empty string")
                continue
            if not _repo_path(repo_root, evidence_path, f"{prefix}.evidence_paths[{evidence_index}]", errors).exists():
                errors.append(f"{prefix}.evidence_paths[{evidence_index}]: path not found: {evidence_path}")
        gold_path = case.get("gold_path")
        if not isinstance(gold_path, str) or not gold_path:
            errors.append(f"{prefix}.gold_path: must be a non-empty string")
        elif not _repo_path(repo_root, gold_path, f"{prefix}.gold_path", errors).is_file():
            errors.append(f"{prefix}.gold_path: file not found: {gold_path}")

    if phase == "confirmatory":
        if not isinstance(replicates, int) or replicates < 3:
            errors.append("confirmatory mode requires at least three replicates")
        if evaluation.get("judge_count", 0) < 3:
            errors.append("confirmatory mode requires at least three judges")
        if evaluation.get("gold_adjudicators", 0) < 2:
            errors.append("confirmatory mode requires at least two gold adjudicators")
        if not controls or not all(controls.values()):
            errors.append("confirmatory mode requires every fairness control enabled")
        if not budgets.get("equal_across_candidates") or any(budgets.get(field) is None for field in budget_fields):
            errors.append("confirmatory mode requires equal, non-null token/time/tool budgets")
        if any(not isinstance(case, dict) or not case.get("confirmation_eligible") for case in cases):
            errors.append("confirmatory mode may contain only confirmation-eligible cases")
        if not evaluation.get("blind_candidate_identity") or not evaluation.get("randomize_order_per_judge"):
            errors.append("confirmatory mode requires candidate blinding and per-judge order randomization")
        for field in ("system_instructions_sha256", "tool_policy_sha256"):
            if not isinstance(execution.get(field), str) or not SHA256.fullmatch(execution[field]):
                errors.append(f"confirmatory mode requires execution.{field} to be a lowercase SHA-256 digest")
        for slot in ("A", "B"):
            if not isinstance(candidates.get(slot), dict) or not candidates[slot].get("validation_commands"):
                errors.append(f"confirmatory mode requires candidates.{slot}.validation_commands to contain at least one native validation command")
    elif phase == "historical-pilot":
        warnings.append("historical-pilot mode cannot declare a definitive winner")
    elif phase == "calibration":
        warnings.append("calibration mode validates the harness but cannot declare a definitive winner")

    if errors:
        raise ValueError("configuration failed preflight:\n- " + "\n- ".join(errors))
    return config, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    args = parser.parse_args()
    try:
        config, warnings = validate(args.config.resolve(), args.repo_root.resolve())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    runs = len(config["cases"]) * 2 * config["execution"]["replicates"]
    print(f"valid: {config['benchmark_id']} ({runs} executor runs)")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

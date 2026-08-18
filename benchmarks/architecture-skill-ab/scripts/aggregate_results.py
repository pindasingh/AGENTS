#!/usr/bin/env python3
"""Aggregate complete architecture A/B run scores without third-party packages."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import random
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from prepare_runs import file_manifest
from seal_review import submission_files
from validate_config import DEFAULT_REPO_ROOT, is_safe_id, validate

SUBMISSION_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
DIMENSIONS = {
    "semantic_accuracy": 45,
    "projection_fidelity": 20,
    "requested_view_compliance": 15,
    "artifact_usefulness": 20,
}


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "stddev": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def case_macro_mean(records: list[dict[str, Any]], case_ids: list[str], slot: str) -> float | None:
    means = []
    for case_id in case_ids:
        values = [
            float(record["scores"]["total"])
            for record in records
            if record["completed"] and record["candidate_slot"] == slot and record["case_id"] == case_id
        ]
        if values:
            means.append(statistics.fmean(values))
    return round(statistics.fmean(means), 4) if means else None


def bootstrap_ci(values: list[float], samples: int = 10000) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(0)
    means = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(samples))
    return [round(means[int(0.025 * samples)], 4), round(means[int(0.975 * samples) - 1], 4)]


def interval_agreement(item_ratings: list[list[float]]) -> float | None:
    observed_pairs = [(a, b) for ratings in item_ratings for index, a in enumerate(ratings) for b in ratings[index + 1 :]]
    all_ratings = [rating for ratings in item_ratings for rating in ratings]
    expected_pairs = [(a, b) for index, a in enumerate(all_ratings) for b in all_ratings[index + 1 :]]
    if not observed_pairs or not expected_pairs:
        return None
    observed = statistics.fmean((a - b) ** 2 for a, b in observed_pairs)
    expected = statistics.fmean((a - b) ** 2 for a, b in expected_pairs)
    if expected == 0:
        return 1.0 if observed == 0 else None
    return round(1 - observed / expected, 4)


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"judge evidence {field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"judge evidence {field} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"judge evidence {field} must include a timezone")
    return parsed


def load_candidate_map(path: Path, config: dict[str, Any]) -> dict[tuple[str, int, str], str]:
    raw = path.read_bytes()
    mapping = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(mapping, dict) or set(mapping) != {"warning", "candidates", "submissions"}:
        raise ValueError("candidate map fields do not match the prepared schema")
    expected_candidates = {
        slot: {
            "id": config["candidates"][slot]["id"],
            "revision": config["candidates"][slot]["revision"],
            "skill_paths": config["candidates"][slot]["skill_paths"],
        }
        for slot in ("A", "B")
    }
    if mapping["candidates"] != expected_candidates or not isinstance(mapping["warning"], str):
        raise ValueError("candidate map identities do not match the validated configuration")
    submissions = mapping["submissions"]
    expected_keys = {
        (case["id"], replicate, slot)
        for case in config["cases"]
        for replicate in range(1, config["execution"]["replicates"] + 1)
        for slot in ("A", "B")
    }
    if not isinstance(submissions, list) or len(submissions) != len(expected_keys):
        raise ValueError("candidate map does not contain every planned submission")
    result: dict[tuple[str, int, str], str] = {}
    for submission in submissions:
        if not isinstance(submission, dict) or set(submission) != {"case_id", "replicate", "candidate_slot", "submission_id"}:
            raise ValueError("candidate map submission fields are invalid")
        key = (submission["case_id"], submission["replicate"], submission["candidate_slot"])
        submission_id = submission["submission_id"]
        if key not in expected_keys or key in result or not isinstance(submission_id, str) or not SUBMISSION_ID.fullmatch(submission_id):
            raise ValueError("candidate map contains an unexpected, duplicate, or invalid submission")
        result[key] = submission_id
    if len(set(result.values())) != len(result):
        raise ValueError("candidate map submission IDs must be globally unique")
    return result


def load_judge_evidence(
    path: Path,
    config: dict[str, Any],
    records: list[dict[str, Any]],
    submission_map: dict[tuple[str, int, str], str],
    preparation: dict[str, Any],
    unblinding: dict[str, Any],
) -> dict[str, Any]:
    evidence = read_json(path)
    if not isinstance(evidence, dict) or set(evidence) != {"protocol", "judges"}:
        raise ValueError("judge evidence must contain exactly protocol and judges")
    protocol = evidence["protocol"]
    protocol_fields = {
        "candidate_identity_blinded",
        "order_randomized_per_judge",
        "judgments_locked_before_unblinding",
        "order_randomization_seed",
        "judgments_locked_at",
    }
    if not isinstance(protocol, dict) or set(protocol) != protocol_fields:
        raise ValueError("judge evidence protocol fields do not match the schema")
    for field in ("candidate_identity_blinded", "order_randomized_per_judge", "judgments_locked_before_unblinding"):
        if protocol[field] is not True:
            raise ValueError(f"judge evidence protocol requires {field}=true")
    seed = protocol["order_randomization_seed"]
    if not isinstance(seed, str) or not re.fullmatch(r"[0-9a-f]{64}", seed):
        raise ValueError("judge evidence requires the prepared 32-byte randomization seed")
    if hashlib.sha256(bytes.fromhex(seed)).hexdigest() != preparation["order_randomization_seed_sha256"]:
        raise ValueError("judge randomization seed does not match the preparation commitment")
    locked = parse_timestamp(protocol["judgments_locked_at"], "judgments_locked_at")
    if not isinstance(unblinding, dict) or set(unblinding) != {"candidate_map_revealed_at"}:
        raise ValueError("unblinding.json must contain exactly candidate_map_revealed_at")
    revealed = parse_timestamp(unblinding["candidate_map_revealed_at"], "candidate_map_revealed_at")
    if locked >= revealed:
        raise ValueError("judge evidence must be locked before revealing the candidate map")

    judges = evidence["judges"]
    if not isinstance(judges, list) or len(judges) != config["evaluation"]["judge_count"]:
        raise ValueError("judge evidence count must exactly match evaluation.judge_count")
    expected_keys = set(submission_map)
    key_by_submission = {submission_id: key for key, submission_id in submission_map.items()}
    judge_ids: set[str] = set()
    ratings_by_key: dict[tuple[str, int, str], list[float]] = {key: [] for key in expected_keys}
    correctness_by_slot: dict[str, list[float]] = {"A": [], "B": []}
    time_by_slot: dict[str, list[float]] = {"A": [], "B": []}
    seed_bytes = bytes.fromhex(seed)
    for judge in judges:
        if not isinstance(judge, dict) or set(judge) != {"id", "format_experience", "prior_format_preference", "assessments"}:
            raise ValueError("every judge must contain exactly id, format_experience, prior_format_preference, and assessments")
        judge_id = judge["id"]
        if not is_safe_id(judge_id) or judge_id in judge_ids:
            raise ValueError("judge IDs must be unique safe lowercase IDs")
        judge_ids.add(judge_id)
        for field in ("format_experience", "prior_format_preference"):
            if not isinstance(judge[field], str) or not judge[field].strip():
                raise ValueError(f"judge {judge_id} requires non-empty {field}")
        assessments = judge["assessments"]
        if not isinstance(assessments, list):
            raise ValueError(f"judge {judge_id} assessments must be an array")
        seen: set[tuple[str, int, str]] = set()
        positions: dict[tuple[str, int], set[int]] = {}
        for assessment in assessments:
            required = {"case_id", "replicate", "submission_id", "presentation_position", "answer_correctness", "answer_time_seconds", "artifact_usefulness_points"}
            if not isinstance(assessment, dict) or set(assessment) != required:
                raise ValueError(f"judge {judge_id} assessment fields do not match the schema")
            submission_id = assessment["submission_id"]
            if not isinstance(submission_id, str) or not SUBMISSION_ID.fullmatch(submission_id) or submission_id not in key_by_submission:
                raise ValueError(f"judge {judge_id} has an invalid or unknown random submission ID")
            key = key_by_submission[submission_id]
            if assessment["case_id"] != key[0] or assessment["replicate"] != key[1] or key in seen:
                raise ValueError(f"judge {judge_id} has an unexpected or duplicate assessment")
            seen.add(key)
            message = f"{judge_id}\0{key[0]}\0{key[1]}".encode("utf-8")
            a_first = hmac.new(seed_bytes, message, hashlib.sha256).digest()[0] % 2 == 0
            expected_position = 1 if (key[2] == "A") == a_first else 2
            position = assessment["presentation_position"]
            if position != expected_position:
                raise ValueError(f"judge {judge_id} presentation order does not match the committed independent permutation")
            positions.setdefault((key[0], key[1]), set()).add(position)
            correctness = assessment["answer_correctness"]
            answer_time = assessment["answer_time_seconds"]
            usefulness = assessment["artifact_usefulness_points"]
            if not isinstance(correctness, (int, float)) or isinstance(correctness, bool) or not math.isfinite(correctness) or not 0 <= correctness <= 1:
                raise ValueError(f"judge {judge_id} answer_correctness must be finite and between 0 and 1")
            if not isinstance(answer_time, (int, float)) or isinstance(answer_time, bool) or not math.isfinite(answer_time) or answer_time < 0:
                raise ValueError(f"judge {judge_id} answer_time_seconds must be finite and non-negative")
            if not isinstance(usefulness, (int, float)) or isinstance(usefulness, bool) or not math.isfinite(usefulness) or not 0 <= usefulness <= 20:
                raise ValueError(f"judge {judge_id} artifact_usefulness_points must be finite and between 0 and 20")
            ratings_by_key[key].append(float(usefulness))
            correctness_by_slot[key[2]].append(float(correctness))
            time_by_slot[key[2]].append(float(answer_time))
        if seen != expected_keys:
            raise ValueError(f"judge {judge_id} does not assess every planned candidate artifact")
        if any(value != {1, 2} for value in positions.values()) or len(positions) != len(expected_keys) // 2:
            raise ValueError(f"judge {judge_id} must see both artifacts in distinct positions for every case/replicate")

    record_by_key = {(record["case_id"], record["replicate"], record["candidate_slot"]): record for record in records}
    for key, ratings in ratings_by_key.items():
        record = record_by_key[key]
        if record["completed"]:
            mean = statistics.fmean(ratings)
            if abs(float(record["scores"]["artifact_usefulness"]) - mean) > 1e-6:
                raise ValueError(f"run usefulness score does not equal judge mean for {key}")
    return {
        "present": True,
        "judge_count": len(judges),
        "candidate_identity_blinded": True,
        "order_randomized_per_judge": True,
        "judgments_locked_before_unblinding": True,
        "answer_correctness": {slot: stats(values) for slot, values in correctness_by_slot.items()},
        "answer_time_seconds": {slot: stats(values) for slot, values in time_by_slot.items()},
        "usefulness_inter_rater_agreement": interval_agreement(list(ratings_by_key.values())),
    }


def load_score(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    try:
        score = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: cannot read score: {exc}") from exc
    required = {"run_id", "case_id", "candidate_slot", "replicate", "completed", "scores", "critical_errors", "metrics"}
    if not isinstance(score, dict):
        raise ValueError(f"{path}: score must be an object")
    missing = required - set(score)
    unknown = set(score) - required - {"notes"}
    if missing:
        raise ValueError(f"{path}: missing fields {sorted(missing)}")
    if unknown:
        raise ValueError(f"{path}: unknown fields {sorted(unknown)}")
    if "notes" in score and (not isinstance(score["notes"], list) or any(not isinstance(note, str) for note in score["notes"])):
        raise ValueError(f"{path}: notes must be an array of strings")
    for field in ("run_id", "case_id", "candidate_slot", "replicate"):
        if score[field] != expected[field]:
            raise ValueError(f"{path}: {field} does not match run plan")
    if not isinstance(score["completed"], bool):
        raise ValueError(f"{path}: completed must be boolean")
    if not isinstance(score["critical_errors"], list) or any(not isinstance(item, str) or not item for item in score["critical_errors"]):
        raise ValueError(f"{path}: critical_errors must be an array of non-empty strings")
    metrics = score["metrics"]
    if not isinstance(metrics, dict):
        raise ValueError(f"{path}: metrics must be an object")
    required_metrics = {"duration_seconds", "total_tokens", "tool_calls", "artifact_bytes", "validation_failures"}
    if set(metrics) != required_metrics:
        raise ValueError(f"{path}: metrics must contain exactly {sorted(required_metrics)}")
    duration = metrics["duration_seconds"]
    if duration is not None and (not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(duration) or duration < 0):
        raise ValueError(f"{path}: duration_seconds must be null or a non-negative number")
    for name in ("total_tokens", "tool_calls", "artifact_bytes"):
        value = metrics[name]
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            raise ValueError(f"{path}: {name} must be null or a non-negative integer")
    validation_failures = metrics["validation_failures"]
    if not isinstance(validation_failures, int) or isinstance(validation_failures, bool) or validation_failures < 0:
        raise ValueError(f"{path}: validation_failures must be a non-negative integer")
    if score["completed"]:
        scores = score["scores"]
        if not isinstance(scores, dict) or set(scores) != {*DIMENSIONS, "total"}:
            raise ValueError(f"{path}: completed run requires all score dimensions and total")
        for name, maximum in DIMENSIONS.items():
            value = scores[name]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= maximum:
                raise ValueError(f"{path}: {name} must be between 0 and {maximum}")
        total = scores["total"]
        if not isinstance(total, (int, float)) or isinstance(total, bool) or not math.isfinite(total) or not 0 <= total <= 100:
            raise ValueError(f"{path}: total must be a finite number between 0 and 100")
        calculated = round(sum(float(scores[name]) for name in DIMENSIONS), 6)
        if abs(float(total) - calculated) > 1e-6:
            raise ValueError(f"{path}: total {scores['total']} does not equal dimension sum {calculated}")
    elif score["scores"] is not None:
        raise ValueError(f"{path}: incomplete run must use null scores")
    return score


def expected_plan(config: dict[str, Any], digest: str) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "benchmark_id": config["benchmark_id"],
        "config_sha256": digest,
        "phase": config["execution"]["phase"],
        "executor_run_count": len(config["cases"]) * 2 * config["execution"]["replicates"],
        "runs": [],
    }
    for case in config["cases"]:
        for replicate in range(1, config["execution"]["replicates"] + 1):
            for slot in ("A", "B"):
                relative = Path("runs") / case["id"] / f"candidate-{slot}" / f"replicate-{replicate:02d}"
                plan["runs"].append({
                    "run_id": f"{case['id']}-{slot}-r{replicate:02d}",
                    "case_id": case["id"],
                    "candidate_slot": slot,
                    "replicate": replicate,
                    "run_directory": relative.as_posix(),
                    "prompt": case["prompt"],
                    "evidence_paths": case["evidence_paths"],
                })
    return plan


def current_input_manifest(config: dict[str, Any], digest: str, repo_root: Path) -> dict[str, Any]:
    return {
        "config_sha256": digest,
        "candidates": {
            slot: {
                "revision": config["candidates"][slot]["revision"],
                "files": file_manifest(repo_root, config["candidates"][slot]["skill_paths"]),
            }
            for slot in ("A", "B")
        },
        "cases": {
            case["id"]: {
                "evidence_files": file_manifest(repo_root, case["evidence_paths"]),
                "gold_file": file_manifest(repo_root, [case["gold_path"]])[0],
            }
            for case in config["cases"]
        },
        "rubric_file": file_manifest(repo_root, [config["evaluation"]["rubric_path"]])[0],
    }


def confined_matches(run_dir: Path, patterns: list[str], label: str) -> list[Path]:
    matches: dict[str, Path] = {}
    for pattern in patterns:
        found = [path for path in run_dir.glob(pattern) if path.is_file()]
        if not found:
            raise ValueError(f"{run_dir}: declared {label} pattern matched no files: {pattern}")
        for path in found:
            resolved = path.resolve()
            try:
                relative = resolved.relative_to(run_dir.resolve()).as_posix()
            except ValueError as exc:
                raise ValueError(f"{run_dir}: {label} escapes run directory: {path}") from exc
            if resolved.stat().st_size == 0:
                raise ValueError(f"{run_dir}: {label} is empty: {relative}")
            matches[relative] = resolved
    return [path for _, path in sorted(matches.items())]


def validate_completed_run_evidence(config: dict[str, Any], run_root: Path, plan: dict[str, Any], records: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[tuple[str, int, str], list[dict[str, object]]]]:
    candidate_by_slot = config["candidates"]
    record_by_id = {record["run_id"]: record for record in records}
    artifact_manifests: dict[tuple[str, int, str], list[dict[str, object]]] = {}
    validated = 0
    for entry in plan["runs"]:
        record = record_by_id[entry["run_id"]]
        if not record["completed"]:
            continue
        run_dir = (run_root / entry["run_directory"]).resolve()
        try:
            run_dir.relative_to(run_root.resolve())
        except ValueError as exc:
            raise ValueError(f"run directory escapes run root: {run_dir}") from exc
        candidate = candidate_by_slot[entry["candidate_slot"]]
        sources = confined_matches(run_dir, candidate["authoritative_source_patterns"], "authoritative source")
        artifacts = confined_matches(run_dir, candidate["artifact_patterns"], "artifact")
        execution = read_json(run_dir / "execution.json")
        timing = read_json(run_dir / "timing.json")
        validation = read_json(run_dir / "validation.json")

        execution_fields = {"run_id", "candidate_slot", "model", "system_instructions_sha256", "tool_policy_sha256", "completed", "budget_exhausted", "errors"}
        if not isinstance(execution, dict) or set(execution) != execution_fields:
            raise ValueError(f"{run_dir}: execution.json fields are invalid")
        if execution["run_id"] != entry["run_id"] or execution["candidate_slot"] != entry["candidate_slot"] or execution["model"] != config["execution"]["model"]:
            raise ValueError(f"{run_dir}: execution identity/model does not match configuration")
        for field in ("system_instructions_sha256", "tool_policy_sha256"):
            if execution[field] != config["execution"][field]:
                raise ValueError(f"{run_dir}: execution {field} does not match configuration")
        if execution["completed"] is not True or execution["budget_exhausted"] is not False:
            raise ValueError(f"{run_dir}: completed confirmatory execution must finish within budget")
        if not isinstance(execution["errors"], list) or any(not isinstance(item, str) for item in execution["errors"]):
            raise ValueError(f"{run_dir}: execution errors must be an array of strings")

        timing_fields = {"total_tokens", "duration_ms", "tool_calls", "captured_from_callback"}
        if not isinstance(timing, dict) or set(timing) != timing_fields or timing["captured_from_callback"] is not True:
            raise ValueError(f"{run_dir}: timing.json must contain callback-captured metrics")
        for field in ("total_tokens", "duration_ms", "tool_calls"):
            value = timing[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{run_dir}: timing {field} must be a non-negative integer")
        budgets = config["execution"]["budgets"]
        if timing["total_tokens"] > budgets["max_total_tokens"] or timing["duration_ms"] > budgets["max_wall_time_seconds"] * 1000 or timing["tool_calls"] > budgets["max_tool_calls"]:
            raise ValueError(f"{run_dir}: completed confirmatory run exceeded its configured budget")

        validation_fields = {"native_viewer", "authoritative_sources_validated", "commands", "viewer"}
        if not isinstance(validation, dict) or set(validation) != validation_fields:
            raise ValueError(f"{run_dir}: validation.json fields are invalid")
        if validation["native_viewer"] != candidate["native_viewer"] or validation["authoritative_sources_validated"] is not True:
            raise ValueError(f"{run_dir}: native/source validation gates did not pass")
        commands = validation["commands"]
        if not isinstance(commands, list) or len(commands) != len(candidate["validation_commands"]):
            raise ValueError(f"{run_dir}: validation command evidence count is invalid")
        for expected_command, command in zip(candidate["validation_commands"], commands):
            if not isinstance(command, dict) or set(command) != {"command", "exit_code", "log_path", "log_sha256"} or command["command"] != expected_command or command["exit_code"] != 0:
                raise ValueError(f"{run_dir}: native validation command failed or changed")
            log_path = (run_dir / command["log_path"]).resolve()
            try:
                log_path.relative_to(run_dir)
            except ValueError as exc:
                raise ValueError(f"{run_dir}: validation log escapes run directory") from exc
            if not log_path.is_file() or hashlib.sha256(log_path.read_bytes()).hexdigest() != command["log_sha256"]:
                raise ValueError(f"{run_dir}: validation log is missing or changed")
        viewer = validation["viewer"]
        viewer_fields = {"command", "exit_code", "log_path", "log_sha256", "artifact_paths", "checks"}
        if not isinstance(viewer, dict) or set(viewer) != viewer_fields or viewer["command"] != candidate["viewer_command"] or viewer["exit_code"] != 0:
            raise ValueError(f"{run_dir}: native viewer execution record is invalid")
        viewer_log = (run_dir / viewer["log_path"]).resolve() if isinstance(viewer["log_path"], str) else run_dir.parent
        try:
            viewer_log.relative_to(run_dir)
        except ValueError as exc:
            raise ValueError(f"{run_dir}: viewer log escapes run directory") from exc
        if not viewer_log.is_file() or viewer_log.stat().st_size == 0 or hashlib.sha256(viewer_log.read_bytes()).hexdigest() != viewer["log_sha256"]:
            raise ValueError(f"{run_dir}: native viewer log is missing, empty, or changed")
        artifact_paths = sorted(path.relative_to(run_dir).as_posix() for path in artifacts)
        if viewer["artifact_paths"] != artifact_paths:
            raise ValueError(f"{run_dir}: native viewer record does not cover every declared artifact")
        if not isinstance(viewer["checks"], list) or sorted(viewer["checks"]) != sorted(candidate["viewer_checks"]) or len(viewer["checks"]) != len(set(viewer["checks"])):
            raise ValueError(f"{run_dir}: native viewer checks do not match the predeclared checks")

        expected_artifact_bytes = sum(path.stat().st_size for path in artifacts)
        metrics = record["metrics"]
        if metrics["total_tokens"] != timing["total_tokens"] or metrics["tool_calls"] != timing["tool_calls"] or metrics["artifact_bytes"] != expected_artifact_bytes:
            raise ValueError(f"{run_dir}: score metrics do not match timing/artifact evidence")
        if metrics["duration_seconds"] is None or abs(float(metrics["duration_seconds"]) - timing["duration_ms"] / 1000) > 1e-6:
            raise ValueError(f"{run_dir}: duration metric does not match timing evidence")
        if metrics["validation_failures"] != 0:
            raise ValueError(f"{run_dir}: completed confirmatory run has validation failures")
        if not sources:
            raise ValueError(f"{run_dir}: authoritative source evidence is missing")
        key = (entry["case_id"], entry["replicate"], entry["candidate_slot"])
        artifact_manifests[key] = [
            {
                "path": path.relative_to(run_dir).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for path in artifacts
        ]
        validated += 1
    return {"completed_runs_with_valid_evidence": validated}, artifact_manifests


def validate_preparation_commitment(run_root: Path, supplied: str | None, config_digest: str) -> tuple[dict[str, Any], bool]:
    coordinator = run_root / "coordinator"
    raw = (coordinator / "preparation.json").read_bytes()
    actual_commitment = hashlib.sha256(raw).hexdigest()
    if supplied is not None and (not re.fullmatch(r"[0-9a-f]{64}", supplied) or supplied != actual_commitment):
        raise ValueError("supplied preparation commitment does not match preparation.json")
    preparation = json.loads(raw, parse_constant=reject_constant)
    fields = {"config_sha256", "input_manifest_sha256", "candidate_map_sha256", "run_plan_sha256", "order_randomization_seed_sha256"}
    if not isinstance(preparation, dict) or set(preparation) != fields or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in preparation.values()):
        raise ValueError("preparation.json fields or digests are invalid")
    bound_files = {
        "config_sha256": run_root / "benchmark-config.json",
        "input_manifest_sha256": coordinator / "input-manifest.json",
        "candidate_map_sha256": coordinator / "candidate-map.json",
        "run_plan_sha256": run_root / "run-plan.json",
    }
    for field, path in bound_files.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != preparation[field]:
            raise ValueError(f"prepared file changed after commitment: {path}")
    if preparation["config_sha256"] != config_digest:
        raise ValueError("prepared configuration digest does not match the supplied configuration")
    return preparation, supplied is not None


def validate_review_commitment(
    run_root: Path,
    supplied: str | None,
    submission_map: dict[tuple[str, int, str], str],
    artifact_manifests: dict[tuple[str, int, str], list[dict[str, object]]],
) -> bool:
    if supplied is None:
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", supplied):
        raise ValueError("review commitment must be a lowercase SHA-256 digest")
    coordinator = run_root / "coordinator"
    raw = (coordinator / "review-seal.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != supplied:
        raise ValueError("supplied review commitment does not match review-seal.json")
    seal = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(seal, dict) or set(seal) != {"judge_evidence_sha256", "submissions"}:
        raise ValueError("review seal fields are invalid")
    judge_bytes = (coordinator / "judge-evidence.json").read_bytes()
    if hashlib.sha256(judge_bytes).hexdigest() != seal["judge_evidence_sha256"]:
        raise ValueError("judge evidence changed after the review commitment")
    expected_ids = set(submission_map.values())
    if not isinstance(seal["submissions"], dict) or set(seal["submissions"]) != expected_ids:
        raise ValueError("review seal does not contain every prepared submission")
    for key, submission_id in submission_map.items():
        directory = run_root / "judge-submissions" / key[0] / f"replicate-{key[1]:02d}" / submission_id
        actual_files = submission_files(directory)
        if seal["submissions"][submission_id] != actual_files:
            raise ValueError(f"judge submission changed after review commitment: {submission_id}")
        visible = {(item["path"], item["sha256"], item["bytes"]) for item in actual_files}
        expected = {(item["path"], item["sha256"], item["bytes"]) for item in artifact_manifests.get(key, [])}
        if not expected.issubset(visible):
            raise ValueError(f"judge submission does not contain every declared final artifact path and byte sequence for {key}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--preparation-commitment")
    parser.add_argument("--review-commitment")
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    args = parser.parse_args()
    try:
        repo_root = args.repo_root.resolve()
        config, warnings = validate(args.config.resolve(), repo_root)
        run_root = args.run_directory.resolve()
        plan = read_json(run_root / "run-plan.json")
        digest = hashlib.sha256(args.config.resolve().read_bytes()).hexdigest()
        preparation, preparation_commitment_valid = validate_preparation_commitment(run_root, args.preparation_commitment, digest)
        expected = expected_plan(config, digest)
        if plan != expected:
            raise ValueError("run plan content does not exactly match the validated configuration")
        saved_manifest = read_json(run_root / "coordinator" / "input-manifest.json")
        if saved_manifest != current_input_manifest(config, digest, repo_root):
            raise ValueError("candidate, evidence, gold, or rubric inputs changed after run preparation")
        submission_map = load_candidate_map(run_root / "coordinator" / "candidate-map.json", config)
        records = []
        for expected in plan["runs"]:
            score_path = run_root / expected["run_directory"] / "score.json"
            if not score_path.is_file():
                raise ValueError(f"missing score: {score_path}")
            records.append(load_score(score_path, expected))
        if config["execution"]["phase"] == "confirmatory":
            run_evidence_summary, artifact_manifests = validate_completed_run_evidence(config, run_root, plan, records)
        else:
            run_evidence_summary, artifact_manifests = {"completed_runs_with_valid_evidence": 0}, {}
        if args.review_commitment is not None and not preparation_commitment_valid:
            raise ValueError("review commitment cannot be trusted without the externally preserved preparation commitment")
        review_commitment_valid = validate_review_commitment(run_root, args.review_commitment, submission_map, artifact_manifests)
        judge_path = run_root / "coordinator" / "judge-evidence.json"
        if review_commitment_valid:
            unblinding = read_json(run_root / "coordinator" / "unblinding.json")
            judge_summary = load_judge_evidence(judge_path, config, records, submission_map, preparation, unblinding)
        else:
            judge_summary = {
                "present": False,
                "judge_count": 0,
                "candidate_identity_blinded": False,
                "order_randomized_per_judge": False,
                "judgments_locked_before_unblinding": False,
                "answer_correctness": None,
                "answer_time_seconds": None,
                "usefulness_inter_rater_agreement": None,
            }
    except (ValueError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    by_slot: dict[str, dict[str, Any]] = {}
    for slot in ("A", "B"):
        slot_records = [record for record in records if record["candidate_slot"] == slot]
        completed = [record for record in slot_records if record["completed"]]
        by_slot[slot] = {
            "runs": len(slot_records),
            "completed": len(completed),
            "completion_rate": round(len(completed) / len(slot_records), 4) if slot_records else 0,
            "critical_error_runs": sum(bool(record["critical_errors"]) for record in slot_records),
            "critical_error_rate": round(sum(bool(record["critical_errors"]) for record in slot_records) / len(slot_records), 4) if slot_records else 0,
            "scores": {name: stats([float(record["scores"][name]) for record in completed]) for name in (*DIMENSIONS, "total")},
            "metrics": {
                name: stats([float(record["metrics"][name]) for record in slot_records if record["metrics"][name] is not None])
                for name in ("duration_seconds", "total_tokens", "tool_calls", "artifact_bytes", "validation_failures")
            },
        }

    indexed = {(record["case_id"], record["replicate"], record["candidate_slot"]): record for record in records}
    paired: list[dict[str, Any]] = []
    for case in config["cases"]:
        for replicate in range(1, config["execution"]["replicates"] + 1):
            a = indexed[(case["id"], replicate, "A")]
            b = indexed[(case["id"], replicate, "B")]
            if a["completed"] and b["completed"]:
                paired.append({
                    "case_id": case["id"],
                    "replicate": replicate,
                    "a_minus_b": {
                        name: round(float(a["scores"][name]) - float(b["scores"][name]), 4)
                        for name in (*DIMENSIONS, "total")
                    },
                })
    paired_differences = {
        name: {
            "statistics": stats([item["a_minus_b"][name] for item in paired]),
            "bootstrap_95_percent_ci": bootstrap_ci([item["a_minus_b"][name] for item in paired]),
        }
        for name in (*DIMENSIONS, "total")
    }
    differences = [item["a_minus_b"]["total"] for item in paired]
    margin = 5.0
    case_outcomes = []
    neutral_cases = [case for case in config["cases"] if case["confirmation_eligible"] and case["requested_view"] != "format-fit"]
    for case in neutral_cases:
        values = [item["a_minus_b"]["total"] for item in paired if item["case_id"] == case["id"]]
        mean = statistics.fmean(values) if values else None
        winner = "A" if mean is not None and mean > margin else "B" if mean is not None and mean < -margin else "tie"
        case_outcomes.append({"case_id": case["id"], "paired_runs": len(values), "mean_a_minus_b": round(mean, 4) if mean is not None else None, "winner": winner})

    interval = paired_differences["total"]["bootstrap_95_percent_ci"]
    a_wins = sum(item["winner"] == "A" for item in case_outcomes)
    b_wins = sum(item["winner"] == "B" for item in case_outcomes)
    decision = {"winner": None, "status": "capability-profile-only", "reasons": []}
    if config["execution"]["phase"] != "confirmatory":
        decision["reasons"].append("run phase is not confirmatory")
    if len(neutral_cases) < 5:
        decision["reasons"].append("fewer than five confirmation-eligible neutral cases")
    if not preparation_commitment_valid:
        decision["reasons"].append("externally preserved preparation commitment was not supplied")
    if not review_commitment_valid:
        decision["reasons"].append("externally preserved blinded-review commitment was not supplied")
    if not all(record["completed"] for record in records):
        decision["reasons"].append("not every planned candidate run completed")
    if not judge_summary["present"]:
        decision["reasons"].append("validated judge evidence is missing")
    if interval is None:
        decision["reasons"].append("no completed paired scores")
    potential = "A" if a_wins >= 4 else "B" if b_wins >= 4 else None
    if potential is None:
        decision["reasons"].append("neither candidate wins at least four neutral cases beyond the practical margin")
    if potential == "A" and (interval is None or interval[0] <= margin):
        decision["reasons"].append("A's confidence interval does not clear the +5 practical margin")
    if potential == "B" and (interval is None or interval[1] >= -margin):
        decision["reasons"].append("B's confidence interval does not clear the -5 practical margin")
    if potential and by_slot[potential]["critical_error_rate"] > by_slot["B" if potential == "A" else "A"]["critical_error_rate"]:
        decision["reasons"].append(f"{potential} has a higher critical-error rate")
    if config["execution"]["phase"] == "confirmatory" and len(neutral_cases) >= 5 and not decision["reasons"]:
        decision = {"winner": potential, "status": "winner", "reasons": ["all consistency, confidence, and critical-error guards passed"]}

    stratified: dict[str, dict[str, Any]] = {}
    case_by_id = {case["id"]: case for case in config["cases"]}
    for field in ("architecture_family", "requested_view"):
        groups: dict[str, Any] = {}
        for value in sorted({case[field] for case in config["cases"]}):
            case_ids = [case["id"] for case in config["cases"] if case[field] == value]
            case_differences = {
                case_id: [item["a_minus_b"]["total"] for item in paired if item["case_id"] == case_id]
                for case_id in case_ids
            }
            outcomes = [
                "A" if statistics.fmean(values) > margin else "B" if statistics.fmean(values) < -margin else "tie"
                for values in case_differences.values()
                if values
            ]
            groups[value] = {
                "candidates": {
                    slot: {
                        "run_statistics": stats([
                            float(record["scores"]["total"])
                            for record in records
                            if record["completed"] and record["candidate_slot"] == slot and case_by_id[record["case_id"]][field] == value
                        ]),
                        "case_macro_mean": case_macro_mean(records, case_ids, slot),
                    }
                    for slot in ("A", "B")
                },
                "win_tie_loss": {
                    "A": outcomes.count("A"),
                    "tie": outcomes.count("tie"),
                    "B": outcomes.count("B"),
                },
            }
        stratified[field] = groups

    aggregate = {
        "benchmark_id": config["benchmark_id"],
        "phase": config["execution"]["phase"],
        "commitments": {
            "preparation": preparation_commitment_valid,
            "blinded_review": review_commitment_valid,
        },
        "run_evidence": run_evidence_summary,
        "judge_evidence": judge_summary,
        "summary": by_slot,
        "paired_differences": paired_differences,
        "stratified_total_scores": stratified,
        "neutral_case_outcomes": case_outcomes,
        "decision": decision,
        "warnings": warnings,
    }
    (run_root / "benchmark.json").write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# {config['benchmark_id']} A/B result",
        "",
        f"Phase: **{config['execution']['phase']}**",
        f"Decision: **{decision['winner'] or 'no overall winner'}** ({decision['status']})",
        f"Validated judges: **{judge_summary['judge_count']}**; usefulness agreement: **{judge_summary['usefulness_inter_rater_agreement']}**",
        f"Paired total-score 95% bootstrap CI (A-B): **{paired_differences['total']['bootstrap_95_percent_ci']}**",
        "",
        "| Candidate | Completion | Mean total | Critical-error rate |",
        "|---|---:|---:|---:|",
    ]
    for slot in ("A", "B"):
        summary = by_slot[slot]
        lines.append(f"| {slot} | {summary['completion_rate']:.1%} | {summary['scores']['total']['mean']} | {summary['critical_error_rate']:.1%} |")
    lines.extend(["", "Reasons:"] + [f"- {reason}" for reason in decision["reasons"]])
    (run_root / "benchmark.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {run_root / 'benchmark.json'} and benchmark.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

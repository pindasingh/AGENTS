#!/usr/bin/env python3
"""Prepare a non-overwriting run scaffold from a validated A/B config."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
import sys
from pathlib import Path

from validate_config import DEFAULT_REPO_ROOT, validate


def file_manifest(repo_root: Path, configured_paths: list[str]) -> list[dict[str, object]]:
    files: dict[str, Path] = {}
    for configured in configured_paths:
        path = (repo_root / configured).resolve()
        candidates = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
        for item in candidates:
            resolved = item.resolve()
            try:
                relative = resolved.relative_to(repo_root).as_posix()
            except ValueError as exc:
                raise ValueError(f"manifest input escapes repository root: {item}") from exc
            files[relative] = resolved
    if not files:
        raise ValueError(f"manifest input contains no files: {configured_paths}")
    return [
        {
            "path": relative,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for relative, path in sorted(files.items())
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    args = parser.parse_args()

    config_path = args.config.resolve()
    output = args.output.resolve()
    try:
        config, warnings = validate(config_path, args.repo_root.resolve())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if output.exists():
        print(f"refusing to overwrite existing path: {output}", file=sys.stderr)
        return 1

    raw = config_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    repo_root = args.repo_root.resolve()
    try:
        input_manifest = {
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
    except (OSError, ValueError, IndexError) as exc:
        print(f"cannot build input manifest: {exc}", file=sys.stderr)
        return 1

    output.mkdir(parents=True)
    shutil.copy2(config_path, output / "benchmark-config.json")
    (output / "config.sha256").write_text(f"{digest}  benchmark-config.json\n", encoding="utf-8")

    coordinator = output / "coordinator"
    coordinator.mkdir()
    review_seed = secrets.token_hex(32)
    (coordinator / "review-seed.txt").write_text(review_seed + "\n", encoding="utf-8")
    submissions = [
        {
            "case_id": case["id"],
            "replicate": replicate,
            "candidate_slot": slot,
            "submission_id": secrets.token_urlsafe(9),
        }
        for case in config["cases"]
        for replicate in range(1, config["execution"]["replicates"] + 1)
        for slot in ("A", "B")
    ]
    mapping = {
        "warning": "Coordinator-only: remove candidate identities from every judge packet.",
        "candidates": {
            slot: {
                "id": config["candidates"][slot]["id"],
                "revision": config["candidates"][slot]["revision"],
                "skill_paths": config["candidates"][slot]["skill_paths"],
            }
            for slot in ("A", "B")
        },
        "submissions": submissions,
    }
    mapping_bytes = (json.dumps(mapping, indent=2) + "\n").encode("utf-8")
    (coordinator / "candidate-map.json").write_bytes(mapping_bytes)
    (coordinator / "candidate-map.sha256").write_text(f"{hashlib.sha256(mapping_bytes).hexdigest()}  candidate-map.json\n", encoding="utf-8")
    (coordinator / "input-manifest.json").write_text(json.dumps(input_manifest, indent=2) + "\n", encoding="utf-8")
    for submission in submissions:
        (output / "judge-submissions" / submission["case_id"] / f"replicate-{submission['replicate']:02d}" / submission["submission_id"]).mkdir(parents=True)

    plan = {
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
                run_dir = output / relative
                (run_dir / "outputs").mkdir(parents=True)
                record = {
                    "run_id": f"{case['id']}-{slot}-r{replicate:02d}",
                    "case_id": case["id"],
                    "candidate_slot": slot,
                    "replicate": replicate,
                    "run_directory": relative.as_posix(),
                    "prompt": case["prompt"],
                    "evidence_paths": case["evidence_paths"],
                }
                (run_dir / "run-input.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                plan["runs"].append(record)
    plan_bytes = (json.dumps(plan, indent=2) + "\n").encode("utf-8")
    (output / "run-plan.json").write_bytes(plan_bytes)
    preparation = {
        "config_sha256": digest,
        "input_manifest_sha256": hashlib.sha256((coordinator / "input-manifest.json").read_bytes()).hexdigest(),
        "candidate_map_sha256": hashlib.sha256(mapping_bytes).hexdigest(),
        "run_plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "order_randomization_seed_sha256": hashlib.sha256(bytes.fromhex(review_seed)).hexdigest(),
    }
    preparation_bytes = (json.dumps(preparation, indent=2) + "\n").encode("utf-8")
    (coordinator / "preparation.json").write_bytes(preparation_bytes)
    preparation_commitment = hashlib.sha256(preparation_bytes).hexdigest()
    (coordinator / "preparation-commitment.txt").write_text(preparation_commitment + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# Prepared architecture A/B run\n\n"
        "Follow the harness runbook. Keep coordinator files away from judges. Preserve the printed "
        "PREPARATION_COMMITMENT outside this directory; confirmatory aggregation requires it. "
        "This scaffold does not execute candidates automatically.\n",
        encoding="utf-8",
    )
    print(f"prepared {plan['executor_run_count']} executor runs at {output}")
    print(f"PREPARATION_COMMITMENT={preparation_commitment}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

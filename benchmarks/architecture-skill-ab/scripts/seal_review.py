#!/usr/bin/env python3
"""Seal blinded judge evidence and submission bytes before candidate unblinding."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def submission_files(directory: Path) -> list[dict[str, object]]:
    files = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(directory.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"submission file escapes its directory: {path}") from exc
        data = resolved.read_bytes()
        if not data:
            raise ValueError(f"submission file is empty: {path}")
        files.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    if not files:
        raise ValueError(f"submission contains no judge-visible files: {directory}")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    run_root = args.run_directory.resolve()
    coordinator = run_root / "coordinator"
    seal_path = coordinator / "review-seal.json"
    if seal_path.exists() or (coordinator / "review-commitment.txt").exists():
        print("refusing to overwrite an existing review seal", file=sys.stderr)
        return 1
    try:
        mapping = json.loads((coordinator / "candidate-map.json").read_text(encoding="utf-8"), parse_constant=reject_constant)
        judge_path = coordinator / "judge-evidence.json"
        judge_bytes = judge_path.read_bytes()
        json.loads(judge_bytes, parse_constant=reject_constant)
        manifests = {}
        for submission in mapping["submissions"]:
            submission_id = submission["submission_id"]
            directory = run_root / "judge-submissions" / submission["case_id"] / f"replicate-{submission['replicate']:02d}" / submission_id
            manifests[submission_id] = submission_files(directory)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"cannot seal review: {exc}", file=sys.stderr)
        return 1
    seal = {
        "judge_evidence_sha256": hashlib.sha256(judge_bytes).hexdigest(),
        "submissions": manifests,
    }
    seal_bytes = (json.dumps(seal, indent=2) + "\n").encode("utf-8")
    seal_path.write_bytes(seal_bytes)
    commitment = hashlib.sha256(seal_bytes).hexdigest()
    (coordinator / "review-commitment.txt").write_text(commitment + "\n", encoding="utf-8")
    print(f"REVIEW_COMMITMENT={commitment}")
    print("Preserve this commitment externally before revealing the candidate map.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

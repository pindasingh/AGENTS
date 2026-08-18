from __future__ import annotations

import hashlib
import hmac
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
VALIDATE = HARNESS / "scripts" / "validate_config.py"
PREPARE = HARNESS / "scripts" / "prepare_runs.py"
AGGREGATE = HARNESS / "scripts" / "aggregate_results.py"
SEAL_REVIEW = HARNESS / "scripts" / "seal_review.py"
PILOT = HARNESS / "pilot" / "benchmark-config.json"


def command(*args: object) -> subprocess.CompletedProcess[str]:
    values = [str(arg) for arg in args]
    if Path(values[0]) in {VALIDATE, PREPARE, AGGREGATE}:
        values.extend(["--repo-root", str(REPO)])
    return subprocess.run(
        [sys.executable, *values],
        text=True,
        capture_output=True,
        check=False,
    )


def write_scores(
    output: Path,
    config: dict[str, object] | None = None,
    incomplete_run: str | None = None,
    nonfinite_run: str | None = None,
) -> None:
    plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
    for record in plan["runs"]:
        a = record["candidate_slot"] == "A"
        completed = record["run_id"] != incomplete_run
        run_dir = output / record["run_directory"]
        artifact_bytes = 100
        metrics = {
            "duration_seconds": float("nan") if record["run_id"] == nonfinite_run else None,
            "total_tokens": None,
            "tool_calls": None,
            "artifact_bytes": artifact_bytes,
            "validation_failures": 0,
        }
        if config is not None and config["execution"]["phase"] == "confirmatory" and completed:
            candidate = config["candidates"][record["candidate_slot"]]
            if a:
                source = run_dir / "outputs" / "architecture" / "architecture.ts"
                artifacts = [
                    run_dir / "outputs" / "architecture" / "architecture.json",
                    run_dir / "outputs" / "architecture" / "index.html",
                ]
            else:
                source = run_dir / "outputs" / "architecture.mmd"
                artifacts = [run_dir / "outputs" / "review.html"]
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("authoritative architecture source\n", encoding="utf-8")
            for artifact in artifacts:
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(f"artifact for {record['run_id']}\n", encoding="utf-8")
            viewer_evidence = run_dir / "viewer-check.log"
            viewer_evidence.write_text("native viewer command completed; all predeclared checks passed\n", encoding="utf-8")
            command_records = []
            for index, validation_command in enumerate(candidate["validation_commands"], start=1):
                log = run_dir / f"validation-{index}.log"
                log.write_text("command completed successfully\n", encoding="utf-8")
                command_records.append(
                    {
                        "command": validation_command,
                        "exit_code": 0,
                        "log_path": log.relative_to(run_dir).as_posix(),
                        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                    }
                )
            (run_dir / "execution.json").write_text(
                json.dumps(
                    {
                        "run_id": record["run_id"],
                        "candidate_slot": record["candidate_slot"],
                        "model": config["execution"]["model"],
                        "system_instructions_sha256": config["execution"]["system_instructions_sha256"],
                        "tool_policy_sha256": config["execution"]["tool_policy_sha256"],
                        "completed": True,
                        "budget_exhausted": False,
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "timing.json").write_text(
                json.dumps({"total_tokens": 1000, "duration_ms": 1000, "tool_calls": 10, "captured_from_callback": True}),
                encoding="utf-8",
            )
            (run_dir / "validation.json").write_text(
                json.dumps(
                    {
                        "native_viewer": candidate["native_viewer"],
                        "authoritative_sources_validated": True,
                        "commands": command_records,
                        "viewer": {
                            "command": candidate["viewer_command"],
                            "exit_code": 0,
                            "log_path": viewer_evidence.relative_to(run_dir).as_posix(),
                            "log_sha256": hashlib.sha256(viewer_evidence.read_bytes()).hexdigest(),
                            "artifact_paths": sorted(artifact.relative_to(run_dir).as_posix() for artifact in artifacts),
                            "checks": candidate["viewer_checks"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            artifact_bytes = sum(artifact.stat().st_size for artifact in artifacts)
            metrics = {
                "duration_seconds": 1.0,
                "total_tokens": 1000,
                "tool_calls": 10,
                "artifact_bytes": artifact_bytes,
                "validation_failures": 0,
            }
        score = {
            "run_id": record["run_id"],
            "case_id": record["case_id"],
            "candidate_slot": record["candidate_slot"],
            "replicate": record["replicate"],
            "completed": completed,
            "scores": {
                "semantic_accuracy": 36 if a else 30,
                "projection_fidelity": 16 if a else 14,
                "requested_view_compliance": 12 if a else 11,
                "artifact_usefulness": 16 if a else 15,
                "total": 80 if a else 70,
            }
            if completed
            else None,
            "critical_errors": [],
            "metrics": metrics,
        }
        (run_dir / "score.json").write_text(json.dumps(score), encoding="utf-8")


def write_confirmatory_config(path: Path) -> dict[str, object]:
    config = json.loads(PILOT.read_text(encoding="utf-8"))
    template = deepcopy(config["cases"][0])
    config["benchmark_id"] = "confirmatory-test"
    config["execution"].update(
        {
            "phase": "confirmatory",
            "replicates": 3,
            "model": "test-model-v1",
            "seed_policy": "independent fixed seeds per paired replicate",
            "system_instructions_sha256": "1" * 64,
            "tool_policy_sha256": "2" * 64,
        }
    )
    config["execution"]["controls"] = {key: True for key in config["execution"]["controls"]}
    config["execution"]["budgets"] = {
        "equal_across_candidates": True,
        "max_total_tokens": 10000,
        "max_wall_time_seconds": 600,
        "max_tool_calls": 100,
    }
    for slot in ("A", "B"):
        if not config["candidates"][slot]["validation_commands"]:
            config["candidates"][slot]["validation_commands"] = ["python -c validate-native-output"]
    config["evaluation"].update(
        {
            "judge_count": 3,
            "gold_adjudicators": 2,
            "blind_candidate_identity": True,
            "randomize_order_per_judge": True,
        }
    )
    config["cases"] = []
    for number in range(1, 6):
        case = deepcopy(template)
        case["id"] = f"neutral-{number}"
        case["confirmation_eligible"] = True
        case["notes"] = "Synthetic harness test using an existing local fixture."
        config["cases"].append(case)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def write_judge_evidence(output: Path, config: dict[str, object]) -> None:
    mapping = json.loads((output / "coordinator" / "candidate-map.json").read_text(encoding="utf-8"))
    submissions = {
        (item["case_id"], item["replicate"], item["candidate_slot"]): item["submission_id"]
        for item in mapping["submissions"]
    }
    plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
    run_by_key = {(item["case_id"], item["replicate"], item["candidate_slot"]): output / item["run_directory"] for item in plan["runs"]}
    for key, submission_id in submissions.items():
        run_dir = run_by_key[key]
        if key[2] == "A":
            artifacts = [run_dir / "outputs" / "architecture" / "architecture.json", run_dir / "outputs" / "architecture" / "index.html"]
        else:
            artifacts = [run_dir / "outputs" / "review.html"]
        destination = output / "judge-submissions" / key[0] / f"replicate-{key[1]:02d}" / submission_id
        for artifact in artifacts:
            target = destination / artifact.relative_to(run_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(artifact, target)

    seed = (output / "coordinator" / "review-seed.txt").read_text(encoding="utf-8").strip()
    seed_bytes = bytes.fromhex(seed)
    judges = []
    for judge_number in range(1, config["evaluation"]["judge_count"] + 1):
        judge_id = f"judge-{judge_number}"
        assessments = []
        for case in config["cases"]:
            for replicate in range(1, config["execution"]["replicates"] + 1):
                message = f"{judge_id}\0{case['id']}\0{replicate}".encode("utf-8")
                a_first = hmac.new(seed_bytes, message, hashlib.sha256).digest()[0] % 2 == 0
                order = ("A", "B") if a_first else ("B", "A")
                for position, slot in enumerate(order, start=1):
                    assessments.append(
                        {
                            "case_id": case["id"],
                            "replicate": replicate,
                            "submission_id": submissions[(case["id"], replicate, slot)],
                            "presentation_position": position,
                            "answer_correctness": 0.9 if slot == "A" else 0.8,
                            "answer_time_seconds": 30 if slot == "A" else 35,
                            "artifact_usefulness_points": 16 if slot == "A" else 15,
                        }
                    )
        judges.append(
            {
                "id": judge_id,
                "format_experience": "mixed architecture diagram experience",
                "prior_format_preference": "none",
                "assessments": assessments,
            }
        )
    evidence = {
        "protocol": {
            "candidate_identity_blinded": True,
            "order_randomized_per_judge": True,
            "judgments_locked_before_unblinding": True,
            "order_randomization_seed": seed,
            "judgments_locked_at": "2026-08-18T12:00:00Z",
        },
        "judges": judges,
    }
    (output / "coordinator" / "judge-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def seal_and_unblind(output: Path) -> str:
    sealed = command(SEAL_REVIEW, output)
    if sealed.returncode != 0:
        raise AssertionError(sealed.stderr)
    commitment = (output / "coordinator" / "review-commitment.txt").read_text(encoding="utf-8").strip()
    (output / "coordinator" / "unblinding.json").write_text(
        json.dumps({"candidate_map_revealed_at": "2026-08-18T12:01:00Z"}) + "\n",
        encoding="utf-8",
    )
    return commitment


def preparation_commitment(output: Path) -> str:
    return (output / "coordinator" / "preparation-commitment.txt").read_text(encoding="utf-8").strip()


class HarnessTests(unittest.TestCase):
    def test_pilot_config_validates_with_historical_warning(self) -> None:
        result = command(VALIDATE, PILOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("(4 executor runs)", result.stdout)
        self.assertIn("cannot declare a definitive winner", result.stdout)

    def test_confirmatory_preflight_rejects_weak_controls(self) -> None:
        config = json.loads(PILOT.read_text(encoding="utf-8"))
        config["execution"]["phase"] = "confirmatory"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            result = command(VALIDATE, path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at least three replicates", result.stderr)
        self.assertIn("equal, non-null token/time/tool budgets", result.stderr)
        self.assertIn("only confirmation-eligible cases", result.stderr)
        self.assertIn("candidates.B.validation_commands", result.stderr)

    def test_validator_rejects_unknown_fields_unsafe_ids_and_wrong_optional_types(self) -> None:
        config = json.loads(PILOT.read_text(encoding="utf-8"))
        config["execution"]["replciates"] = 9
        config["description"] = 7
        config["cases"][0]["id"] = "../../outside"
        config["cases"][1]["id"] = "nul"
        config["cases"][1]["notes"] = []
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            result = command(VALIDATE, path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown fields", result.stderr)
        self.assertGreaterEqual(result.stderr.count("safe lowercase filesystem ID"), 2)
        self.assertIn("description: must be a string", result.stderr)
        self.assertIn("notes: must be a string", result.stderr)

    def test_validator_rejects_overflowed_json_numbers(self) -> None:
        text = PILOT.read_text(encoding="utf-8").replace('"replicates": 1', '"replicates": 1e999', 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text(text, encoding="utf-8")
            result = command(VALIDATE, path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-finite number is not allowed", result.stderr)

    def test_prepare_creates_hashed_isolated_non_overwriting_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            first = command(PREPARE, PILOT, output)
            self.assertEqual(first.returncode, 0, first.stderr)
            plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["executor_run_count"], 4)
            self.assertEqual(len(plan["runs"]), 4)
            mapping = json.loads((output / "coordinator" / "candidate-map.json").read_text(encoding="utf-8"))
            self.assertEqual(len(mapping["submissions"]), 4)
            self.assertTrue((output / "coordinator" / "candidate-map.sha256").is_file())
            manifest = json.loads((output / "coordinator" / "input-manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["candidates"]["A"]["files"])
            self.assertTrue(manifest["cases"]["eshop-broad"]["evidence_files"])
            self.assertTrue((output / "runs" / "eshop-broad" / "candidate-A" / "replicate-01" / "outputs").is_dir())
            second = command(PREPARE, PILOT, output)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("refusing to overwrite", second.stderr)

    def test_aggregate_rejects_tampered_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            self.assertEqual(command(PREPARE, PILOT, output).returncode, 0)
            original_commitment = preparation_commitment(output)
            plan_path = output / "run-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["runs"][0]["run_directory"] = "../../outside"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            preparation_path = output / "coordinator" / "preparation.json"
            preparation = json.loads(preparation_path.read_text(encoding="utf-8"))
            preparation["run_plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            preparation_path.write_text(json.dumps(preparation), encoding="utf-8")
            (output / "coordinator" / "preparation-commitment.txt").write_text(
                hashlib.sha256(preparation_path.read_bytes()).hexdigest() + "\n",
                encoding="utf-8",
            )
            result = command(AGGREGATE, PILOT, output, "--preparation-commitment", original_commitment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("supplied preparation commitment does not match", result.stderr)

    def test_aggregate_rejects_nonfinite_scores(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            self.assertEqual(command(PREPARE, PILOT, output).returncode, 0)
            plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
            write_scores(output, nonfinite_run=plan["runs"][0]["run_id"])
            result = command(AGGREGATE, PILOT, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-finite JSON number", result.stderr)

    def test_historical_pilot_cannot_declare_winner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            self.assertEqual(command(PREPARE, PILOT, output).returncode, 0)
            write_scores(output)
            aggregate = command(AGGREGATE, PILOT, output)
            self.assertEqual(aggregate.returncode, 0, aggregate.stderr)
            result = json.loads((output / "benchmark.json").read_text(encoding="utf-8"))
            self.assertIsNone(result["decision"]["winner"])
            self.assertIn("run phase is not confirmatory", result["decision"]["reasons"])
            self.assertIn("validated judge evidence is missing", result["decision"]["reasons"])
            self.assertEqual(result["paired_differences"]["total"]["statistics"]["mean"], 10.0)

    def test_confirmatory_winner_requires_complete_runs_and_judge_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "confirmatory.json"
            config = write_confirmatory_config(config_path)
            output = temporary_path / "run"
            prepared = command(PREPARE, config_path, output)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
            write_scores(output, config, incomplete_run=plan["runs"][0]["run_id"])
            aggregate = command(
                AGGREGATE,
                config_path,
                output,
                "--preparation-commitment",
                preparation_commitment(output),
            )
            self.assertEqual(aggregate.returncode, 0, aggregate.stderr)
            result = json.loads((output / "benchmark.json").read_text(encoding="utf-8"))
            self.assertIsNone(result["decision"]["winner"])
            self.assertIn("not every planned candidate run completed", result["decision"]["reasons"])

    def test_confirmatory_completed_scores_without_artifacts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "confirmatory.json"
            write_confirmatory_config(config_path)
            output = temporary_path / "run"
            self.assertEqual(command(PREPARE, config_path, output).returncode, 0)
            write_scores(output)
            aggregate = command(
                AGGREGATE,
                config_path,
                output,
                "--preparation-commitment",
                preparation_commitment(output),
            )
            self.assertNotEqual(aggregate.returncode, 0)
            self.assertIn("authoritative source pattern matched no files", aggregate.stderr)

    def test_confirmatory_budget_overrun_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "confirmatory.json"
            config = write_confirmatory_config(config_path)
            output = temporary_path / "run"
            self.assertEqual(command(PREPARE, config_path, output).returncode, 0)
            write_scores(output, config)
            plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
            run_dir = output / plan["runs"][0]["run_directory"]
            timing_path = run_dir / "timing.json"
            timing = json.loads(timing_path.read_text(encoding="utf-8"))
            timing["total_tokens"] = config["execution"]["budgets"]["max_total_tokens"] + 1
            timing_path.write_text(json.dumps(timing), encoding="utf-8")
            aggregate = command(
                AGGREGATE,
                config_path,
                output,
                "--preparation-commitment",
                preparation_commitment(output),
            )
            self.assertNotEqual(aggregate.returncode, 0)
            self.assertIn("exceeded its configured budget", aggregate.stderr)

    def test_viewer_evidence_must_match_predeclared_command_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "confirmatory.json"
            config = write_confirmatory_config(config_path)
            output = temporary_path / "run"
            self.assertEqual(command(PREPARE, config_path, output).returncode, 0)
            write_scores(output, config)
            plan = json.loads((output / "run-plan.json").read_text(encoding="utf-8"))
            run_dir = output / plan["runs"][0]["run_directory"]
            validation_path = run_dir / "validation.json"
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            validation["viewer"]["artifact_paths"] = validation["viewer"]["artifact_paths"][:1]
            validation_path.write_text(json.dumps(validation), encoding="utf-8")
            aggregate = command(
                AGGREGATE,
                config_path,
                output,
                "--preparation-commitment",
                preparation_commitment(output),
            )
            self.assertNotEqual(aggregate.returncode, 0)
            self.assertIn("does not cover every declared artifact", aggregate.stderr)

    def test_committed_randomization_order_is_reconstructed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "confirmatory.json"
            config = write_confirmatory_config(config_path)
            output = temporary_path / "run"
            self.assertEqual(command(PREPARE, config_path, output).returncode, 0)
            write_scores(output, config)
            write_judge_evidence(output, config)
            evidence_path = output / "coordinator" / "judge-evidence.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            first = evidence["judges"][0]["assessments"][0]
            first["presentation_position"] = 2 if first["presentation_position"] == 1 else 1
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            review_commitment = seal_and_unblind(output)
            aggregate = command(
                AGGREGATE,
                config_path,
                output,
                "--preparation-commitment",
                preparation_commitment(output),
                "--review-commitment",
                review_commitment,
            )
            self.assertNotEqual(aggregate.returncode, 0)
            self.assertIn("committed independent permutation", aggregate.stderr)

    def test_complete_confirmatory_run_can_declare_winner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "confirmatory.json"
            config = write_confirmatory_config(config_path)
            output = temporary_path / "run"
            self.assertEqual(command(PREPARE, config_path, output).returncode, 0)
            write_scores(output, config)
            write_judge_evidence(output, config)
            review_commitment = seal_and_unblind(output)
            aggregate = command(
                AGGREGATE,
                config_path,
                output,
                "--preparation-commitment",
                preparation_commitment(output),
                "--review-commitment",
                review_commitment,
            )
            self.assertEqual(aggregate.returncode, 0, aggregate.stderr)
            result = json.loads((output / "benchmark.json").read_text(encoding="utf-8"))
            self.assertEqual(result["decision"]["winner"], "A")
            self.assertEqual(result["judge_evidence"]["judge_count"], 3)
            self.assertEqual(result["stratified_total_scores"]["architecture_family"]["event-driven"]["candidates"]["A"]["case_macro_mean"], 80.0)


if __name__ == "__main__":
    unittest.main()

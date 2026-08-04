import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from model_json import init, validate


FLOW_ID = "flow.submit-order.success"
PARTICIPANTS = ["runtime.client", "runtime.api"]


class Tests(unittest.TestCase):
    def initialized(self, directory):
        root = Path(directory) / ".architecture-model"
        init(root, "Ordering", ["../Orders API"])
        return root

    def add_complete_flow(self, root, write_reviews=True):
        model_path = root / "model.json"
        model = json.loads(model_path.read_text())
        evidence = [{"sourceId": "orders-api", "path": "src/Orders.cs", "observation": "Fixture evidence"}]
        findings = [{"sourceId": "orders-api", "unitId": "orders-api"}]
        model["nodes"] = {
            "runtime.client": {"kind": "runtime"},
            "runtime.api": {"kind": "runtime"},
        }
        model["interfaces"]["interface.api.submit-order"] = {"owner": "runtime.api"}
        model["relationships"]["relationship.client.submit-order"] = {
            "from": "runtime.client", "to": "runtime.api"
        }
        model["flowCoverage"]["interface.api.submit-order"] = {
            "status": "covered", "flowIds": [FLOW_ID], "reason": "Fixture path", "evidence": evidence
        }
        model["flows"][FLOW_ID] = {
            "name": "Submit order - successful path",
            "scenario": "Submit order",
            "path": "successful",
            "description": "Submits and returns an order",
            "owner": "runtime.api",
            "trigger": "interface.api.submit-order",
            "callers": [
                {
                    "nodeId": "runtime.client", "relationshipId": "relationship.client.submit-order",
                    "certainty": "corroborated", "sourceFindings": findings, "evidence": evidence,
                },
            ],
            "participants": [
                {"id": "runtime.client", "role": "Initiates the request"},
                {"id": "runtime.api", "role": "Handles and returns the request"},
            ],
            "certainty": "corroborated",
            "sequence": [
                {
                    "number": "1", "kind": "stage", "name": "Request enters the API",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "1.1", "parent": "1", "kind": "entry",
                    "callerRelationshipIds": ["relationship.client.submit-order"],
                    "destination": "runtime.api", "interfaceId": "interface.api.submit-order",
                    "operation": "Sends POST /api/orders",
                    "input": "OrderRequest", "output": "Accepted request", "boundary": "runtime",
                    "certainty": "corroborated", "continuation": "continue",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "2", "kind": "stage", "name": "Response returns",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "2.1", "parent": "2", "kind": "return",
                    "source": "runtime.api",
                    "callerRelationshipIds": ["relationship.client.submit-order"],
                    "operation": "Returns OrderResponse to the caller",
                    "interfaceId": "interface.api.submit-order", "input": "Response payload",
                    "output": "OrderResponse", "boundary": "runtime", "certainty": "corroborated",
                    "continuation": "return", "sourceFindings": findings, "evidence": evidence,
                },
            ],
            "outcome": {"kind": "response", "at": "2.1", "description": "Caller receives OrderResponse"},
            "coverage": {"status": "complete", "unresolvedContinuations": [], "knownOmissions": []},
        }
        model_path.write_text(json.dumps(model), encoding="utf-8")
        progress_path = root / "progress.json"
        progress = json.loads(progress_path.read_text())
        progress["flowReviews"][FLOW_ID] = {
            "stage": "complete",
            "gates": {
                "canonicalFlowValidated": True,
                "numberedSequenceWritten": True,
                "asciiDiagramWritten": True,
                "projectionsValidated": True,
            },
        }
        progress_path.write_text(json.dumps(progress), encoding="utf-8")
        if write_reviews:
            review = root / "flow-reviews" / FLOW_ID
            review.mkdir(parents=True)
            (review / "numbered-sequence.md").write_text(
                """# Submit order - successful path

- Flow ID: `flow.submit-order.success`
- Participant IDs: runtime.client | runtime.api

## Numbered execution

1. **Request enters the API**
   1.1 **Sends POST /api/orders**
2. **Response returns**
   2.1 **Returns OrderResponse to the caller**
""",
                encoding="utf-8",
            )
            (review / "sequence-diagram.txt").write_text(
                """Flow: Submit order - successful path
Flow ID: flow.submit-order.success

Participants (exact model set):
  P1 runtime.client
  P2 runtime.api

1 [STAGE] Request enters the API
1.1 P1 -> P2 : Sends POST /api/orders
2 [STAGE] Response returns
2.1 P2 -> P1 : Returns OrderResponse to the caller
""",
                encoding="utf-8",
            )
        return model, progress

    def mutate(self, root, filename, old, new):
        path = root / "flow-reviews" / FLOW_ID / filename
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_init_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.assertEqual(
                {"subject.json", "decisions.json", "progress.json", "model.json", "scans", "flow-reviews"},
                {path.name for path in root.iterdir()},
            )
            validate(root)
            model = json.loads((root / "model.json").read_text())
            self.assertEqual({}, model["components"])
            self.assertEqual({}, model["flowCoverage"])

    def test_validate_complete_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            validate(root)

    def test_validate_requires_both_flow_reviews(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root, write_reviews=False)
            with self.assertRaisesRegex(ValueError, "missing flow review artifact"):
                validate(root)

    def test_validate_rejects_reordered_markdown_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "numbered-sequence.md", "2. **Response returns**\n   2.1", "2.1 **Returns OrderResponse to the caller**\n2.")
            with self.assertRaisesRegex(ValueError, "sequence numbers/order differ"):
                validate(root)

    def test_validate_rejects_missing_ascii_step(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "sequence-diagram.txt", "1.1 P1 -> P2 : Sends POST /api/orders\n", "")
            with self.assertRaisesRegex(ValueError, "sequence numbers/order differ"):
                validate(root)

    def test_validate_rejects_markdown_label_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "numbered-sequence.md", "Sends POST /api/orders", "Calls the API")
            with self.assertRaisesRegex(ValueError, "labels differ"):
                validate(root)

    def test_validate_rejects_ascii_label_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "sequence-diagram.txt", "Returns OrderResponse to the caller", "Returns a response")
            with self.assertRaisesRegex(ValueError, "does not contain the exact model label"):
                validate(root)

    def test_validate_rejects_ascii_direction_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "sequence-diagram.txt", "1.1 P1 -> P2", "1.1 P2 -> P1")
            with self.assertRaisesRegex(ValueError, "endpoints/direction differ"):
                validate(root)

    def test_validate_rejects_noncontiguous_ascii_participant_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "sequence-diagram.txt", "P2 runtime.api", "P3 runtime.api")
            with self.assertRaisesRegex(ValueError, "participant aliases must be contiguous"):
                validate(root)

    def test_validate_rejects_caller_entry_destination_outside_participants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model, _ = self.add_complete_flow(root)
            model["flows"][FLOW_ID]["sequence"][1]["destination"] = "runtime.missing"
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "destination is not a participant"):
                validate(root)

    def test_validate_rejects_caller_return_source_outside_participants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model, _ = self.add_complete_flow(root)
            model["flows"][FLOW_ID]["sequence"][3]["source"] = "runtime.missing"
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source is not a participant"):
                validate(root)

    def test_validate_rejects_participant_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.add_complete_flow(root)
            self.mutate(root, "numbered-sequence.md", "runtime.client | runtime.api", "runtime.api | runtime.client")
            with self.assertRaisesRegex(ValueError, "participant IDs/order differ"):
                validate(root)

    def test_validate_rejects_incomplete_projection_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            _, progress = self.add_complete_flow(root)
            progress["flowReviews"][FLOW_ID]["gates"]["projectionsValidated"] = False
            (root / "progress.json").write_text(json.dumps(progress), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "review is not complete"):
                validate(root)

    def test_validate_rejects_interface_without_flow_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model = json.loads((root / "model.json").read_text())
            model["interfaces"]["interface.api.submit-order"] = {"owner": "runtime.api"}
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "flowCoverage must exactly match model interfaces"):
                validate(root)

    def test_validate_rejects_covered_interface_without_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model = json.loads((root / "model.json").read_text())
            interface_id = "interface.api.submit-order"
            model["interfaces"][interface_id] = {"owner": "runtime.api"}
            model["flowCoverage"][interface_id] = {
                "status": "covered", "flowIds": ["flow.missing"], "reason": "Invalid fixture", "evidence": []
            }
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "flowIds must resolve to model flows"):
                validate(root)

    def test_validate_rejects_noncontiguous_model_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model, _ = self.add_complete_flow(root)
            model["flows"][FLOW_ID]["sequence"][1]["number"] = "1.2"
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "sibling numbers are not contiguous"):
                validate(root)

    def test_validate_rejects_undetailed_sequence_step(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model, _ = self.add_complete_flow(root)
            del model["flows"][FLOW_ID]["sequence"][1]["output"]
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requires non-empty output"):
                validate(root)

    def test_validate_rejects_unresolved_step_relationship(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model, _ = self.add_complete_flow(root)
            model["flows"][FLOW_ID]["sequence"][1]["relationshipId"] = "relationship.missing"
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "relationshipId does not resolve"):
                validate(root)

    def test_validate_rejects_unsafe_flow_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            model = json.loads((root / "model.json").read_text())
            model["flows"]["flow../escape"] = {}
            (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
            progress = json.loads((root / "progress.json").read_text())
            progress["flowReviews"]["flow../escape"] = {}
            (root / "progress.json").write_text(json.dumps(progress), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid or unsafe flow ID"):
                validate(root)

    def test_standard_library_only(self):
        tree = ast.parse((ROOT / "scripts/model_json.py").read_text())
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue(roots <= set(sys.stdlib_module_names), roots - set(sys.stdlib_module_names))


if __name__ == "__main__":
    unittest.main()

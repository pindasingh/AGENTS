import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from architecture_model import build_index, canonical_bytes, diff_indexes, format_model, init, long_path, render, validate, write_json

SOURCE_ID = "source.orders-api"
DOMAIN_ID = "domain.ordering"
OPERATION_ID = "operation.submit-order"
PATH_ID = "path.submit-order.success"


class ArchitectureModelTests(unittest.TestCase):
    def initialized(self, directory):
        root = Path(directory) / ".architecture-model"
        init(root, "Ordering", ["../orders-api"])
        return root

    def evidence(self, observation="Fixture evidence"):
        return [{"sourceId": SOURCE_ID, "path": "src/Orders.cs", "observation": observation}]

    def findings(self, unit_id="orders-api"):
        return [{"sourceId": SOURCE_ID, "unitId": unit_id}]

    def artifact(self, root, collection, artifact_id, value):
        write_json(root / collection / f"{artifact_id}.json", value)

    def complete_model(self, root):
        scan_path = root / "sources" / SOURCE_ID / "scan.json"
        scan = json.loads(scan_path.read_text())
        scan["source"].update({
            "repository": "https://example.invalid/orders-api.git",
            "revision": "abc123",
            "branch": "main",
            "status": "complete",
        })
        scan["source"]["coverage"]["included"] = ["src/**"]
        scan["units"] = {"orders-api": {"kind": "runtime"}}
        write_json(scan_path, scan)

        progress_path = root / "progress.json"
        progress = json.loads(progress_path.read_text())
        progress["sources"][SOURCE_ID] = {
            "revision": "abc123",
            "stage": "complete",
            "gates": {
                "scanWritten": True,
                "scanValidated": True,
                "graphUpdated": True,
                "gapsReviewed": True,
                "conflictsReviewed": True,
            },
        }

        evidence = self.evidence()
        findings = self.findings()
        nodes = {
            "runtime.client": ("runtime", "Client", "Initiates order submission"),
            "runtime.api": ("runtime", "Orders API", "Handles order submission"),
            "store.orders": ("store", "Orders store", "Persists orders"),
        }
        for node_id, (kind, name, responsibility) in nodes.items():
            self.artifact(root, "nodes", node_id, {
                "schemaVersion": 2,
                "id": node_id,
                "kind": kind,
                "name": name,
                "responsibility": responsibility,
                "technology": ["Fixture"],
                "identity": {"fixture": node_id},
                "certainty": "observed",
                "sourceFindings": findings,
                "evidence": evidence,
            })

        components = {
            "component.client.order-form": ("runtime.client", "Order form", "Captures an order"),
            "component.api.submit-handler": ("runtime.api", "Submit handler", "Orchestrates submission"),
        }
        for component_id, (owner, name, responsibility) in components.items():
            self.artifact(root, "components", component_id, {
                "schemaVersion": 2,
                "id": component_id,
                "domainId": DOMAIN_ID,
                "ownerNodeId": owner,
                "name": name,
                "responsibility": responsibility,
                "technology": ["Fixture"],
                "operationIds": [OPERATION_ID],
                "certainty": "observed",
                "sourceFindings": findings,
                "evidence": evidence,
            })

        interface_id = "interface.api.submit-order"
        self.artifact(root, "interfaces", interface_id, {
            "schemaVersion": 2,
            "id": interface_id,
            "ownerNodeId": "runtime.api",
            "kind": "http",
            "purpose": "Submits an order",
            "method": "POST",
            "path": "/api/orders",
            "version": "v1",
            "rules": [],
            "coverage": {
                "status": "covered",
                "operationPathIds": [PATH_ID],
                "reason": "Successful request path",
                "gapIds": [],
            },
            "certainty": "observed",
            "sourceFindings": findings,
            "evidence": evidence,
        })

        relationships = {
            "relationship.client.submit-order": ("runtime.client", "runtime.api", "request", interface_id),
            "relationship.api.write-orders": ("runtime.api", "store.orders", "data", None),
        }
        for relationship_id, (source, destination, kind, linked_interface) in relationships.items():
            document = {
                "schemaVersion": 2,
                "id": relationship_id,
                "fromId": source,
                "toId": destination,
                "kind": kind,
                "purpose": "Fixture interaction",
                "technology": "Fixture",
                "rules": [],
                "certainty": "observed",
                "sourceFindings": findings,
                "evidence": evidence,
            }
            if linked_interface:
                document["interfaceId"] = linked_interface
            self.artifact(root, "relationships", relationship_id, document)

        operation_root = root / "operations" / OPERATION_ID
        write_json(operation_root / "operation.json", {
            "schemaVersion": 2,
            "id": OPERATION_ID,
            "domainId": DOMAIN_ID,
            "name": "Submit order",
            "description": "Submits and persists an order",
            "ownerComponentIds": ["component.client.order-form", "component.api.submit-handler"],
            "triggerInterfaceIds": [interface_id],
            "pathIds": [PATH_ID],
        })
        write_json(operation_root / "paths" / f"{PATH_ID}.json", {
            "schemaVersion": 2,
            "id": PATH_ID,
            "operationId": OPERATION_ID,
            "name": "Submit order — successful path",
            "kind": "success",
            "description": "Submits and stores a valid order",
            "triggerInterfaceIds": [interface_id],
            "callers": [{
                "nodeId": "runtime.client",
                "relationshipId": "relationship.client.submit-order",
                "certainty": "corroborated",
                "sourceFindings": findings,
                "evidence": evidence,
            }],
            "participants": [
                {"id": "runtime.client", "role": "Initiates the request"},
                {"id": "runtime.api", "role": "Accepts and returns the request"},
                {"id": "component.api.submit-handler", "role": "Orchestrates submission"},
                {"id": "store.orders", "role": "Persists the order"},
            ],
            "certainty": "corroborated",
            "sequence": [
                {
                    "number": "1", "kind": "stage", "name": "Request enters the Orders API",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "1.1", "parent": "1", "kind": "entry",
                    "callerRelationshipIds": ["relationship.client.submit-order"],
                    "destination": "runtime.api", "interfaceId": interface_id,
                    "operation": "Sends POST /api/orders", "input": "OrderRequest",
                    "output": "Accepted request", "boundary": "runtime", "continuation": "continue",
                    "certainty": "corroborated", "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "1.2", "parent": "1", "kind": "local-operation",
                    "at": "component.api.submit-handler", "operation": "Validates the submitted order",
                    "input": "OrderRequest", "output": "Validated order", "boundary": "in-process",
                    "continuation": "continue", "certainty": "observed",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "1.3", "parent": "1", "kind": "data-write",
                    "source": "component.api.submit-handler", "destination": "store.orders",
                    "relationshipId": "relationship.api.write-orders", "operation": "Stores the accepted order",
                    "input": "Validated order", "output": "Persisted order", "boundary": "data-store",
                    "continuation": "continue", "certainty": "observed",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "2", "kind": "stage", "name": "Response returns",
                    "sourceFindings": findings, "evidence": evidence,
                },
                {
                    "number": "2.1", "parent": "2", "kind": "return",
                    "source": "runtime.api", "callerRelationshipIds": ["relationship.client.submit-order"],
                    "interfaceId": interface_id, "operation": "Returns OrderResponse to the caller",
                    "input": "Persisted order", "output": "OrderResponse", "boundary": "runtime",
                    "continuation": "return", "certainty": "corroborated",
                    "sourceFindings": findings, "evidence": evidence,
                },
            ],
            "outcome": {"kind": "response", "at": "2.1", "description": "Caller receives OrderResponse"},
            "coverage": {"status": "complete", "unresolvedGapIds": [], "knownOmissions": []},
        })

        domain_path = root / "domains" / f"{DOMAIN_ID}.json"
        domain = json.loads(domain_path.read_text())
        domain["componentIds"] = list(components)
        domain["operationIds"] = [OPERATION_ID]
        write_json(domain_path, domain)

        progress["pathReviews"][PATH_ID] = {
            "stage": "complete",
            "gates": {
                "canonicalPathValidated": True,
                "numberedSequenceGenerated": True,
                "asciiDiagramGenerated": True,
                "projectionsValidated": True,
            },
        }
        write_json(progress_path, progress)
        render(root)
        return root

    def mutate_json(self, path, callback):
        document = json.loads(path.read_text())
        callback(document)
        write_json(path, document)

    def assert_invalid(self, root, pattern):
        build_index(root)
        with self.assertRaisesRegex(ValueError, pattern):
            validate(root)

    def test_init_creates_sharded_index_and_rejects_incomplete_final_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.initialized(directory)
            self.assertTrue((root / "index.json").is_file())
            self.assertNotIn("nodes", json.loads((root / "index.json").read_text()))
            validate(root, allow_incomplete=True)
            with self.assertRaisesRegex(ValueError, "source is not complete"):
                validate(root)

    def test_complete_sharded_model_validates(self):
        with tempfile.TemporaryDirectory() as directory:
            validate(self.complete_model(self.initialized(directory)))

    def test_index_contains_only_references_hashes_and_hierarchy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            index = json.loads((root / "index.json").read_text())
            component_entry = index["artifacts"]["components"]["component.api.submit-handler"]
            self.assertEqual({"path", "semanticHash", "contentHash"}, set(component_entry))
            self.assertEqual([OPERATION_ID], index["hierarchy"]["domains"][DOMAIN_ID]["operationIds"])
            self.assertNotIn("responsibility", json.dumps(index))

    def test_rejects_stale_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "components" / "component.api.submit-handler.json"
            self.mutate_json(path, lambda value: value.update(name="Changed"))
            with self.assertRaisesRegex(ValueError, "index.json: stale"):
                validate(root)

    def test_rejects_invalid_relationship_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "relationships" / "relationship.api.write-orders.json"
            self.mutate_json(path, lambda value: value.update(toId="store.missing"))
            self.assert_invalid(root, "endpoints must resolve")

    def test_rejects_invalid_node_kind(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "nodes" / "runtime.api.json"
            self.mutate_json(path, lambda value: value.update(kind="blob"))
            self.assert_invalid(root, "kind: invalid value")

    def test_rejects_nonreciprocal_component_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "components" / "component.api.submit-handler.json"
            self.mutate_json(path, lambda value: value.update(operationIds=[]))
            self.assert_invalid(root, "not reciprocal")

    def test_rejects_extra_participant(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "operations" / OPERATION_ID / "paths" / f"{PATH_ID}.json"
            self.mutate_json(path, lambda value: value["participants"].append({"id": "store.extra", "role": "Unused"}))
            self.assert_invalid(root, "does not resolve|participants must exactly")

    def test_rejects_non_stage_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "operations" / OPERATION_ID / "paths" / f"{PATH_ID}.json"
            def mutate(value):
                value["sequence"][0] = {
                    "number": "1", "kind": "local-operation", "at": "runtime.api",
                    "operation": "Invalid root", "input": "x", "output": "y", "boundary": "in-process",
                    "continuation": "continue", "certainty": "observed",
                    "sourceFindings": self.findings(), "evidence": self.evidence(),
                }
            self.mutate_json(path, mutate)
            self.assert_invalid(root, "root sequence records must be stages")

    def test_rejects_noncontiguous_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "operations" / OPERATION_ID / "paths" / f"{PATH_ID}.json"
            self.mutate_json(path, lambda value: value["sequence"][2].update(number="1.3"))
            self.assert_invalid(root, "not contiguous|must be unique")

    def test_rejects_reversed_caller_relationship(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "relationships" / "relationship.client.submit-order.json"
            self.mutate_json(path, lambda value: value.update(fromId="runtime.api", toId="runtime.client"))
            self.assert_invalid(root, "caller relationship direction")

    def test_rejects_reversed_step_relationship(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "relationships" / "relationship.api.write-orders.json"
            self.mutate_json(path, lambda value: value.update(fromId="store.orders", toId="runtime.api"))
            self.assert_invalid(root, "direction is incompatible")

    def test_rejects_nonterminal_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "operations" / OPERATION_ID / "paths" / f"{PATH_ID}.json"
            self.mutate_json(path, lambda value: value["outcome"].update(at="1.2"))
            self.assert_invalid(root, "must reference a terminal step")

    def test_rejects_complete_coverage_with_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "operations" / OPERATION_ID / "paths" / f"{PATH_ID}.json"
            self.mutate_json(path, lambda value: value["coverage"]["knownOmissions"].append("Skipped branch"))
            self.assert_invalid(root, "complete paths cannot")

    def test_render_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            projection = root / "projections" / OPERATION_ID / PATH_ID / "sequence-diagram.txt"
            first = projection.read_bytes()
            render(root)
            second = projection.read_bytes()
            self.assertEqual(first, second)

    def test_projection_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            projection = root / "projections" / OPERATION_ID / PATH_ID / "sequence-diagram.txt"
            projection.write_text(projection.read_text().replace("Stores the accepted order", "Writes something"))
            build_index(root)
            with self.assertRaisesRegex(ValueError, "differs from deterministic rendering"):
                validate(root)

    def test_set_like_order_does_not_change_canonical_bytes(self):
        left = {"componentIds": ["component.z", "component.a"]}
        right = {"componentIds": ["component.a", "component.z"]}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))

    def test_diff_separates_semantic_and_evidence_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            before = Path(directory) / "before.json"
            before.write_bytes((root / "index.json").read_bytes())
            component = root / "components" / "component.api.submit-handler.json"
            self.mutate_json(component, lambda value: value["evidence"][0].update(lineStart=10, lineEnd=12))
            build_index(root)
            evidence_diff = diff_indexes(before, root / "index.json")
            self.assertIn("components:component.api.submit-handler", evidence_diff["evidenceOnlyChanges"])
            self.mutate_json(component, lambda value: value.update(responsibility="Coordinates validation and storage"))
            build_index(root)
            semantic_diff = diff_indexes(before, root / "index.json")
            self.assertIn("components:component.api.submit-handler", semantic_diff["semanticChanges"])

    def test_format_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            format_model(root)
            first = (root / "index.json").read_bytes()
            format_model(root)
            self.assertEqual(first, (root / "index.json").read_bytes())

    def test_rejects_nondeterministic_participant_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "operations" / OPERATION_ID / "paths" / f"{PATH_ID}.json"
            self.mutate_json(path, lambda value: value["participants"].reverse())
            self.assert_invalid(root, "first endpoint appearance order")

    def test_rejects_ad_hoc_source_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "nodes" / "runtime.api.json"
            self.mutate_json(path, lambda value: value.update(sourceFindings=["not-structured"]))
            self.assert_invalid(root, "must be an object")

    def test_rejects_unresolved_local_source_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            path = root / "nodes" / "runtime.api.json"
            self.mutate_json(path, lambda value: value["sourceFindings"][0].update(unitId="missing-unit"))
            self.assert_invalid(root, "unitId: does not resolve")

    def test_revision_and_line_changes_preserve_model_semantic_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.complete_model(self.initialized(directory))
            before = json.loads((root / "index.json").read_text())["modelSemanticHash"]
            scan_path = root / "sources" / SOURCE_ID / "scan.json"
            self.mutate_json(scan_path, lambda value: value["source"].update(revision="def456"))
            progress_path = root / "progress.json"
            self.mutate_json(progress_path, lambda value: value["sources"][SOURCE_ID].update(revision="def456"))
            node_path = root / "nodes" / "runtime.api.json"
            self.mutate_json(node_path, lambda value: value["evidence"][0].update(lineStart=20, lineEnd=25))
            build_index(root)
            after = json.loads((root / "index.json").read_text())["modelSemanticHash"]
            self.assertEqual(before, after)
            validate(root)

    def test_machine_readable_evals_have_verifiable_expectations(self):
        document = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual("build-architecture-model", document["skill_name"])
        self.assertGreaterEqual(len(document["evals"]), 6)
        self.assertEqual(len(document["evals"]), len({item["id"] for item in document["evals"]}))
        for item in document["evals"]:
            self.assertTrue(item["prompt"])
            self.assertTrue(item["expected_output"])
            self.assertGreaterEqual(len(item["expectations"]), 4)

    def test_committed_example_is_complete_and_valid(self):
        validate(long_path(ROOT / "examples" / "order-submission" / ".architecture-model"))

    def test_standard_library_only(self):
        tree = ast.parse((ROOT / "scripts" / "architecture_model.py").read_text())
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue(roots <= set(sys.stdlib_module_names), roots - set(sys.stdlib_module_names))


if __name__ == "__main__":
    unittest.main()

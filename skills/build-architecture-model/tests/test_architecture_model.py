from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from architecture_model import compile_model, init_model, validate_canonical, validate_scan, write_json  # noqa: E402


def evidence(path: str, observation: str) -> list[dict]:
    return [{"path": path, "observation": observation}]


def base_scan(source_id: str, unit_id: str, unit: dict) -> dict:
    return {
        "schemaVersion": 1,
        "source": {
            "id": source_id,
            "path": f"../{source_id}",
            "repository": f"https://example/{source_id}.git",
            "revision": f"revision-{source_id}",
            "branch": "main",
            "scanStatus": "complete",
            "coverage": {"included": ["**/*"], "excluded": ["bin/**"], "limitations": []},
        },
        "units": {unit_id: unit},
        "operations": {},
        "gaps": [],
    }


def runtime(name: str, deployment: str, subtype: str = "api") -> dict:
    return {
        "kind": "runtime",
        "subtype": subtype,
        "name": name,
        "responsibility": f"Runs {name}",
        "technology": [".NET 8"],
        "identity": {"deploymentIdentity": deployment},
        "inbound": [],
        "outbound": [],
        "evidence": evidence("src/Program.cs", f"Starts {name}"),
    }


class ScanValidationTests(unittest.TestCase):
    def test_bundled_agent_template_is_valid(self) -> None:
        template = json.loads((SKILL_DIR / "assets" / "scan-template.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_scan(template, "scan-template.json"))

    def test_evidence_is_mandatory(self) -> None:
        unit = runtime("Orders API", "orders-api")
        unit["evidence"] = []
        failures = validate_scan(base_scan("orders-api", "orders-api", unit))
        self.assertTrue(any("evidence must be a non-empty array" in item for item in failures))

    def test_operation_references_local_dependency(self) -> None:
        unit = runtime("Orders API", "orders-api")
        unit["inbound"] = [{
            "id": "submit-v2",
            "kind": "http",
            "purpose": "Submits an order",
            "method": "POST",
            "path": "/api/v2/orders",
            "version": "v2",
            "evidence": evidence("src/OrdersController.cs", "Defines POST /api/v2/orders"),
        }]
        unit["outbound"] = [{
            "id": "write-orders",
            "kind": "data",
            "purpose": "Stores accepted orders",
            "technology": "EF Core/SQL Server",
            "target": {"kind": "store", "server": "sales", "database": "Orders", "schema": "fulfilment"},
            "evidence": evidence("src/OrdersDbContext.cs", "Writes accepted orders"),
        }]
        scan = base_scan("orders-api", "orders-api", unit)
        scan["operations"] = {
            "submit-order": {
                "name": "Submit order",
                "owner": "orders-api",
                "trigger": "submit-v2",
                "steps": [
                    {"order": 1, "at": "orders-api", "action": "Validates order", "evidence": evidence("src/SubmitHandler.cs", "Validates the command")},
                    {"order": 2, "uses": "write-orders", "action": "Stores order", "evidence": evidence("src/SubmitHandler.cs", "Persists the order")},
                ],
            }
        }
        self.assertEqual([], validate_scan(scan))


class CompilationTests(unittest.TestCase):
    def model(self, scans: dict[str, dict]) -> dict:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "model"
        init_model(root, "Orders", [scan["source"]["path"] for scan in scans.values()])
        for filename, scan in scans.items():
            write_json(root / "scans" / filename, scan)
        return compile_model(root)

    def test_shared_logical_database_is_one_node_with_separate_directions(self) -> None:
        api = runtime("Orders API", "orders-api")
        worker = runtime("Orders Worker", "orders-worker", "worker")
        target = {"kind": "store", "technology": "SQL Server", "server": "sales", "database": "Orders", "schema": "fulfilment"}
        api["outbound"] = [{
            "id": "write-orders", "kind": "data", "purpose": "Writes orders", "technology": "EF Core/SQL Server",
            "target": target, "evidence": evidence("src/OrdersDbContext.cs", "Writes Orders.fulfilment"),
        }]
        worker["outbound"] = [{
            "id": "read-orders", "kind": "data", "purpose": "Reads pending orders", "technology": "Dapper/SQL Server",
            "target": deepcopy(target), "evidence": evidence("src/OrderReader.cs", "Reads Orders.fulfilment"),
        }]
        model = self.model({
            "api.json": base_scan("orders-api", "orders-api", api),
            "worker.json": base_scan("orders-worker", "orders-worker", worker),
        })
        stores = [node_id for node_id, node in model["nodes"].items() if node["kind"] == "store"]
        self.assertEqual(1, len(stores))
        database_edges = [edge for edge in model["relationships"].values() if edge["to"] == stores[0]]
        self.assertEqual({"Writes orders", "Reads pending orders"}, {edge["purpose"] for edge in database_edges})
        self.assertEqual([], validate_canonical(model))

    def test_duplicate_outbound_observations_merge_with_both_findings(self) -> None:
        first = runtime("Orders API", "orders-api")
        second = runtime("Orders API", "orders-api")
        dependency = {
            "id": "write-orders", "kind": "data", "purpose": "Writes orders", "technology": "SQL Server",
            "target": {"kind": "store", "server": "sales", "database": "Orders", "schema": "fulfilment"},
            "evidence": evidence("src/OrdersDb.cs", "Writes Orders.fulfilment"),
        }
        first["outbound"] = [deepcopy(dependency)]
        second["outbound"] = [deepcopy(dependency)]
        model = self.model({
            "api-source.json": base_scan("orders-api-source", "orders-api", first),
            "api-deploy.json": base_scan("orders-api-deploy", "orders-api", second),
        })
        self.assertEqual(1, len(model["relationships"]))
        relationship = next(iter(model["relationships"].values()))
        self.assertEqual(2, len(relationship["sourceFindings"]))
        self.assertEqual("corroborated", relationship["certainty"])

    def test_same_server_with_different_schemas_remains_separate(self) -> None:
        api = runtime("Orders API", "orders-api")
        api["outbound"] = []
        for schema in ("fulfilment", "billing"):
            api["outbound"].append({
                "id": f"write-{schema}", "kind": "data", "purpose": f"Writes {schema}", "technology": "SQL Server",
                "target": {"kind": "store", "server": "sales", "database": "Orders", "schema": schema},
                "evidence": evidence("src/Db.cs", f"Uses schema {schema}"),
            })
        model = self.model({"api.json": base_scan("orders-api", "orders-api", api)})
        self.assertEqual(2, len([node for node in model["nodes"].values() if node["kind"] == "store"]))

    def test_http_caller_is_corroborated_only_from_outbound_evidence(self) -> None:
        api = runtime("Orders API", "orders-api")
        api["inbound"] = [{
            "id": "submit-v2", "kind": "http", "purpose": "Submits orders", "method": "POST", "path": "/api/v2/orders", "version": "v2",
            "contract": {"name": "SubmitOrder", "version": "v2", "fingerprint": "sha256:abc"},
            "evidence": evidence("src/OrdersController.cs", "Defines the v2 endpoint"),
        }]
        mfe = runtime("Orders MFE", "orders-mfe", "mfe")
        mfe["technology"] = ["React"]
        mfe["outbound"] = [{
            "id": "submit-order-v2", "kind": "request", "purpose": "Submits orders", "technology": "HTTPS/JSON",
            "target": {"kind": "runtime", "deploymentIdentity": "orders-api", "name": "Orders API"},
            "interface": {"method": "POST", "path": "/api/v2/orders", "version": "v2"},
            "contract": {"name": "SubmitOrder", "version": "v2", "fingerprint": "sha256:abc"},
            "evidence": evidence("src/ordersClient.ts", "Calls POST /api/v2/orders"),
        }]
        model = self.model({
            "api.json": base_scan("orders-api", "orders-api", api),
            "mfe.json": base_scan("orders-mfe", "orders-mfe", mfe),
        })
        relationships = list(model["relationships"].values())
        self.assertEqual(1, len(relationships))
        self.assertEqual("corroborated", relationships[0]["certainty"])
        self.assertIn("destinationInterface", relationships[0])

    def test_incompatible_api_versions_do_not_corroborate(self) -> None:
        api = runtime("Orders API", "orders-api")
        api["inbound"] = [{
            "id": "submit-v2", "kind": "http", "purpose": "Submits orders", "method": "POST", "path": "/api/orders", "version": "v2",
            "contract": {"name": "SubmitOrder", "version": "v2"},
            "evidence": evidence("src/OrdersController.cs", "Defines the v2 endpoint"),
        }]
        mfe = runtime("Legacy Orders MFE", "legacy-orders-mfe", "mfe")
        mfe["technology"] = ["React"]
        mfe["outbound"] = [{
            "id": "submit-v1", "kind": "request", "purpose": "Submits orders", "technology": "HTTPS/JSON",
            "target": {"kind": "runtime", "deploymentIdentity": "orders-api", "name": "Orders API"},
            "interface": {"method": "POST", "path": "/api/orders", "version": "v1"},
            "contract": {"name": "SubmitOrder", "version": "v1"},
            "evidence": evidence("src/ordersClient.ts", "Calls the v1 endpoint"),
        }]
        model = self.model({
            "api.json": base_scan("orders-api", "orders-api", api),
            "mfe.json": base_scan("legacy-orders-mfe", "legacy-orders-mfe", mfe),
        })
        relationship = next(iter(model["relationships"].values()))
        self.assertEqual("conflicting", relationship["certainty"])
        self.assertNotIn("destinationInterface", relationship)
        self.assertTrue(any(item["kind"] == "interface-version" for item in model["conflicts"].values()))

    def test_incompatible_event_versions_become_conflicts(self) -> None:
        api = runtime("Orders API", "orders-api")
        api["outbound"] = [{
            "id": "publish-order-v3", "kind": "event", "purpose": "Publishes accepted orders", "technology": "MassTransit/Azure Service Bus",
            "target": {"kind": "channel", "transport": "Azure Service Bus", "namespace": "sales", "topic": "order-submitted"},
            "contract": {"name": "OrderSubmitted", "version": "v3", "fingerprint": "sha256:v3"},
            "evidence": evidence("src/SubmitOrderHandler.cs", "Publishes OrderSubmitted v3"),
        }]
        worker = runtime("Search Worker", "search-worker", "worker")
        worker["inbound"] = [{
            "id": "consume-order-v2", "kind": "event", "purpose": "Indexes orders", "version": "v2",
            "channel": {"technology": "MassTransit", "transport": "Azure Service Bus", "namespace": "sales", "topic": "order-submitted", "subscription": "search"},
            "contract": {"name": "OrderSubmitted", "version": "v2", "fingerprint": "sha256:v2"},
            "evidence": evidence("src/OrderSubmittedConsumer.cs", "Consumes OrderSubmitted v2"),
        }]
        model = self.model({
            "api.json": base_scan("orders-api", "orders-api", api),
            "worker.json": base_scan("search-worker", "search-worker", worker),
        })
        self.assertTrue(any(item["kind"] == "contract-version" for item in model["conflicts"].values()))
        event_edges = [edge for edge in model["relationships"].values() if edge["kind"] in {"event", "message-delivery"}]
        self.assertEqual({"conflicting"}, {edge["certainty"] for edge in event_edges})

    def test_compilation_is_independent_of_scan_filename_order(self) -> None:
        api = runtime("Orders API", "orders-api")
        worker = runtime("Orders Worker", "orders-worker", "worker")
        target = {"kind": "store", "server": "sales", "database": "Orders", "schema": "fulfilment"}
        api["outbound"] = [{
            "id": "write-orders", "kind": "data", "purpose": "Writes orders", "technology": "SQL Server",
            "target": deepcopy(target), "evidence": evidence("src/Db.cs", "Writes orders"),
        }]
        worker["outbound"] = [{
            "id": "read-orders", "kind": "data", "purpose": "Reads orders", "technology": "SQL Server",
            "target": deepcopy(target), "evidence": evidence("src/Db.cs", "Reads orders"),
        }]
        first = self.model({
            "z-api.json": base_scan("orders-api", "orders-api", api),
            "a-worker.json": base_scan("orders-worker", "orders-worker", worker),
        })
        second = self.model({
            "a-api.json": base_scan("orders-api", "orders-api", api),
            "z-worker.json": base_scan("orders-worker", "orders-worker", worker),
        })
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Run deterministic checks for the map-to-c4 evaluation suite.

The Markdown files are reasoning evals for an agent/model. This runner verifies
that the full suite remains linked and sourced, then exercises the renderer and
package validator contracts that can be tested without invoking a model.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

EVAL_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVAL_DIR.parent
SCRIPT_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from render_c4 import html_page, render, validate  # noqa: E402
from validate_c4_package import validate_diagram_page, validate_index  # noqa: E402
from validate_canonical_projection import validate_view as validate_canonical_view  # noqa: E402

REQUIRED_SOURCES = {
    "https://c4model.com/introduction",
    "https://c4model.com/abstractions",
    "https://c4model.com/abstractions/software-system",
    "https://c4model.com/abstractions/container",
    "https://c4model.com/abstractions/component",
    "https://c4model.com/abstractions/code",
    "https://c4model.com/abstractions/microservices",
    "https://c4model.com/abstractions/queues-and-topics",
    "https://c4model.com/abstractions/faq",
    "https://c4model.com/diagrams",
    "https://c4model.com/diagrams/system-context",
    "https://c4model.com/diagrams/container",
    "https://c4model.com/diagrams/component",
    "https://c4model.com/diagrams/code",
    "https://c4model.com/diagrams/system-landscape",
    "https://c4model.com/diagrams/dynamic",
    "https://c4model.com/diagrams/deployment",
    "https://c4model.com/diagrams/notation",
    "https://c4model.com/diagrams/checklist",
    "https://c4model.com/diagrams/faq",
    "https://c4model.com/tooling",
    "https://c4model.com/faq",
}


def base_views() -> dict[str, dict]:
    context = {
        "id": "eval-context",
        "title": "System Context diagram — Orders",
        "diagramType": "System Context",
        "description": "Customers place orders.",
        "scope": {"id": "system-orders", "name": "Orders", "type": "Software System", "description": "Accepts and fulfils orders."},
        "elements": [{"id": "person-customer", "name": "Customer", "type": "Person", "description": "Places an order."}],
        "relationships": [{"id": "rel-customer-orders", "source": "person-customer", "destination": "system-orders", "description": "Places orders"}],
        "navigation": [],
        "links": [],
    }
    container = {
        "id": "eval-containers",
        "title": "Container diagram — Orders",
        "diagramType": "Container",
        "description": "The web application accepts customer orders.",
        "scope": {"id": "system-orders", "name": "Orders", "type": "Software System", "description": "Accepts and fulfils orders."},
        "elements": [
            {"id": "container-web", "name": "Web Application", "type": "Container: Application", "description": "Accepts customer orders.", "technology": "Python", "insideScope": True},
            {"id": "person-customer", "name": "Customer", "type": "Person", "description": "Places an order.", "insideScope": False},
        ],
        "relationships": [{"id": "rel-customer-web", "source": "person-customer", "destination": "container-web", "description": "Places orders", "technology": "HTTPS"}],
        "navigation": [],
        "links": [],
    }
    component = {
        "id": "eval-components",
        "title": "Component diagram — Web Application",
        "diagramType": "Component",
        "description": "The order component validates orders.",
        "scope": {"id": "container-web", "name": "Web Application", "type": "Container", "description": "Accepts customer orders.", "technology": "Python"},
        "elements": [
            {"id": "component-orders", "name": "Order Component", "type": "Component", "description": "Validates orders behind an interface.", "technology": "Python", "insideScope": True},
            {"id": "container-db", "name": "Orders Database", "type": "Container: Data Store", "description": "Stores accepted orders.", "technology": "PostgreSQL", "insideScope": False},
        ],
        "relationships": [{"id": "rel-component-db", "source": "component-orders", "destination": "container-db", "description": "Stores accepted orders", "technology": "SQL/TLS"}],
        "navigation": [],
        "links": [],
    }
    code = {
        "id": "eval-code",
        "title": "Code diagram — Order Component",
        "diagramType": "Code",
        "description": "Observed classes implementing order validation.",
        "scope": {"id": "component-orders", "name": "Order Component", "type": "Component", "description": "Validates orders behind an interface.", "technology": "Python"},
        "elements": [
            {"id": "code-handler", "name": "OrderHandler", "type": "Class", "description": "Coordinates order validation.", "insideScope": True},
            {"id": "code-validator", "name": "OrderValidator", "type": "Class", "description": "Validates an order.", "insideScope": True},
        ],
        "relationships": [{"id": "rel-handler-validator", "source": "code-handler", "destination": "code-validator", "description": "Delegates validation"}],
        "navigation": [],
        "links": [],
    }
    return {"context": context, "containers": container, "components": component, "code": code}


class EvalSuiteIntegrityTests(unittest.TestCase):
    def test_every_eval_is_linked_and_has_a_rubric(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        linked = set(re.findall(r"evals/([a-z0-9-]+\.md)", skill))
        present = {path.name for path in EVAL_DIR.glob("*.md") if path.name != "README.md"}
        self.assertEqual(present, linked)
        for name in sorted(present):
            text = (EVAL_DIR / name).read_text(encoding="utf-8")
            self.assertIn("## Official sources", text, name)
            self.assertIn("## Prompt", text, name)
            self.assertRegex(text, r"## Required (?:outcome|classification)")
            self.assertIn("## Fail conditions", text, name)
            self.assertRegex(text, r"(?m)^- https://c4model\.com/", name)

    def test_normative_site_topics_are_covered(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in EVAL_DIR.glob("*.md"))
        covered = set(re.findall(r"https://c4model\.com/[a-z0-9/-]+", text))
        self.assertEqual(set(), REQUIRED_SOURCES - covered)


class RendererSemanticsTests(unittest.TestCase):
    def test_all_core_levels_render_connected_annotated_svg(self) -> None:
        for name, view in base_views().items():
            with self.subTest(view=name):
                svg = render(view)
                root = ET.fromstring(svg)
                elements = [node for node in root.iter() if node.attrib.get("data-c4-element-id")]
                relationships = [node for node in root.iter() if node.attrib.get("data-c4-relationship-id")]
                self.assertEqual(len(view["elements"]) + 1, len(elements))
                self.assertEqual(len(view["relationships"]), len(relationships))
                self.assertTrue(all(any("marker-end" in child.attrib for child in node.iter()) for node in relationships))
                self.assertTrue(all(node.attrib.get("data-label") for node in relationships))

    def test_level_mixing_and_pseudo_groups_are_rejected(self) -> None:
        invalid = deepcopy(base_views()["containers"])
        invalid["elements"][0]["type"] = "Component"
        with self.assertRaisesRegex(ValueError, "in-scope elements must be Containers"):
            validate(invalid)
        invalid = deepcopy(base_views()["context"])
        invalid["elements"][0]["type"] = "Software System group"
        with self.assertRaisesRegex(ValueError, "pseudo-group"):
            validate(invalid)

    def test_context_detail_and_indirect_neighbours_are_rejected(self) -> None:
        invalid = deepcopy(base_views()["context"])
        invalid["relationships"][0]["technology"] = "HTTPS"
        with self.assertRaisesRegex(ValueError, "must omit technology"):
            validate(invalid)
        invalid = deepcopy(base_views()["context"])
        invalid["elements"].append({"id": "system-payments", "name": "Payments", "type": "Software System", "description": "Takes payments."})
        with self.assertRaisesRegex(ValueError, "must connect directly"):
            validate(invalid)
        invalid["relationships"].extend([
            {"id": "rel-orders-payments", "source": "system-orders", "destination": "system-payments", "description": "Requests payment"},
            {"id": "rel-customer-payments", "source": "person-customer", "destination": "system-payments", "description": "Views payment"},
        ])
        with self.assertRaisesRegex(ValueError, "relationships must connect directly"):
            validate(invalid)

    def test_container_protocol_is_required(self) -> None:
        invalid = deepcopy(base_views()["containers"])
        invalid["relationships"][0].pop("technology")
        with self.assertRaisesRegex(ValueError, "technology/protocol is required"):
            validate(invalid)

    def test_component_and_code_scope_rules_are_rejected_when_mixed(self) -> None:
        invalid = deepcopy(base_views()["components"])
        invalid["elements"][0]["type"] = "Container"
        with self.assertRaisesRegex(ValueError, "in-scope elements must be Components"):
            validate(invalid)
        invalid = deepcopy(base_views()["code"])
        invalid["elements"][0]["insideScope"] = False
        with self.assertRaisesRegex(ValueError, "inside the scoped Component"):
            validate(invalid)

    def test_dynamic_interactions_require_unique_order_and_render_it(self) -> None:
        dynamic = deepcopy(base_views()["containers"])
        dynamic["id"] = "eval-dynamic"
        dynamic["title"] = "Dynamic diagram — Place order"
        dynamic["diagramType"] = "Dynamic"
        with self.assertRaisesRegex(ValueError, "order is required"):
            validate(dynamic)
        dynamic["relationships"][0]["order"] = 1
        svg = render(dynamic)
        self.assertIn(">1. Places orders [HTTPS]<", svg)
        self.assertIn('data-order="1"', svg)


class CanonicalProjectionTests(unittest.TestCase):
    def canonical_model(self) -> dict:
        return {
            "nodes": {
                "person-customer": {"name": "Customer", "kind": "person"},
                "container-web": {"name": "Web Application", "kind": "runtime"},
                "container-db": {"name": "Orders Database", "kind": "store"},
                "channel-orders": {"name": "Orders topic", "kind": "channel"},
                "container-worker": {"name": "Orders Worker", "kind": "runtime"},
            },
            "relationships": {
                "model-customer-web": {"from": "person-customer", "to": "container-web"},
                "model-web-channel": {"from": "container-web", "to": "channel-orders"},
                "model-channel-worker": {"from": "channel-orders", "to": "container-worker"},
            },
            "systemBoundaries": {
                "system-orders": {
                    "status": "confirmed",
                    "members": ["container-web", "container-db", "container-worker"],
                }
            },
        }

    def canonical_view(self, name: str) -> dict:
        view = deepcopy(base_views()[name])
        view["scope"]["modelBoundaryId"] = "system-orders"
        for element in view["elements"]:
            element["modelElementId"] = element["id"]
        view["relationships"][0]["modelRelationshipIds"] = ["model-customer-web"]
        return view

    def test_context_and_container_trace_to_confirmed_model(self) -> None:
        self.assertEqual([], validate_canonical_view(self.canonical_model(), self.canonical_view("context"), "context"))
        self.assertEqual([], validate_canonical_view(self.canonical_model(), self.canonical_view("containers"), "containers"))

    def test_unconfirmed_boundary_and_reverse_direction_fail(self) -> None:
        model = self.canonical_model()
        model["systemBoundaries"]["system-orders"]["status"] = "candidate"
        failures = validate_canonical_view(model, self.canonical_view("containers"), "containers")
        self.assertTrue(any("not confirmed" in failure for failure in failures))
        model["systemBoundaries"]["system-orders"]["status"] = "confirmed"
        model["relationships"]["model-customer-web"] = {"from": "container-web", "to": "person-customer"}
        failures = validate_canonical_view(model, self.canonical_view("containers"), "containers")
        self.assertTrue(any("do not support the rendered direction" in failure for failure in failures))

    def test_library_cannot_project_as_container(self) -> None:
        model = self.canonical_model()
        model["nodes"]["container-web"]["kind"] = "library"
        failures = validate_canonical_view(model, self.canonical_view("containers"), "containers")
        self.assertTrue(any("cannot be an in-scope Container" in failure for failure in failures))

    def test_condensed_event_path_can_retain_both_model_edges(self) -> None:
        view = deepcopy(base_views()["containers"])
        view["scope"]["modelBoundaryId"] = "system-orders"
        view["elements"] = [
            {"id": "container-web", "modelElementId": "container-web", "name": "Web", "type": "Container: Application", "description": "Publishes orders.", "technology": "Python", "insideScope": True},
            {"id": "container-worker", "modelElementId": "container-worker", "name": "Worker", "type": "Container: Application", "description": "Consumes orders.", "technology": "Python", "insideScope": True},
        ]
        view["relationships"] = [{
            "id": "view-web-worker", "source": "container-web", "destination": "container-worker",
            "description": "Publishes orders", "technology": "Topic", "modelRelationshipIds": ["model-web-channel", "model-channel-worker"],
        }]
        self.assertEqual([], validate_canonical_view(self.canonical_model(), view, "condensed"))


class PackageValidationTests(unittest.TestCase):
    def test_generated_core_package_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            links = []
            for stem, view in base_views().items():
                svg_name = f"{stem}.svg"
                (root / svg_name).write_text(render(view), encoding="utf-8")
                (root / f"{stem}.html").write_text(html_page(view, svg_name), encoding="utf-8")
                links.append(f'<a href="{stem}.html">{stem}</a>')
            (root / "index.html").write_text("<!doctype html><title>Orders architecture</title>" + "".join(links), encoding="utf-8")
            failures = validate_index(root)
            for page in sorted(root.glob("*.html")):
                if page.name != "index.html":
                    failures.extend(validate_diagram_page(page))
            self.assertEqual([], failures)

    def test_disconnected_cards_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "containers.html"
            page.write_text("<!doctype html><h1>Container diagram — Bad</h1><div>Container A</div><ul><li>→ Uses B</li></ul>", encoding="utf-8")
            failures = validate_diagram_page(page)
            self.assertTrue(any("no rendered SVG diagram" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main(verbosity=2)

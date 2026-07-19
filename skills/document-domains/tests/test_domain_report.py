import copy
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'domain_report', SKILL_DIR / 'scripts' / 'domain_report.py'
)
domain_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(domain_report)


def claim(name, description, evidence_id):
    return {
        'name': name,
        'description': description,
        'certainty': 'observed',
        'evidence_ids': [evidence_id],
    }


def operation(operation_id, component_id, name, entry_point, evidence_id, next_component=None):
    first = f'step-{operation_id.removeprefix("operation-")}-receive'
    second = f'step-{operation_id.removeprefix("operation-")}-complete'

            'handler': 'OrdersController.PlaceOrder', 'payload': 'PlaceOrderRequest',
            'ingress_path': ['Azure Front Door', 'API Management', 'Orders API'],
            'evidence_ids': [evidence_id], 'gap_ids': [],
        }

            'handler': 'OrderPlacedConsumer', 'payload': 'OrderPlacedEvent',
            'ingress_path': ['Azure Service Bus', 'Orders Worker'],
            'evidence_ids': [evidence_id], 'gap_ids': [],
        }
    return {
        'id': operation_id,
        'component_id': component_id,
        'name': name,
        'kind': 'message consumer',
        'direction': 'inbound',
        'entry_point': entry_point,
        'inbound_endpoint': inbound_endpoint,
        'description': f'{name} operation.',
        'summary': f'{name} from entry point to outcome.',
        'certainty': 'observed',
        'evidence_ids': [evidence_id],
        'preconditions': ['The entry-point contract is available.'],
        'steps': [
            {
                'id': first,
                'sequence': 1,
                'kind': 'entry point',
                'action': entry_point,
                'certainty': 'observed',
                'evidence_ids': [evidence_id],
                'component_id': component_id,
                'next_step_ids': [second],
            },
            {
                'id': second,
                'sequence': 2,
                'kind': 'outcome',
                'action': 'Complete the documented operation.',
                'certainty': 'observed',
                'evidence_ids': [evidence_id],
                'component_id': next_component or component_id,
                'next_step_ids': [],
            },
        ],
        'outcomes': [claim('Completed', 'The operation reaches its documented outcome.', evidence_id)],
        'failure_paths': [],
        'gap_ids': [],
    }


def fixture_manifest():

    manifest['evidence'] = [{
        'id': evidence_id,
        'root_id': 'root-fixture',
        'path': 'src/orders.md',
        'observation': 'The fixture establishes two component operations.',
        'source_kind': 'implementation',
        'reliability': 'direct',
        'freshness': 'current',
    }]
    manifest['components'] = [
        {
            'id': 'component-orders-api',
            'name': 'Orders API',
            'kind': 'HTTP API',
            'root_id': 'root-fixture',
            'description': 'Accepts order placement requests.',
            'certainty': 'observed',
            'evidence_ids': [evidence_id],
        },
        {
            'id': 'component-orders-worker',
            'name': 'Orders Worker',

        },
    ]
    manifest['operations'] = [
        operation(
            'operation-place-order', 'component-orders-api', 'Place order',
            'POST /orders', evidence_id,

    ]
    manifest['connections'] = [{

        'certainty': 'observed',
        'rationale': 'The API publishes the event consumed by the worker.',

        'stages': [
            {
                'id': 'stage-accept-order',
                'sequence': 1,
                'title': 'Accept order',
                'description': 'Accept the HTTP request.',
                'certainty': 'observed',
                'evidence_ids': [evidence_id],
                'operation_id': 'operation-place-order',

    return manifest


class DomainReportContractTests(unittest.TestCase):
    def test_fixture_validates(self):
        errors, warnings = domain_report.validate(fixture_manifest())
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_renderer_uses_domain_component_operation_hierarchy(self):
        manifest = fixture_manifest()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.html'
            domain_report.render(manifest, output)
            page = output.read_text(encoding='utf-8')

        top_nav = re.search(r'<body>.*?<nav>(.*?)</nav>', page, re.DOTALL).group(1)
        self.assertIn("href='#domain'", top_nav)
        self.assertIn("href='#section-component-orders-api'", top_nav)
        self.assertIn("href='#section-component-orders-worker'", top_nav)
        self.assertNotIn("href='#issues'", top_nav)
        self.assertNotIn("href='#evidence'", top_nav)

        self.assertIn('Table of contents', page)

        self.assertIn('orders-worker', page)
        self.assertIn('OrdersController.PlaceOrder', page)
        self.assertIn('Azure Front Door → API Management → Orders API', page)

    def test_validator_rejects_vague_operation_entry_point(self):
        manifest = fixture_manifest()
        manifest['operations'][0]['entry_point'] = 'Authenticated request'
        errors, _ = domain_report.validate(manifest)
        self.assertTrue(any('no concrete actor' in error for error in errors))

    def test_renderer_omits_unknown_endpoint_fields(self):
        manifest = fixture_manifest()
        manifest['gaps'] = [{
            'id': 'gap-endpoint-transport', 'scope_ref': 'operation-place-order',
            'kind': 'inbound endpoint', 'description': 'Transport is not established.',
            'impact': 'Delivery configuration is incomplete.', 'searches': ['src/orders.md'],
            'status': 'open',
        }]
        endpoint = manifest['operations'][0]['inbound_endpoint']
        endpoint['transport'] = 'unknown'
        endpoint['gap_ids'] = ['gap-endpoint-transport']
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.html'
            domain_report.render(manifest, output)
            page = output.read_text(encoding='utf-8')
        self.assertNotIn('<dd>unknown</dd>', page)
        self.assertIn("href='#gap-endpoint-transport'", page)
        self.assertIn('Incomplete endpoint evidence', page)

    def test_validator_rejects_unknown_endpoint_without_gap(self):
        manifest = fixture_manifest()
        manifest['operations'][0]['inbound_endpoint']['transport'] = 'unknown'
        errors, _ = domain_report.validate(manifest)


    def test_schema_excludes_legacy_collections(self):
        manifest = fixture_manifest()

        self.assertNotIn('domain_journeys', manifest)


if __name__ == '__main__':
    unittest.main()

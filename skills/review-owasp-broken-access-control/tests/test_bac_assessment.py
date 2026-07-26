from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "bac_assessment.py"
TEMPLATE_PATH = SKILL_DIR / "assets" / "assessment-template.json"
SPEC = importlib.util.spec_from_file_location("bac_assessment", SCRIPT_PATH)
assert SPEC and SPEC.loader
bac = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bac)


class AssessmentTests(unittest.TestCase):
    def template(self):
        return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    def completed_without_findings(self):
        data = self.template()
        data["assessment"].update(
            {
                "subject": "Invoice API",
                "revision": "abc123",
                "assessmentDate": "2026-07-24",
                "scope": ["src/Invoice.Api"],
                "limitations": [],
                "summary": "No supported broken-access-control finding was identified in the reviewed scope.",
            }
        )
        data["authorizationModel"] = {
            "actors": ["anonymous", "invoice owner", "peer user"],
            "resources": ["invoice"],
            "actions": ["read"],
            "contexts": ["same tenant"],
            "enforcementPoints": ["invoice query policy"],
            "policyStatements": ["Only an invoice owner may read an invoice."],
            "accessPaths": [
                {
                    "id": "PATH-001",
                    "entryPoint": "GET /api/invoices/{invoiceId}",
                    "methodsOrOperations": ["GET"],
                    "channel": "primary API v1",
                    "authentication": "authenticated session",
                    "actors": ["invoice owner", "peer user"],
                    "resource": "invoice",
                    "actions": ["read"],
                    "inputVectors": ["path.invoiceId", "session subject", "tenant claim"],
                    "traceStatus": "complete",
                    "gapIds": [],
                    "tiers": [
                        {
                            "name": "Authenticated invoice endpoint and scoped query",
                            "type": "application",
                            "component": "Invoice API",
                            "entryIdentity": "authenticated session subject with tenant claim",
                            "exitIdentity": "same originating subject",
                            "credentials": ["session cookie"],
                            "policies": ["fallback authentication", "owner and tenant query scope"],
                            "resourceContext": ["invoiceId", "subjectId", "tenantId"],
                            "decision": "Loads and returns only the subject-owned invoice in the subject tenant.",
                            "status": "verified",
                            "evidence": [
                                {
                                    "kind": "source",
                                    "location": "src/Invoices/GetInvoice.cs:1-60",
                                    "observation": "The endpoint and query use the authenticated subject and tenant.",
                                    "revision": "abc123"
                                }
                            ]
                        }
                    ],
                    "evidence": [
                        {
                            "kind": "source",
                            "location": "src/Invoices/GetInvoice.cs:1-60",
                            "observation": "The route and handler define the invoice read path.",
                            "revision": "abc123"
                        }
                    ]
                }
            ],
        }
        for branch in data["coverage"]:
            branch.update(
                {
                    "status": "not-applicable",
                    "rationale": "The reviewed subject has no applicable surface for this branch in this fixture.",
                    "evidence": [],
                    "findingIds": [],
                }
            )
        data["gaps"] = []
        return data

    def evidence(self):
        return {
            "kind": "source",
            "location": "src/Invoices/GetInvoice.cs:42-58 (Handle)",
            "observation": "The query loads by caller-controlled invoice ID without owner or tenant scope.",
            "revision": "abc123",
        }

    def finding(self):
        return {
            "id": "BAC-001",
            "title": "Users can read another user's invoice by changing its identifier",
            "category": "Object-Level Authorization — IDOR / BOLA",
            "component": "Billing API",
            "classification": "Horizontal privilege escalation",
            "status": "confirmed",
            "severity": "high",
            "confidence": "high",
            "summary": "An authenticated peer can retrieve invoices they do not own.",
            "actor": "authenticated peer user",
            "resource": "another user's invoice",
            "action": "read",
            "affectedImplementation": {
                "controllers": ["InvoiceController"],
                "classes": ["InvoiceService"],
                "methods": ["getInvoice(invoiceId)"],
                "endpoints": ["GET /api/invoices/{invoiceId}"],
                "filesOrArtifacts": ["src/Invoices/GetInvoice.cs"],
            },
            "expectedAccessRule": {
                "summary": "Only the owner or an explicitly authorized support role may read an invoice.",
                "language": "pseudo",
                "pseudocode": "allow when invoice.ownerId == subject.id\n  or subject.hasPermission('invoice-support')\notherwise deny",
            },
            "exercise": {
                "summary": "Use synthetic peer accounts and records in an authorized test environment.",
                "language": "http",
                "pseudocode": "GET /api/invoices/INV-B\nAuthorization: Bearer <user-a-test-token>\n\nexpected: 403 or 404\nobserved: 200 with User B invoice",
            },
            "failureProof": {
                "summary": "The handler uses the caller-controlled identifier without owner or tenant scope.",
                "language": "pseudo",
                "pseudocode": "invoiceId = request.path.invoiceId\ninvoice = store.findById(invoiceId)\n# no owner, tenant, or support-policy check\nreturn invoice",
            },
            "impact": {
                "summary": "The caller can disclose another user's billing and address information.",
                "language": "yaml",
                "pseudocode": "actor: authenticated peer user\naction: read\nresource: another user's invoice\nresult: billing data disclosure",
            },
            "remediation": {
                "summary": "Constrain retrieval by subject-derived tenant and ownership at the trusted data boundary.",
                "language": "pseudo",
                "pseudocode": "invoice = store.findAuthorized(\n  invoiceId, subject.id, subject.tenantId\n)\nif invoice is absent: deny\nreturn invoice",
            },
            "attackPath": [
                "A peer user authenticates and supplies another invoice identifier to GET /invoices/{id}.",
                "The handler loads and returns that invoice without checking ownership or tenant membership.",
            ],
            "evidence": [self.evidence()],
            "severityRationale": "Any ordinary account can repeatedly access sensitive peer records with a known identifier.",
            "coverageIds": ["A01-CV-03", "A01-PR-04"],
            "accessPathIds": ["PATH-001"],
            "mappings": {
                "owasp": ["A01:2025"],
                "asvs": ["ASVS 5.0.0-8.2.2"],
                "wstg": ["WSTG v4.2-ATHZ-04"],
                "apiTop10": ["API1:2023"],
                "cwe": ["CWE-639"],
            },
            "regressionTests": [
                {
                    "type": "allowed",
                    "description": "Request an invoice as its owner.",
                    "expected": "The owner receives the invoice.",
                },
                {
                    "type": "denied",
                    "description": "Request the same invoice as an authenticated peer and as a user from another tenant.",
                    "expected": "No invoice data or state is exposed and the attempt is denied and logged.",
                },
            ],
            "limitations": [],
        }

    def with_finding(self):
        data = self.completed_without_findings()
        tier = data["authorizationModel"]["accessPaths"][0]["tiers"][0]
        tier["policies"] = ["fallback authentication only"]
        tier["resourceContext"] = ["caller-controlled invoiceId"]
        tier["decision"] = "Loads by invoiceId without owner or tenant authorization and returns the record."
        finding = self.finding()
        data["findings"] = [finding]
        for branch in data["coverage"]:
            if branch["id"] in finding["coverageIds"]:
                branch.update(
                    {
                        "status": "finding",
                        "rationale": "The object lookup demonstrates a missing ownership check.",
                        "evidence": [self.evidence()],
                        "findingIds": [finding["id"]],
                    }
                )
        return data

    def test_starter_template_is_structurally_valid(self):
        self.assertEqual([], bac.validate_assessment(self.template()))

    def test_completed_assessment_without_findings_is_valid(self):
        self.assertEqual([], bac.validate_assessment(self.completed_without_findings()))

    def test_supported_idor_finding_is_valid_and_renders(self):
        data = self.with_finding()
        self.assertEqual([], bac.validate_assessment(data))
        report = bac.render_report(data)
        self.assertIn("BAC-001", report)
        self.assertIn("A01-CV-03", report)
        self.assertIn("A02–A10 were not comprehensively assessed", report)
        self.assertIn("API1:2023", report)
        self.assertIn("### Category: Object-Level Authorization — IDOR / BOLA", report)
        self.assertIn("#### Component: Billing API", report)
        self.assertIn("**Unauthorized scenario**", report)
        self.assertIn("```http", report)
        self.assertIn("**End-to-end authorization path**", report)
        self.assertIn("PATH-001 [complete]", report)

    def test_finding_requires_grouping_implementation_and_concise_issue_blocks(self):
        data = self.with_finding()
        finding = data["findings"][0]
        del finding["category"]
        finding["affectedImplementation"] = {key: [] for key in bac.AFFECTED_IMPLEMENTATION_FIELDS}
        finding["failureProof"]["pseudocode"] = "\n".join(f"line {number}" for number in range(13))
        errors = bac.validate_assessment(data)
        self.assertTrue(any("findings[0].category" in error for error in errors), errors)
        self.assertTrue(any("must identify at least one code or endpoint location" in error for error in errors), errors)
        self.assertTrue(any("failureProof.pseudocode must not exceed 12" in error for error in errors), errors)

    def test_missing_coverage_branch_fails(self):
        data = self.completed_without_findings()
        data["coverage"] = data["coverage"][:-1]
        errors = bac.validate_assessment(data)
        self.assertTrue(any("missing required coverage ids" in error for error in errors), errors)

    def test_recorded_review_requires_access_path_inventory(self):
        data = self.completed_without_findings()
        data["authorizationModel"]["accessPaths"] = []
        errors = bac.validate_assessment(data)
        self.assertIn(
            "authorizationModel.accessPaths must not be empty once review coverage is recorded",
            errors,
        )

    def test_access_path_requires_evidence_and_verified_end_to_end_tiers(self):
        data = self.completed_without_findings()
        path = data["authorizationModel"]["accessPaths"][0]
        path["evidence"] = []
        path["tiers"] = []
        errors = bac.validate_assessment(data)
        self.assertTrue(any("accessPaths[0].evidence must contain" in error for error in errors), errors)
        self.assertTrue(any("accessPaths[0].tiers must be a non-empty" in error for error in errors), errors)

    def test_complete_path_rejects_unverified_tier_or_gap(self):
        data = self.completed_without_findings()
        path = data["authorizationModel"]["accessPaths"][0]
        path["tiers"][0]["status"] = "unverified"
        path["gapIds"] = ["GAP-404"]
        errors = bac.validate_assessment(data)
        self.assertTrue(any("gapIds must be empty when traceStatus is complete" in error for error in errors), errors)
        self.assertTrue(any("tiers must all be verified" in error for error in errors), errors)

    def test_blocked_path_requires_reciprocal_awaiting_user_gap(self):
        data = self.completed_without_findings()
        path = data["authorizationModel"]["accessPaths"][0]
        path["traceStatus"] = "blocked"
        path["gapIds"] = ["GAP-001"]
        path["tiers"][0]["status"] = "unverified"
        path["tiers"][0]["evidence"] = []
        data["gaps"] = [{
            "id": "GAP-001",
            "title": "Effective gateway policy is unavailable",
            "whyItMatters": "The policy determines route reachability and identity propagation.",
            "searched": ["gateway and deployment configuration in the supplied repository"],
            "requestedArtifacts": ["Effective deployed gateway policy export"],
            "blockedConclusions": ["Whether the backend path is reachable by the peer actor"],
            "requestStatus": "awaiting-user",
            "userDecision": "Awaiting user direction.",
            "nextStep": "Provide the policy export or explicitly accept partial coverage.",
            "accessPathIds": ["PATH-001"],
            "coverageIds": ["A01-CV-02"],
        }]
        self.assertEqual([], bac.validate_assessment(data))
        html = bac.render_report(data, "html")
        self.assertIn("Trace completeness", html)
        self.assertIn("BLOCKED", html)
        self.assertIn("Requested artifacts or access", html)
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "blocked.json"
            output = Path(temp_dir) / "checkpoint.html"
            source.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(3, bac.command_render(source, output, "html"))
            self.assertFalse(output.exists())
            self.assertEqual(0, bac.command_render(source, output, "html", allow_blocked=True))
            self.assertTrue(output.exists())

    def test_confirmed_finding_requires_at_least_one_complete_path(self):
        data = self.with_finding()
        path = data["authorizationModel"]["accessPaths"][0]
        path["traceStatus"] = "blocked"
        path["gapIds"] = []
        path["tiers"][0]["status"] = "unverified"
        errors = bac.validate_assessment(data)
        self.assertTrue(any("confirmed finding BAC-001 must reference at least one complete" in error for error in errors), errors)

    def test_reviewed_no_finding_requires_evidence(self):
        data = self.completed_without_findings()
        data["coverage"][0]["status"] = "reviewed-no-finding"
        errors = bac.validate_assessment(data)
        self.assertTrue(any("must contain at least one evidence item" in error for error in errors), errors)

    def test_finding_reference_must_be_reciprocal(self):
        data = self.with_finding()
        data["coverage"][2]["findingIds"] = []
        errors = bac.validate_assessment(data)
        self.assertTrue(any("not reciprocally referenced" in error for error in errors), errors)

    def test_unknown_cwe_fails(self):
        data = self.with_finding()
        data["findings"][0]["mappings"]["cwe"] = ["CWE-999999"]
        errors = bac.validate_assessment(data)
        self.assertTrue(any("outside the bundled A01/API cross-references" in error for error in errors), errors)

    def test_wstg_mapping_must_be_selected_and_versioned(self):
        data = self.with_finding()
        data["findings"][0]["mappings"]["wstg"] = ["WSTG-ATHZ-04"]
        errors = bac.validate_assessment(data)
        self.assertTrue(any("unselected or unversioned WSTG" in error for error in errors), errors)
        data["findings"][0]["mappings"]["wstg"] = ["WSTG v4.2-ATHZ-04"]
        self.assertEqual([], bac.validate_assessment(data))

    def test_api3_supplemental_cwe_requires_api3_mapping(self):
        data = self.with_finding()
        data["findings"][0]["mappings"]["cwe"] = ["CWE-915"]
        errors = bac.validate_assessment(data)
        self.assertTrue(any("without API3:2023" in error for error in errors), errors)
        data["findings"][0]["mappings"]["apiTop10"] = ["API3:2023"]
        self.assertEqual([], bac.validate_assessment(data))

    def test_live_assessment_requires_authorized_targets(self):
        data = self.completed_without_findings()
        data["assessment"]["authorizationMode"] = "live-authorized"
        errors = bac.validate_assessment(data)
        self.assertIn("assessment.authorizedTargets must not be empty for live-authorized assessments", errors)

    def test_access_path_table_is_not_interrupted_by_evidence(self):
        data = self.completed_without_findings()
        second_path = copy.deepcopy(data["authorizationModel"]["accessPaths"][0])
        second_path["id"] = "PATH-002"
        second_path["entryPoint"] = "POST /api/refunds/{refundId}/approve"
        data["authorizationModel"]["accessPaths"].append(second_path)
        report = bac.render_report(data)
        first_row = report.index("| `PATH-001`")
        second_row = report.index("| `PATH-002`")
        evidence_heading = report.index("#### End-to-end tiers for PATH-001")
        self.assertLess(first_row, second_row)
        self.assertLess(second_row, evidence_heading)

    def test_coverage_table_is_not_interrupted_by_evidence(self):
        data = self.completed_without_findings()
        for branch in data["coverage"][:2]:
            branch["status"] = "reviewed-no-finding"
            branch["evidence"] = [self.evidence()]
        report = bac.render_report(data)
        first_row = report.index("| `A01-CV-01`")
        last_row = report.index("| `A01-PR-11`")
        evidence_heading = report.index("#### Evidence for A01-CV-01")
        self.assertLess(first_row, last_row)
        self.assertLess(last_row, evidence_heading)

    def test_markdown_report_has_dashboard_toc_and_detail_links(self):
        report = bac.render_report(self.with_finding())
        self.assertIn("## Table of contents", report)
        self.assertIn("Overall A01 assessment outcome: FAIL", report)
        self.assertIn("[BAC-001](#finding-bac-001)", report)
        self.assertIn('<a id="finding-bac-001"></a>', report)

    def test_html_report_is_standalone_navigable_and_decision_oriented(self):
        report = bac.render_report(self.with_finding(), "html")
        self.assertTrue(report.startswith("<!doctype html>"))
        self.assertIn('aria-label="Report table of contents"', report)
        self.assertIn('class="card outcome-fail"', report)
        self.assertIn('href="#finding-bac-001"', report)
        self.assertIn('<details class="finding" id="finding-bac-001">', report)
        self.assertIn("Category: Object-Level Authorization — IDOR / BOLA", report)
        self.assertIn("Component: Billing API", report)
        self.assertIn("Classification", report)
        self.assertIn("Affected implementation", report)
        self.assertIn("End-to-end authorization path", report)
        self.assertIn("Identity in → out", report)
        self.assertIn("Unauthorized scenario", report)
        self.assertIn("authenticated peer user</strong> attempts the action <strong>read</strong> on <strong>another user&#x27;s invoice", report)
        self.assertIn("<summary>Request or test shape</summary>", report)
        self.assertIn('<pre class="issue-code"><code class="language-http">', report)
        self.assertIn("Expected access rule", report)
        self.assertIn("Recommended resolution", report)
        self.assertIn("Technical evidence, attack path, severity rationale, standards mappings, and limitations", report)
        self.assertNotIn("<h3>Coverage at a glance</h3>", report)
        self.assertIn("A02–A10 assessment", report)

    def test_html_findings_register_is_a_compact_per_category_issue_list(self):
        report = bac.render_report(self.with_finding(), "html")
        register = report[report.index('<section id="findings">'):report.index('<section class="finding-category"')]
        self.assertIn("Object-Level Authorization — IDOR / BOLA", register)
        self.assertIn("BAC-001: Users can read another user&#x27;s invoice", register)
        self.assertIn('<th scope="col">Issue</th><th scope="col">Risk</th><th scope="col">Status</th>', register)
        self.assertNotIn("Classification", register)
        self.assertNotIn("Confidence", register)
        self.assertNotIn("Component:", register)

    def test_completed_no_finding_report_has_pass_outcome(self):
        markdown = bac.render_report(self.completed_without_findings())
        html = bac.render_report(self.completed_without_findings(), "html")
        self.assertIn("Overall A01 assessment outcome: PASS", markdown)
        self.assertIn("End-to-end trace completeness: COMPLETE", markdown)
        self.assertIn('class="card outcome-pass"', html)
        self.assertIn('class="card outcome-complete"', html)

    def test_cli_render_infers_markdown_and_html_from_extension(self):
        data = self.with_finding()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "assessment.json"
            markdown_output = temp / "report.md"
            html_output = temp / "report.html"
            source.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(0, bac.command_render(source, markdown_output))
            self.assertEqual(0, bac.command_render(source, html_output))
            self.assertIn("## Table of contents", markdown_output.read_text(encoding="utf-8"))
            self.assertIn("<!doctype html>", html_output.read_text(encoding="utf-8"))

    def test_cli_render_accepts_explicit_format_and_rejects_unknown_auto_extension(self):
        data = self.with_finding()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "assessment.json"
            explicit = temp / "human-report.txt"
            explicit_md = temp / "engineer-report.txt"
            unknown = temp / "report.txt"
            source.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(0, bac.command_render(source, explicit, "html"))
            self.assertIn("<!doctype html>", explicit.read_text(encoding="utf-8"))
            self.assertEqual(0, bac.command_render(source, explicit_md, "md"))
            self.assertIn("## Table of contents", explicit_md.read_text(encoding="utf-8"))
            self.assertEqual(2, bac.command_render(source, unknown))


if __name__ == "__main__":
    unittest.main()

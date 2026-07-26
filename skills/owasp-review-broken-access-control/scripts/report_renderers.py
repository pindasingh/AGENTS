"""Human-oriented Markdown and standalone HTML renderers for A01 assessments."""

from __future__ import annotations

import html
import re
from collections import Counter
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}


def anchor(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return text or "section"


def assessment_outcome(data: dict[str, Any]) -> tuple[str, str]:
    findings = data["findings"]
    supported = [item for item in findings if item["status"] in {"confirmed", "likely"}]
    unresolved = [item for item in findings if item["status"] == "needs-validation"]
    not_assessed = [item for item in data["coverage"] if item["status"] == "not-assessed"]
    if supported:
        return "FAIL", f"{len(supported)} confirmed or likely broken-access-control finding(s) require action."
    if unresolved or not_assessed:
        return "REVIEW", "No supported finding is recorded, but validation or coverage remains incomplete."
    return "PASS", "No supported broken-access-control finding was identified in the reviewed scope."


def trace_completeness(data: dict[str, Any]) -> tuple[str, str]:
    paths = data["authorizationModel"]["accessPaths"]
    blocked = [item for item in paths if item["traceStatus"] == "blocked"]
    awaiting = [item for item in data["gaps"] if item["requestStatus"] == "awaiting-user"]
    partial = [item for item in paths if item["traceStatus"] == "partial"]
    accepted_gaps = [item for item in data["gaps"] if item["requestStatus"] != "awaiting-user"]
    not_assessed = [item for item in data["coverage"] if item["status"] == "not-assessed"]
    if blocked or awaiting:
        return "BLOCKED", "Material evidence is unavailable and user direction is required."
    if partial or accepted_gaps or not_assessed:
        return "PARTIAL", "The review traced available tiers, but accepted exclusions or unavailable evidence limit completeness."
    return "COMPLETE", "Every recorded access path is traced through verified material tiers."


def trace_counts(data: dict[str, Any]) -> Counter[str]:
    return Counter(item["traceStatus"] for item in data["authorizationModel"]["accessPaths"])


def coverage_counts(data: dict[str, Any]) -> Counter[str]:
    return Counter(item["status"] for item in data["coverage"])


def finding_counts(data: dict[str, Any]) -> Counter[str]:
    return Counter(item["status"] for item in data["findings"])


def sorted_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        data["findings"],
        key=lambda item: (
            item["category"].casefold(),
            item["component"].casefold(),
            SEVERITY_ORDER[item["severity"]],
            item["id"],
        ),
    )


def grouped_findings(findings: list[dict[str, Any]]) -> list[tuple[str, list[tuple[str, list[dict[str, Any]]]]]]:
    categories: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for finding in findings:
        categories.setdefault(finding["category"], {}).setdefault(finding["component"], []).append(finding)
    return [
        (
            category,
            [
                (component, sorted(items, key=lambda item: (SEVERITY_ORDER[item["severity"]], item["id"])))
                for component, items in sorted(components.items(), key=lambda pair: pair[0].casefold())
            ],
        )
        for category, components in sorted(categories.items(), key=lambda pair: pair[0].casefold())
    ]


def markdown_toc(data: dict[str, Any]) -> str:
    lines = [
        "## Table of contents",
        "",
        "- [Executive dashboard](#executive-dashboard)",
        "- [Executive summary](#executive-summary)",
        "- [Scope and authority](#scope-and-authority)",
        "- [Findings register](#findings-summary)",
        "- [Detailed findings](#detailed-findings)",
        "- [Expected access rules](#authorization-model)",
    ]
    lines.extend(
        [
            "- [Review coverage](#a01-coverage-matrix)",
            "- [What was not fully checked](#gaps-and-next-steps)",
            "- [About this review](#framework-statement)",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_dashboard(data: dict[str, Any]) -> str:
    outcome, reason = assessment_outcome(data)
    findings = finding_counts(data)
    coverage = coverage_counts(data)
    traces = trace_counts(data)
    completeness, completeness_reason = trace_completeness(data)
    return "\n".join(
        [
            "## Executive dashboard",
            "",
            f"> **Overall A01 assessment outcome: {outcome}**  ",
            f"> {reason}  ",
            f"> **End-to-end trace completeness: {completeness}**  ",
            f"> {completeness_reason}",
            "",
            "| Decision indicator | Result |",
            "|---|---:|",
            f"| Confirmed findings | {findings['confirmed']} |",
            f"| Likely findings | {findings['likely']} |",
            f"| Needs validation | {findings['needs-validation']} |",
            f"| Complete access paths | {traces['complete']} |",
            f"| Partial access paths | {traces['partial']} |",
            f"| Blocked access paths | {traces['blocked']} |",
            f"| Evidence gaps | {len(data['gaps'])} |",
            f"| A01 branches with findings | {coverage['finding']} |",
            f"| A01 branches reviewed without finding | {coverage['reviewed-no-finding']} |",
            f"| A01 branches not assessed | {coverage['not-assessed']} |",
            f"| A01 branches not applicable | {coverage['not-applicable']} |",
            "",
            "**Decision rule:** Security outcome and trace completeness are separate. `FAIL` means at least one confirmed or likely finding; `REVIEW` means no supported finding but unresolved validation or coverage; `PASS` means no supported finding and no unassessed branch. `BLOCKED` requires user direction, `PARTIAL` records accepted exclusions or unavailable evidence, and `COMPLETE` means every recorded path has verified material tiers. An unqualified pass requires complete tracing.",
            "",
            "Start with the [findings register](#findings-summary), then follow a finding ID to its evidence and recommended resolution. Use the [coverage matrix](#a01-coverage-matrix) to see what passed, failed, was not assessed, or did not apply.",
            "",
        ]
    )


def render_markdown_report(data: dict[str, Any], legacy_report: str) -> str:
    """Enhance the contract renderer with navigation and decision-oriented summaries."""
    first_break = legacy_report.find("\n")
    title = legacy_report[:first_break]
    body = legacy_report[first_break + 1 :].lstrip("\n")
    report = "\n\n".join([title, markdown_toc(data).rstrip(), markdown_dashboard(data).rstrip(), body])

    for finding in data["findings"]:
        finding_id = finding["id"]
        report = report.replace(
            f"| {finding_id} |",
            f"| [{finding_id}](#finding-{anchor(finding_id)}) |",
            1,
        )
        report = report.replace(
            f"##### {finding_id}: {finding['title']}",
            f"<a id=\"finding-{anchor(finding_id)}\"></a>\n\n##### {finding_id}: {finding['title']}",
            1,
        )

    # Put the decision and problem register before specialist authorization-model detail.
    authorization_marker = "## Authorization model"
    findings_marker = "## Findings summary"
    coverage_marker = "## A01 coverage matrix"
    authorization_start = report.index(authorization_marker)
    findings_start = report.index(findings_marker)
    coverage_start = report.index(coverage_marker)
    authorization_block = report[authorization_start:findings_start]
    findings_block = report[findings_start:coverage_start]
    report = report[:authorization_start] + findings_block + authorization_block + report[coverage_start:]
    report = report.replace(
        "## Findings summary\n\n",
        "## Findings summary\n\nThis compact register lists issues by category. Follow a finding ID to its explanation, evidence, recommended resolution, and verification steps.\n\n",
        1,
    )
    report = report.replace(
        "## Authorization model\n\n",
        "## Authorization model\n\nThe expected access rules below are the standard used to judge the implementation; they are not the resolution.\n\n",
        1,
    )
    return report.rstrip() + "\n"


def h(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def list_html(values: list[Any], empty: str = "None recorded.") -> str:
    if not values:
        return f'<p class="muted">{h(empty)}</p>'
    return "<ul>" + "".join(f"<li>{h(value)}</li>" for value in values) + "</ul>"


def evidence_html(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">None recorded.</p>'
    return "<ul class=\"evidence\">" + "".join(
        f"<li><strong>{h(item['kind'])}:</strong> <code>{h(item['location'])}</code> "
        f"<span class=\"muted\">at <code>{h(item['revision'])}</code></span><br>{h(item['observation'])}</li>"
        for item in items
    ) + "</ul>"


def badge(value: str) -> str:
    return f'<span class="badge badge-{anchor(value)}">{h(value.upper())}</span>'


def code_html(language: str, content: str) -> str:
    return f'<pre class="issue-code"><code class="language-{anchor(language)}">{h(content.rstrip())}</code></pre>'


def classification_pseudocode(finding: dict[str, Any]) -> str:
    mappings = finding["mappings"]
    standards = mappings["owasp"] + mappings["apiTop10"] + mappings["cwe"]
    return "\n".join([
        f"type: {finding['classification']}",
        f"status: {finding['status']}",
        f"severity: {finding['severity']}",
        f"confidence: {finding['confidence']}",
        f"standards: [{', '.join(standards)}]",
    ])


def implementation_pseudocode(finding: dict[str, Any]) -> str:
    affected = finding["affectedImplementation"]
    lines = [f"component: {finding['component']}"]
    labels = {
        "controllers": "controllers",
        "classes": "classes",
        "methods": "methods",
        "endpoints": "endpoints",
        "filesOrArtifacts": "files_or_artifacts",
    }
    for key, label in labels.items():
        lines.append(f"{label}: [{', '.join(affected[key])}]")
    return "\n".join(lines)


def verification_pseudocode(finding: dict[str, Any]) -> str:
    return "\n".join(
        f"{test['type'].upper()}: {test['description']} => {test['expected']}"
        for test in finding["regressionTests"]
    )


def authorization_path_pseudocode(
    finding: dict[str, Any], access_paths_by_id: dict[str, dict[str, Any]]
) -> str:
    lines: list[str] = []
    for path_id in finding["accessPathIds"]:
        access_path = access_paths_by_id[path_id]
        if lines:
            lines.append("")
        lines.append(f"{path_id} [{access_path['traceStatus']}]")
        for tier in access_path["tiers"]:
            authority = ", ".join(tier["credentials"] + tier["policies"]) or "no authority input recorded"
            lines.append(
                f"  -> {tier['component']} / {tier['name']} | {tier['entryIdentity']} -> "
                f"{tier['exitIdentity']} | {authority} | {tier['decision']}"
            )
    return "\n".join(lines)


def issue_block_html(title: str, block: dict[str, Any]) -> str:
    return f'<div class="issue-block"><h3>{h(title)}</h3><p>{h(block["summary"])}</p>{code_html(block["language"], block["pseudocode"])}</div>'


def unauthorized_scenario_html(finding: dict[str, Any]) -> str:
    block = finding["exercise"]
    return (
        '<div class="issue-block"><h3>Unauthorized scenario</h3>'
        f'<p><strong>{h(finding["actor"])}</strong> attempts the action <strong>{h(finding["action"])}</strong> '
        f'on <strong>{h(finding["resource"])}</strong>.</p><p>{h(block["summary"])}</p>'
        f'<details class="technical"><summary>Request or test shape</summary>{code_html(block["language"], block["pseudocode"])}</details></div>'
    )


def table(headers: list[str], rows: list[list[str]], *, raw: set[int] | None = None) -> str:
    raw = raw or set()
    head = "".join(f"<th scope=\"col\">{h(value)}</th>" for value in headers)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{value if index in raw else h(value)}</td>" for index, value in enumerate(row)
        )
        body_rows.append(f"<tr>{cells}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def render_html_report(data: dict[str, Any], coverage_names: dict[str, str]) -> str:
    assessment = data["assessment"]
    model = data["authorizationModel"]
    findings = sorted_findings(data)
    finding_groups = grouped_findings(findings)
    coverage = data["coverage"]
    gaps = data["gaps"]
    outcome, reason = assessment_outcome(data)
    completeness, completeness_reason = trace_completeness(data)
    traces = trace_counts(data)
    access_paths_by_id = {item["id"]: item for item in model["accessPaths"]}
    fcounts = finding_counts(data)
    ccounts = coverage_counts(data)

    cards = "".join(
        [
            f'<div class="card outcome-{anchor(outcome)}"><span>Overall outcome</span><strong>{h(outcome)}</strong><small>{h(reason)}</small></div>',
            f'<div class="card outcome-{anchor(completeness)}"><span>Trace completeness</span><strong>{h(completeness)}</strong><small>{h(completeness_reason)}</small></div>',
            f'<div class="card"><span>Confirmed / likely</span><strong>{fcounts["confirmed"] + fcounts["likely"]}</strong><small>Supported findings</small></div>',
            f'<div class="card"><span>Complete paths</span><strong>{traces["complete"]}</strong><small>Verified end to end</small></div>',
            f'<div class="card"><span>Partial / blocked paths</span><strong>{traces["partial"] + traces["blocked"]}</strong><small>Incomplete end-to-end paths</small></div>',
            f'<div class="card"><span>Evidence gaps</span><strong>{len(gaps)}</strong><small>Pending or accepted limitations</small></div>',
        ]
    )

    coverage_rows = []
    result_map = {"finding": "FAIL", "reviewed-no-finding": "PASS", "not-assessed": "NOT ASSESSED", "not-applicable": "N/A"}
    for item in coverage:
        linked_id = f'<a href="#coverage-{anchor(item["id"])}"><code>{h(item["id"])}</code></a>'
        finding_links = ", ".join(
            f'<a href="#finding-{anchor(fid)}">{h(fid)}</a>' for fid in item["findingIds"]
        ) or "—"
        coverage_rows.append([
            linked_id,
            coverage_names[item["id"]],
            badge(result_map[item["status"]]),
            item["rationale"],
            finding_links,
        ])

    finding_navigation = ""
    if finding_groups:
        nav_categories = "".join(
            f'<li><a href="#register-category-{anchor(category)}">{h(category)}</a></li>'
            for category, _ in finding_groups
        )
        finding_navigation = f'<ul class="finding-links">{nav_categories}</ul>'

    path_rows = []
    for item in model["accessPaths"]:
        path_rows.append([
            f'<a href="#path-{anchor(item["id"])}"><code>{h(item["id"])}</code></a>',
            badge(item["traceStatus"]),
            item["entryPoint"],
            ", ".join(item["methodsOrOperations"]),
            item["channel"],
            item["authentication"],
            f'{item["resource"]} — {", ".join(item["actions"])}',
        ])

    parts = [f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h(assessment['title'])}</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--text:#182230;--muted:#596579;--line:#d9e0e9;--blue:#175cd3;--green:#067647;--red:#b42318;--amber:#b54708;--gray:#475467;--shadow:0 1px 3px rgba(16,24,40,.08)}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
a{{color:var(--blue);text-decoration:none}} a:hover{{text-decoration:underline}} code{{font:13px ui-monospace,SFMono-Regular,Consolas,monospace}} .button{{display:inline-block;margin:4px 8px 4px 0;padding:9px 14px;border-radius:8px;background:var(--blue);color:#fff;font-weight:700}} .button:hover{{text-decoration:none;filter:brightness(.95)}} .button.secondary{{background:#e4e7ec;color:#344054}}
.layout{{display:grid;grid-template-columns:minmax(240px,300px) minmax(0,1fr);min-height:100vh}} nav{{position:sticky;top:0;height:100vh;overflow:auto;padding:24px 20px;background:#101828;color:#d0d5dd}} nav h2{{color:#fff;font-size:16px}} nav a{{color:#d0d5dd}} nav ol,nav ul{{padding-left:20px}} nav li{{margin:7px 0}} nav .finding-links{{font-size:13px}}
main{{width:min(1180px,100%);padding:32px 40px 80px}} section,.finding,.gap,.path-detail{{background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:26px;margin:0 0 24px}} h1{{font-size:32px;line-height:1.2;margin:0 0 14px}} h2{{font-size:24px;margin-top:0}} h3{{font-size:18px;margin-top:26px}} h4{{font-size:16px}} .subtitle,.muted{{color:var(--muted)}} .register-category{{border-top:1px solid var(--line);margin-top:24px;padding-top:4px}} .finding-category{{scroll-margin-top:18px}} .component-group{{border-left:4px solid #dbe7fb;padding-left:20px;margin:24px 0}} .component-group>h3{{margin-top:0}}
.meta{{display:flex;flex-wrap:wrap;gap:8px 20px;padding:0;list-style:none}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:20px 0}} .card{{display:flex;flex-direction:column;gap:3px;padding:18px;border:1px solid var(--line);border-radius:10px;background:#f9fafb}} .card span,.card small{{color:var(--muted)}} .card strong{{font-size:25px}} .outcome-fail{{border-left:6px solid var(--red)}} .outcome-pass,.outcome-complete{{border-left:6px solid var(--green)}} .outcome-review,.outcome-partial,.outcome-blocked{{border-left:6px solid var(--amber)}}
.table-wrap{{overflow:auto}} table{{width:100%;border-collapse:collapse;font-size:14px}} th,td{{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:10px 12px}} th{{background:#f2f4f7;color:#344054;position:sticky;top:0}} .badge{{display:inline-block;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700;white-space:nowrap;background:#eef2f6;color:var(--gray)}} .badge-fail,.badge-confirmed,.badge-critical,.badge-high{{background:#fee4e2;color:var(--red)}} .badge-pass,.badge-complete,.badge-verified{{background:#d1fadf;color:var(--green)}} .badge-review,.badge-not-assessed,.badge-likely,.badge-needs-validation,.badge-medium,.badge-partial,.badge-blocked,.badge-unverified,.badge-awaiting-user,.badge-excluded-by-user,.badge-confirmed-unavailable{{background:#fef0c7;color:var(--amber)}} .badge-informational,.badge-low,.badge-n-a{{background:#e4e7ec;color:var(--gray)}}
.callout{{border-left:4px solid var(--blue);background:#eff8ff;padding:12px 16px;margin:16px 0}} .facts{{display:grid;grid-template-columns:180px 1fr;gap:8px 18px}} .facts dt{{font-weight:700}} .facts dd{{margin:0}} .attack-path li,.tests li,.evidence li{{margin:8px 0}} .finding{{scroll-margin-top:18px;padding:20px;margin-bottom:16px}} .finding > summary,.path-detail > summary{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;cursor:pointer;list-style:none}} .finding > summary::-webkit-details-marker,.path-detail > summary::-webkit-details-marker{{display:none}} .finding > summary h2,.path-detail > summary h2{{font-size:18px;margin:0 auto 0 0}} .finding-body{{padding-top:18px;border-top:1px solid var(--line);margin-top:16px}} .issue-block{{margin:22px 0}} .issue-block h3{{margin:0 0 6px}} .issue-block p{{margin:0 0 10px}} .issue-code{{margin:0;overflow:auto;border:1px solid #344054;border-radius:8px;background:#101828;color:#f2f4f7;padding:14px 16px;white-space:pre-wrap;overflow-wrap:anywhere}} .evidence-anchors code{{display:inline-block;margin:2px 5px 2px 0}} .back{{float:right;font-size:13px}} details.technical{{border-top:1px solid var(--line);padding-top:12px;margin-top:16px}} details.technical > summary{{cursor:pointer;font-weight:700}}
@media(max-width:900px){{.layout{{display:block}}nav{{position:relative;height:auto}}main{{padding:22px 14px}}.cards{{grid-template-columns:repeat(2,1fr)}}.facts{{grid-template-columns:1fr}}}}
@media print{{body{{background:#fff}}nav{{display:none}}.layout{{display:block}}main{{width:100%;padding:0}}section,.finding,.gap,.path-detail{{box-shadow:none;break-inside:avoid}}a{{color:inherit}}}}
</style>
</head>
<body>
<div class="layout">
<nav aria-label="Report table of contents">
<h2>Table of contents</h2>
<ol>
<li><a href="#dashboard">Executive dashboard</a></li>
<li><a href="#scope">Scope and authority</a></li>
<li><a href="#findings">Findings by category and component</a>{finding_navigation}</li>
<li><a href="#authorization-model">Expected access rules</a></li>
<li><a href="#coverage">Review coverage</a></li>
<li><a href="#gaps">What was not fully checked</a></li>
<li><a href="#framework">About this review</a></li>
</ol>
</nav>
<main id="top">
<section id="dashboard">
<h1>{h(assessment['title'])}</h1>
<p class="subtitle">A plain-language decision report with technical evidence available when needed.</p>
<div class="cards">{cards}</div>
<div class="callout"><strong>Security outcome — {h(outcome)}:</strong> {h(reason)}<br><strong>Trace completeness — {h(completeness)}:</strong> {h(completeness_reason)}</div>
<h2>What this means</h2><p>{h(assessment['summary'])}</p>
<p><a class="button" href="#findings">Review what needs attention</a> <a class="button secondary" href="#coverage">See review coverage</a></p>
<ul class="meta"><li><strong>Subject:</strong> {h(assessment['subject'])}</li><li><strong>Revision:</strong> <code>{h(assessment['revision'])}</code></li><li><strong>Date:</strong> {h(assessment['assessmentDate'])}</li><li><strong>Mode:</strong> {h(assessment['authorizationMode'])}</li></ul>
<details class="technical"><summary>How the overall result is calculated</summary><p>Security outcome and trace completeness are separate. FAIL means at least one confirmed or likely issue. REVIEW means no proven issue but some validation or coverage is incomplete. PASS means no proven issue and no unassessed review area. BLOCKED means material evidence needs user direction; PARTIAL means an exclusion or unavailable artifact was explicitly accepted; COMPLETE means every recorded path has verified material tiers. An unqualified pass requires complete tracing.</p></details>
</section>
<section id="scope"><a class="back" href="#top">Back to top</a><h2>Scope and authority</h2>
<h3>In scope</h3>{list_html(assessment['scope'])}<h3>Authorized live targets</h3>{list_html(assessment['authorizedTargets'])}<h3>Exclusions</h3>{list_html(assessment['exclusions'])}<h3>Limitations</h3>{list_html(assessment['limitations'])}
</section>"""]

    authorization_sections = ['<section id="authorization-model"><a class="back" href="#top">Back to top</a><h2>Expected access rules</h2><p>These rules describe who should be allowed to do what. They are the standard used to judge the implementation; they are not the fix.</p>']
    labels = {"actors": "Actors", "resources": "Resources", "actions": "Actions", "contexts": "Contexts", "enforcementPoints": "Trusted enforcement points", "policyStatements": "Expected policy statements"}
    for key, label in labels.items():
        if key == "policyStatements":
            authorization_sections.append(f"<h3>{h(label)}</h3>{list_html(model[key])}")
        else:
            authorization_sections.append(f'<details class="technical"><summary>{h(label)}</summary>{list_html(model[key])}</details>')
    inventory = table(['ID','Trace','Entry point','Method/operation','Channel','Authentication','Resource/action'],path_rows,raw={0,1}) if path_rows else '<p class="muted">No access paths recorded.</p>'
    authorization_sections.append(f'<details class="technical"><summary>Technical access-path inventory</summary>{inventory}</details></section>')

    for item in model["accessPaths"]:
        tier_rows = [
            [
                str(index),
                tier["type"],
                tier["component"],
                tier["name"],
                f'{tier["entryIdentity"]} → {tier["exitIdentity"]}',
                ", ".join(tier["credentials"]) or "None",
                ", ".join(tier["policies"]) or "None",
                ", ".join(tier["resourceContext"]) or "None",
                tier["decision"],
                badge(tier["status"]),
            ]
            for index, tier in enumerate(item["tiers"], start=1)
        ]
        tier_evidence = "".join(
            f'<h4>{h(tier["name"])} — {h(tier["component"])}</h4>{evidence_html(tier["evidence"])}'
            for tier in item["tiers"]
        )
        authorization_sections.append(
            f'<details class="path-detail" id="path-{anchor(item["id"])}"><summary><h2>{h(item["id"])}: {h(item["entryPoint"])}</h2>{badge(item["traceStatus"])}</summary><div class="finding-body">'
            f'<p><strong>Eligible actors:</strong> {h(", ".join(item["actors"]))}</p>'
            f'<p><strong>Input and authority vectors:</strong> {h(", ".join(item["inputVectors"]))}</p>'
            f'<p><strong>Related gaps:</strong> {h(", ".join(item["gapIds"]) or "None")}</p>'
            f'{table(["#", "Type", "Component", "Tier", "Identity in → out", "Credentials", "Policies", "Resource context", "Decision", "Status"], tier_rows, raw={9})}'
            f'<details class="technical"><summary>Tier and path evidence</summary>{tier_evidence}<h4>Path evidence</h4>{evidence_html(item["evidence"])}</details></div></details>'
        )

    parts.append('<section id="findings"><a class="back" href="#top">Back to top</a><h2>Findings register</h2><p>A compact issue list grouped by access-control category. Select an issue to open its explanation and evidence.</p>')
    if not finding_groups:
        parts.append('<p>No findings recorded. See coverage and gaps before interpreting this as a pass.</p>')
    for category, components in finding_groups:
        category_findings = [item for _, component_findings in components for item in component_findings]
        rows = [
            [
                f'<a href="#finding-{anchor(item["id"])}"><strong>{h(item["id"])}: {h(item["title"])}</strong></a>',
                badge(item["severity"]),
                badge(item["status"]),
            ]
            for item in category_findings
        ]
        parts.append(
            f'<div class="register-category" id="register-category-{anchor(category)}"><h3>{h(category)}</h3>'
            f'{table(["Issue", "Risk", "Status"], rows, raw={0, 1, 2})}</div>'
        )
    parts.append('</section>')

    for category, components in finding_groups:
        parts.append(f'<section class="finding-category" id="category-{anchor(category)}"><a class="back" href="#top">Back to top</a><h2>Category: {h(category)}</h2><p>Each issue below is assigned to one primary component; related code and endpoints are listed inside the issue.</p>')
        for component, component_findings in components:
            parts.append(f'<div class="component-group" id="component-{anchor(category)}-{anchor(component)}"><h3>Component: {h(component)}</h3>')
            for item in component_findings:
                mappings = item["mappings"]
                facts = "".join(
                    f"<dt>{h(label)}</dt><dd>{h(value)}</dd>"
                    for label, value in [
                        ("Who can do this", item["actor"]),
                        ("What is exposed", item["resource"]),
                        ("What they can do", item["action"]),
                        ("Affected access paths", ", ".join(item["accessPathIds"])),
                    ]
                )
                mapping_rows = [
                    ["Coverage", ", ".join(item["coverageIds"])],
                    ["OWASP", ", ".join(mappings["owasp"])],
                    ["ASVS", ", ".join(mappings["asvs"]) or "None"],
                    ["WSTG", ", ".join(mappings["wstg"]) or "None"],
                    ["API Security", ", ".join(mappings["apiTop10"]) or "None"],
                    ["CWE", ", ".join(mappings["cwe"]) or "None"],
                ]
                evidence_anchors = " ".join(f'<code>{h(evidence["location"])}</code>' for evidence in item["evidence"])
                primary_blocks = "".join([
                    '<div class="issue-block"><h3>Classification</h3>' + code_html("yaml", classification_pseudocode(item)) + '</div>',
                    '<div class="issue-block"><h3>Affected implementation</h3>' + code_html("yaml", implementation_pseudocode(item)) + f'<p class="evidence-anchors"><strong>Evidence anchors:</strong> {evidence_anchors}</p></div>',
                    '<div class="issue-block"><h3>End-to-end authorization path</h3><p>Identity, credentials, policy, and decision are shown at each evidenced tier.</p>' + code_html("text", authorization_path_pseudocode(item, access_paths_by_id)) + '</div>',
                    issue_block_html("Expected access rule", item["expectedAccessRule"]),
                    unauthorized_scenario_html(item),
                    issue_block_html("Why the check fails", item["failureProof"]),
                    issue_block_html("What could happen", item["impact"]),
                    issue_block_html("Recommended resolution", item["remediation"]),
                    '<div class="issue-block"><h3>How to verify the fix</h3>' + code_html("text", verification_pseudocode(item)) + '</div>',
                ])
                parts.append(
                    f'<details class="finding" id="finding-{anchor(item["id"])}"><summary><h2>{h(item["id"])}: {h(item["title"])}</h2>{badge(item["severity"])}{badge(item["status"])}</summary>'
                    f'<div class="finding-body"><p><strong>In short:</strong> {h(item["summary"])}</p>{primary_blocks}'
                    f'<details class="technical"><summary>Technical evidence, attack path, severity rationale, standards mappings, and limitations</summary>'
                    f'<dl class="facts">{facts}</dl><h4>Attack path</h4><ol class="attack-path">{"".join(f"<li>{h(step)}</li>" for step in item["attackPath"])}</ol>'
                    f'<h4>Evidence</h4>{evidence_html(item["evidence"])}<p><strong>Severity rationale:</strong> {h(item["severityRationale"])}</p>'
                    f'{table(["Type", "Mapping"], mapping_rows)}<h4>Limitations</h4>{list_html(item["limitations"])}</details></div></details>'
                )
            parts.append('</div>')
        parts.append('</section>')

    parts.extend(authorization_sections)
    parts.append(f'<section id="coverage"><a class="back" href="#top">Back to top</a><h2>Review coverage</h2><p>This table shows which access-control checks failed, passed, were not assessed, or did not apply. Select a check ID for its supporting detail.</p>{table(["Check","What was reviewed","Result","Conclusion","Related problems"],coverage_rows,raw={0,2,4})}</section>')
    for item in coverage:
        parts.append(f'<details class="path-detail" id="coverage-{anchor(item["id"])}"><summary><h2>{h(item["id"])}: {h(coverage_names[item["id"]])}</h2>{badge(result_map[item["status"]])}</summary><div class="finding-body"><p>{h(item["rationale"])}</p><details class="technical"><summary>Supporting evidence</summary>{evidence_html(item["evidence"])}</details></div></details>')

    parts.append('<section id="gaps"><a class="back" href="#top">Back to top</a><h2>What was not fully checked</h2><p>These gaps prevent a complete conclusion for the affected review areas.</p>')
    if not gaps:
        parts.append('<p>No unresolved coverage gaps recorded.</p>')
    parts.append('</section>')
    for gap in gaps:
        parts.append(
            f'<article class="gap" id="gap-{anchor(gap["id"])}"><h2>{h(gap["id"])}: {h(gap["title"])}</h2>'
            f'<p>{badge(gap["requestStatus"])} <strong>User direction:</strong> {h(gap["userDecision"])}</p>'
            f'<p><strong>Why it matters:</strong> {h(gap["whyItMatters"])}</p>'
            f'<p><strong>Affected paths:</strong> {h(", ".join(gap["accessPathIds"]) or "None recorded")}</p>'
            f'<p><strong>Affected coverage:</strong> {h(", ".join(gap["coverageIds"]))}</p>'
            f'<h3>Searched or inspected</h3>{list_html(gap["searched"])}'
            f'<h3>Requested artifacts or access</h3>{list_html(gap["requestedArtifacts"])}'
            f'<h3>Blocked conclusions</h3>{list_html(gap["blockedConclusions"])}'
            f'<p><strong>Safe next step:</strong> {h(gap["nextStep"])}</p></article>'
        )

    parts.append('''<section id="framework"><a class="back" href="#top">Back to top</a><h2>About this review</h2><details class="technical"><summary>Standards and scope statement</summary><p>This report uses OWASP Top 10 A01:2025 as its risk taxonomy, OWASP ASVS 5.0.0 V8 for current verification requirements, OWASP WSTG 4.2 authorization tests for reproducible test design, the OWASP Authorization Cheat Sheet for implementation guidance, and OWASP API Security Top 10:2023 where applicable. This A01 assessment does not constitute an A02–A10 assessment or automatic ASVS certification.</p></details></section></main></div><script>function revealHash(){const id=location.hash.slice(1);if(!id)return;const target=document.getElementById(id);if(!target)return;if(target.tagName==='DETAILS')target.open=true;let parent=target.parentElement?.closest('details');while(parent){parent.open=true;parent=parent.parentElement?.closest('details');}}window.addEventListener('hashchange',revealHash);window.addEventListener('DOMContentLoaded',revealHash);</script></body></html>''')
    return "\n".join(parts) + "\n"


def resolve_output_format(output: Path, requested: str) -> str:
    if requested in {"md", "markdown"}:
        return "markdown"
    if requested in {"htm", "html"}:
        return "html"
    if requested != "auto":
        raise ValueError(f"unsupported report format: {requested}")
    suffix = output.suffix.lower()
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    raise ValueError("cannot infer report format; use --format markdown|html or an .md/.html output extension")

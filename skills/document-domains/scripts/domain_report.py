#!/usr/bin/env python3
'''Initialize, validate, compare, and render domain manifests.'''

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


VAGUE_TRIGGER_PATTERN = re.compile(
    r'\b(source-specific|authenticated)\s+(event|request)|\b(event|request|message)\s+or\s+(event|request|message)\b|^\s*(event|request|message)\s+(received|arrives?)\s*$',
    re.IGNORECASE,
)
CONCRETE_ENTRY_PATTERN = re.compile(r'^(when\b|GET\s|POST\s|PUT\s|PATCH\s|DELETE\s)', re.IGNORECASE)


def read(path):
    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError('Manifest must be a JSON object')
    return data


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-') or 'domain'


def initialize(title, domain, sources):
    roots = []
    for number, source in enumerate(sources, 1):
        path = Path(source).resolve()
        label = path.name or f'source-{number}'
        roots.append({'id': f'root-{slug(label)}-{number}', 'path': path.as_posix(),
                      'label': label, 'scan_status': 'not-started', 'notes': '',
                      'remote': '', 'branch': '', 'commit': '',
                      'fetch_status': 'not-checked', 'working_tree_divergence': ''})
    return {
        'schema_version': '2.1',
        'document': {'id': slug(domain), 'title': title, 'domain': domain,
                     'revision': 1,
                     'generated_at': datetime.now(timezone.utc).isoformat(),
                     'summary': '',
                     'source_trust': 'Local source only; runtime and deployment are not verified.'},
        'source_roots': roots,
        'coverage': {'included_patterns': [], 'excluded_paths': [],



def validate(data):
    errors, warnings, indexes, owner = [], [], {}, {}
    if data.get('schema_version') != '2.1':
        errors.append('schema_version must equal 2.1')
    required_document = {'id', 'title', 'domain', 'revision', 'generated_at',
                         'summary', 'source_trust'}
    if not required_document.issubset(data.get('document', {})):
        errors.append('document is missing required fields')
    required_coverage = {'included_patterns', 'excluded_paths', 'limitations',
                         'search_log'}
    if not required_coverage.issubset(data.get('coverage', {})):
        errors.append('coverage is missing required fields')
    for collection in COLLECTIONS:
        values = data.get(collection)
        if not isinstance(values, list):
            errors.append(f'{collection} must be an array')
            values = []
        indexes[collection] = {}
        for position, item in enumerate(values):
            if not isinstance(item, dict):
                errors.append(f'{collection}[{position}] must be an object')
                continue
            item_id = item.get('id')
            if not isinstance(item_id, str) or not ID_PATTERN.fullmatch(item_id):
                errors.append(f'{collection}[{position}] has an invalid id')
                continue
            if item_id in owner:
                errors.append(f'{item_id} is reused in {collection} and {owner[item_id]}')
            indexes[collection][item_id] = item
            owner[item_id] = collection
    roots, evidence = set(indexes['source_roots']), set(indexes['evidence'])
    components, operations = set(indexes['components']), set(indexes['operations'])
    gaps = set(indexes['gaps'])
    for item_id, item in indexes['evidence'].items():
        if not {'root_id', 'path', 'observation'}.issubset(item):
            errors.append(f'{item_id} is missing its source anchor')
        if item.get('root_id') not in roots:
            errors.append(f'{item_id} references an unknown source root')
    for item_id, item in indexes['components'].items():
        if item.get('root_id') not in roots:
            errors.append(f'{item_id} references an unknown source root')
    for operation_id, operation in indexes['operations'].items():
        required_operation = {'component_id', 'name', 'kind', 'direction', 'entry_point',
                              'inbound_endpoint', 'description', 'summary', 'preconditions',
                              'steps', 'outcomes', 'failure_paths', 'gap_ids'}
        if not required_operation.issubset(operation):
            errors.append(f'{operation_id} is missing required operation fields')
        if operation.get('component_id') not in components:
            errors.append(f'{operation_id} references an unknown component')
        entry_point = operation.get('entry_point')
        if not isinstance(entry_point, str) or not CONCRETE_ENTRY_PATTERN.match(entry_point.strip()):

        if not isinstance(endpoint, dict) or not required_endpoint.issubset(endpoint):
            errors.append(f'{operation_id} has an incomplete inbound endpoint')

                errors.append(f'{operation_id} has unknown inbound endpoint fields without a gap')
            if not isinstance(endpoint.get('ingress_path'), list):
                errors.append(f'{operation_id} ingress_path must be an array')
            for gap_id in endpoint.get('gap_ids', []):
                if gap_id not in gaps:
                    errors.append(f'{operation_id} inbound endpoint references unknown gap {gap_id}')
        steps = operation.get('steps', [])
        step_ids = {step.get('id') for step in steps if isinstance(step, dict)}
        for step in steps:
            if not isinstance(step, dict):
                errors.append(f'{operation_id} contains a non-object interaction step')
                continue
            required = {'id', 'sequence', 'kind', 'action', 'certainty',
                        'evidence_ids', 'next_step_ids'}
            if not required.issubset(step):
                errors.append(f'{operation_id} contains an incomplete interaction step')
            if step.get('component_id') and step.get('component_id') not in components:
                errors.append(f'{operation_id} references an unknown step component')
            for next_id in step.get('next_step_ids', []):
                if next_id not in step_ids:
                    errors.append(f'{operation_id} references unknown next step {next_id}')
        if not operation.get('outcomes') and not operation.get('failure_paths') and not operation.get('gap_ids'):
            errors.append(f'{operation_id} has no outcome, failure path, or gap')
        for gap_id in operation.get('gap_ids', []):



def check_claims(value, evidence, errors, warnings, path='manifest'):
    if isinstance(value, dict):
        certainty = value.get('certainty')
        if certainty is not None and certainty not in CERTAINTIES:
            errors.append(f'{path} has invalid certainty {certainty}')
        for evidence_id in value.get('evidence_ids', []):
            if evidence_id not in evidence:
                errors.append(f'{path} references unknown evidence {evidence_id}')
        if certainty in {'observed', 'corroborated'} and not value.get('evidence_ids'):
            warnings.append(f'{path} is {certainty} without evidence')
        for key, child in value.items():
            check_claims(child, evidence, errors, warnings, f'{path}.{key}')
    elif isinstance(value, list):
        for number, child in enumerate(value):
            check_claims(child, evidence, errors, warnings, f'{path}[{number}]')


def compare(previous, current):
    result = []
    for collection in COLLECTIONS:
        before = {item['id']: item for item in previous.get(collection, [])}
        after = {item['id']: item for item in current.get(collection, [])}
        for item_id in sorted(after.keys() - before.keys()):
            result.append({'kind': 'added', 'collection': collection, 'ref': item_id})
        for item_id in sorted(before.keys() - after.keys()):
            result.append({'kind': 'removed', 'collection': collection, 'ref': item_id})
        for item_id in sorted(before.keys() & after.keys()):
            if before[item_id] != after[item_id]:
                result.append({'kind': 'changed', 'collection': collection, 'ref': item_id})
    return result


def esc(value):
    return html.escape(str(value if value is not None else ''))


def badge(value):
    # Certainty remains available in the canonical manifest for agent use, but
    # displaying it on every report card and interaction step adds visual noise.
    return ''


def anchors(ids, evidence):
    output = []
    for evidence_id in ids or []:
        item = evidence.get(evidence_id)
        if not item:
            continue
        label = item.get('path', evidence_id)
        if item.get('line_start'):
            label += ':' + str(item['line_start'])
        output.append(f'''<a href='#evidence-{esc(evidence_id)}'>{esc(label)}</a>''')
    return f'''<span class='evidence-links'>{' · '.join(output)}</span>'''


def cards(items, evidence, mode, names=None):
    output = []
    for item in items:
        title = item.get('name') or item.get('title') or item.get('id')
        if mode == 'interface':
            detail = f'''<p class='operation'>{esc(item.get('operation'))}</p>
            <p>{esc(item.get('description'))}</p>
            <p class='meta'>{esc(item.get('kind'))} · {esc(item.get('direction'))}</p>'''
        elif mode == 'connection':

            target = friendly(item.get('to_ref'))
            title = f'{source} → {target}'
            detail = f'''<p class='operation'>{esc(item.get('mechanism'))}: {esc(item.get('contract'))}</p>
            <p>{esc(item.get('rationale'))}</p>'''
        elif mode == 'heuristic':
            detail = f'''<p>{esc(item.get('description'))}</p>
            <p class='meta'>{esc(item.get('kind'))}</p>'''
        elif mode == 'gap':
            title = str(item.get('kind') or 'Verification gap').replace('-', ' ').title()

            <p><strong>Why it matters:</strong> {esc(item.get('impact'))}</p>
            <p><strong>Evidence trail checked:</strong></p>{trail}
            <p class='meta'>Trail ends at: {esc(scope)}</p>'''
        elif mode == 'conflict':
            title = 'Conflicting evidence'
            observations = ''.join(
                f'''<li>{esc(observation.get('value'))}</li>'''
                for observation in item.get('observations', [])
            )
            detail = f'''<p>{esc(item.get('claim'))}</p>
            <ul>{observations}</ul><p><strong>Why it matters:</strong>
            {esc(item.get('impact'))}</p>'''
        else:
            detail = f'''<p>{esc(item.get('description'))}</p>
            <p class='meta'>{esc(item.get('kind'))} · {esc(item.get('path'))}</p>'''
        output.append(f'''<article class='card searchable' id='{esc(item.get('id'))}'>
        <div class='card-head'><h3>{esc(title)}</h3>{badge(item.get('certainty'))}</div>
        {detail}{anchors(item.get('evidence_ids'), evidence)}</article>''')
    return ''.join(output) or '''<p class='empty'>None recorded.</p>'''


def render(data, output, previous=None):
    errors, warnings = validate(data)
    if errors:
        raise ValueError('Manifest validation failed:\n' + '\n'.join(errors))
    evidence = {item['id']: item for item in data['evidence']}
    components = {item['id']: item for item in data['components']}
    operations = {item['id']: item for item in data['operations']}
    names = {item_id: item.get('name') or item.get('title') or item_id
             for item_id, item in {**components, **operations}.items()}
    for operation_id, operation in operations.items():
        owner_name = components.get(operation.get('component_id'), {}).get('name')
        names[operation_id] = (f'''{owner_name} — {operation.get('name')}'''
                               if owner_name else operation.get('name') or operation_id)
    changes = compare(previous, data) if previous else data.get('changes', [])
    style = (Path(__file__).resolve().parent.parent / 'assets' / 'report.css').read_text(encoding='utf-8')
    doc = data['document']
    operation_output = {}
    for operation in data['operations']:
        endpoint = operation.get('inbound_endpoint', {})
        endpoint_fields = (

            ('Subscription / consumer group', endpoint.get('subscription')),
            ('Authentication', endpoint.get('authentication')),
            ('Handler', endpoint.get('handler')),
            ('Payload', endpoint.get('payload')),
            ('Ingress path', ' → '.join(endpoint.get('ingress_path', []))),
        )
        known_endpoint_rows = ''.join(
            f'''<dt>{esc(label)}</dt><dd>{esc(value)}</dd>'''
            for label, value in endpoint_fields
            if value and value != 'not-applicable' and 'unknown' not in str(value).lower()
        )
        endpoint_gaps = endpoint.get('gap_ids', [])
        gap_link = (f'''<p class='endpoint-gap'><a href='#{esc(endpoint_gaps[0])}'>
        Incomplete endpoint evidence</a></p>''' if endpoint_gaps else '')
        endpoint_output = (f'''<div class='inbound-endpoint'><h4>Inbound endpoint</h4>
        <dl>{known_endpoint_rows}</dl>{gap_link}</div>''' if known_endpoint_rows else gap_link)
        nodes = []
        for step in sorted(operation.get('steps', []), key=lambda item: item.get('sequence', 0)):
            component = components.get(step.get('component_id'), {})
            states = step.get('state_changes', [])
            state_text = '; '.join(
                value if isinstance(value, str) else value.get('description', str(value))
                for value in states
            )
            nodes.append(f'''<div class='interaction-step searchable'><div class='node-top'>
            <span>{esc(component.get('name') or step.get('kind'))}</span>{badge(step.get('certainty'))}</div>
            <strong>{esc(step.get('action'))}</strong><small>{esc(state_text)}</small>
            {anchors(step.get('evidence_ids'), evidence)}</div>''')
        outcomes = ''.join(
            f'''<li>{badge(item.get('certainty'))} <strong>{esc(item.get('name'))}</strong>
            {esc(item.get('description'))}</li>''' for item in operation.get('outcomes', [])
        ) or '<li>No successful outcome recorded.</li>'
        failures = ''.join(
            f'''<li>{badge(item.get('certainty'))} <strong>{esc(item.get('name'))}</strong>
            {esc(item.get('description'))}</li>''' for item in operation.get('failure_paths', [])
        ) or '<li>None recorded.</li>'
        operation_output[operation.get('id')] = f'''<details class='operation-card searchable' id='{esc(operation.get('id'))}'>
        <summary><strong>{esc(operation.get('name'))}</strong><span>{esc(operation.get('entry_point'))}</span></summary>
        <p>{esc(operation.get('summary'))}</p>{endpoint_output}
        <h4>Interaction sequence</h4><div class='interaction-sequence'>{'''<span class='arrow'>→</span>'''.join(nodes)}</div>

            linked_component = components.get(linked_operation.get('component_id'), {})
            operation_label = linked_operation.get('name') or 'External boundary or evidence gap'
            stage_body = f'''<strong>{esc(stage.get('title'))}</strong><p>{esc(stage.get('description'))}</p>
            <small>{esc(linked_component.get('name') or operation_label)}</small>'''

    operation_groups = {component_id: [] for component_id in components}
    for operation in data['operations']:
        operation_groups.setdefault(operation.get('component_id'), []).append(operation)
    component_nav = ''.join(
        f'''<a href='#section-{esc(component_id)}'>{esc(component.get('name'))}</a>'''
        for component_id, component in components.items()
    )
    toc_components = []
    component_sections = []
    for component_id, component in components.items():
        component_operations = operation_groups.get(component_id, [])
        operation_links = ''.join(
            f'''<li><a href='#{esc(operation.get('id'))}'><strong>{esc(operation.get('name'))}</strong>
            <span>{esc(operation.get('entry_point'))}</span></a></li>'''
            for operation in component_operations
        ) or '<li>No documented operations.</li>'
        toc_components.append(f'''<li class='toc-component searchable'>
        <a href='#section-{esc(component_id)}'><strong>{esc(component.get('name'))}</strong></a>
        <ol>{operation_links}</ol></li>''')
        operation_details = ''.join(operation_output.get(operation.get('id'), '')
                                    for operation in component_operations)
        component_sections.append(f'''<section class='component-section' id='section-{esc(component_id)}'>
        <h2>{esc(component.get('name'))}</h2>
        <div class='component-overview'><h3>Component overview</h3>
        <dl><dt>Responsibility</dt><dd>{esc(component.get('description'))}</dd>
        <dt>Architectural role</dt><dd>{esc(component.get('kind'))}</dd>
        <dt>Documented operations</dt><dd>{len(component_operations)}</dd></dl>
        <ol class='component-operation-links'>{operation_links}</ol></div>
        <h3>Operations</h3>
        {operation_details or '<p class="empty">No documented operations.</p>'}</section>''')
    domain_component_index = f'''<nav class='report-toc' aria-label='Domain, component, and operation contents'>
    <ol>{''.join(toc_components)}</ol></nav>'''
    component_section_output = ''.join(component_sections)
    heuristic_output = cards(data.get('domain_heuristics', []), evidence, 'heuristic')

    evidence_output = ''.join(
        f'''<article class='evidence searchable' id='evidence-{esc(item.get('id'))}'>
        <h3>{esc(item.get('path'))}{':' + esc(item.get('line_start')) if item.get('line_start') else ''}</h3>
        <p>{esc(item.get('observation'))}</p><small>{esc(item.get('source_kind') or 'source')}</small>
        </article>''' for item in data['evidence']
    ) or '''<p class='empty'>No evidence recorded.</p>'''
    gap_output = cards(data['gaps'], evidence, 'gap')
    conflict_output = cards(data['conflicts'], evidence, 'conflict')
    change_output = ''.join(
        f'''<li class='searchable'><strong>{esc(item.get('kind'))}</strong>
        {esc(item.get('collection'))} / {esc(item.get('ref'))} {esc(item.get('summary'))}</li>'''
        for item in changes
    ) or '<li>No baseline changes recorded.</li>'
    root_output = ''.join(
        f'''<li><strong>{esc(item.get('label'))}</strong>
        <small>{esc(item.get('branch'))}{' @ ' + esc(item.get('commit')) if item.get('commit') else ''}
        · fetch {esc(item.get('fetch_status') or 'not-checked')}</small></li>'''

    page = f'''<!doctype html><html lang='en'><head><meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>{esc(doc.get('title'))}</title><style>{style}</style></head><body>
    <header><div><h1>{esc(doc.get('title'))}</h1>
    <p>{esc(doc.get('summary'))}</p></div>
    <label class='search'>Search report<input id='search' type='search'
    placeholder='operation, component, evidence…'></label></header>
    <nav><a href='#domain'>{esc(doc.get('domain'))} domain</a>{component_nav}</nav><main>
    <section id='domain'><h2>{esc(doc.get('domain'))} domain</h2>
    <p class='section-intro'>{esc(doc.get('summary'))}</p>
    <h3>Table of contents</h3>

    {component_section_output}
    <section id='issues'><h2>Verification gaps and trail ends</h2>
    <p class='section-intro'>What could only be partially verified, what could not be verified, and where the available evidence trail ends.</p>
    <h3>Could not fully verify</h3><div class='grid'>{gap_output}</div>
    <h3>Conflicting evidence</h3><div class='grid'>{conflict_output}</div></section>
    <section id='evidence'><h2>Source evidence</h2><details class='evidence-disclosure'>
    <summary>Show source anchors</summary><div class='evidence-grid'>{evidence_output}</div></details></section></main>
    <script>const search=document.querySelector('#search');
    search.addEventListener('input',()=>{{const query=search.value.trim().toLowerCase();
    document.querySelectorAll('.searchable').forEach(item=>{{
    item.hidden=Boolean(query)&&!item.textContent.toLowerCase().includes(query);}});}});
    function openTarget(){{const target=document.querySelector(location.hash);if(!target)return;
    if(target.tagName==='DETAILS')target.open=true;const parent=target.closest('details');if(parent)parent.open=true;}}
    window.addEventListener('hashchange',openTarget);openTarget();</script>
    </body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    init.add_argument('output', type=Path)
    init.add_argument('--title', required=True)
    init.add_argument('--domain', required=True)
    init.add_argument('--source', action='append', required=True)
    check = commands.add_parser('validate')
    check.add_argument('manifest', type=Path)
    report = commands.add_parser('render')
    report.add_argument('manifest', type=Path)
    report.add_argument('output', type=Path)
    report.add_argument('--previous', type=Path)
    difference = commands.add_parser('diff')
    difference.add_argument('previous', type=Path)
    difference.add_argument('current', type=Path)
    difference.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'init':
        write(args.output, initialize(args.title, args.domain, args.source))
        print(f'Initialized {args.output}')
    elif args.command == 'validate':
        errors, warnings = validate(read(args.manifest))
        for warning in warnings:
            print(f'WARNING: {warning}')
        if errors:
            for error in errors:
                print(f'ERROR: {error}', file=sys.stderr)
            return 1
        print(f'Valid: {args.manifest} ({len(warnings)} warnings)')
    elif args.command == 'render':
        previous = read(args.previous) if args.previous else None
        render(read(args.manifest), args.output, previous)
        print(f'Rendered {args.output}')
    else:
        result = compare(read(args.previous), read(args.current))
        if args.output:
            write(args.output, result)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

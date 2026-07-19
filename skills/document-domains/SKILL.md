
# Document Domains



Use one hierarchy throughout the report: **domain → components → operations**.




For every Git repository:

1. Read repository instructions and inspect status, remotes, local branches, remote-tracking branches, and origin HEAD.
2. Resolve main first, then master. Do not treat the currently checked-out feature branch as documentation truth.
3. Fetch the configured enterprise remote when repository instructions and credentials permit. Use the fetched origin/main or origin/master commit.

Treat build and test results as supporting evidence. Keep static source anchors for documented claims.

## Start or hydrate

1. Identify all user-supplied source roots and the requested output directory.
2. Inspect existing output for domain-manifest.json.


    python <skill-dir>/scripts/domain_report.py init <output>/domain-manifest.json --title <title> --domain <domain> --source <path> [--source <path> ...]

Read [manifest-spec.md](references/manifest-spec.md) before authoring or updating the manifest. Read [investigation-playbook.md](references/investigation-playbook.md) before searching unfamiliar source or connecting components.

## Investigate in passes



### 2. Discover components and public interfaces

- Identify deployable components and meaningful subsystem boundaries from source evidence.
- Search language- and framework-specific entry-point patterns only after identifying the technologies present.
- Enumerate operations separately even when they share a route, handler, class, topic, or command.
- Record an evidence anchor for every component and interface.

### 3. Trace every operation

- Follow each entry point through validation, authorization, orchestration, domain decisions, data transformations, persistence, outbound calls/messages, side effects, responses, and failure or compensation paths.
- Trace forward from the interface and reverse from observed sinks to expose skipped hops.
- Preserve branches and asynchronous boundaries. Do not flatten them into a single happy path.
- Stop at an evidenced result, an external/local boundary, or an explicit gap.


- Mark it inferred when the link is reasoned but incomplete; include rationale and competing possibilities.






Run the renderer contract tests before generating a report:

    python -m unittest discover -s <skill-dir>/tests -p "test_*.py"

Run manifest validation repeatedly while building the model:

    python <skill-dir>/scripts/domain_report.py validate <output>/domain-manifest.json

Render the self-contained report after validation:

    python <skill-dir>/scripts/domain_report.py render <output>/domain-manifest.json <output>/domain-report.html

For hydration, include the prior manifest so the report contains a deterministic change summary:



Do not declare completion until:

- Every supplied root is represented in coverage.
- Every Git root identifies the evaluated main or master commit and fetch status, or records an explicit canonical-revision gap.
- Every discovered public entry point maps to one component operation or an explicit gap.
- Every operation has a complete inbound-endpoint record; every unknown endpoint field references an explicit evidence gap.

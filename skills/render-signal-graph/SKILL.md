---
name: render-signal-graph
description: Render a data-only JSON projection of a TypeScript Signal architecture model into a rich, self-contained interactive HTML architecture canvas. Use after build-signal-graph whenever a user asks for architecture visualization, component relationships, operation impact, endpoint-to-persistence/message/downstream tracing, path highlighting, or an HTML projection of a Signal model.
compatibility: Requires already-installed TypeScript compiler (tsc) and Node.js; no third-party packages.
license: See LICENSE
---

# Render Signal Graph

Render the built and type-checked Signal TypeScript model as one interactive architecture canvas. The TypeScript remains authoritative; HTML is a disposable projection.

Read the sibling build skill's [TypeScript DSL contract](../build-signal-graph/references/typescript-dsl.md) before rendering.

## Visual contract

Represent each architectural identity exactly once:

- actors, services, stores, brokers, and external APIs are stable boxes;
- systems provide ownership context rather than duplicate runtime boxes;
- endpoints are labelled HTTP interaction arrows, not boxes;
- messages are labelled publish/consume arrows, not boxes;
- subscriptions route broker/topic interactions to the owning consumer service;
- reads, writes, deletes, requests, responses, publications, consumption, and downstream calls are separate directional edges.

Never duplicate a component to make execution order easier to draw. Never collapse distinct actions into slash-separated labels such as `INSERT/UPDATE/DELETE`. Multiple interactions between the same boxes remain separate, offset edges whose arrowheads physically touch both boxes.

## Path interaction

The canvas must preserve the complete architecture while letting a user understand what an operation touches:

1. Compile all `flow` and `continuesFrom` relationships into complete root-to-leaf path variants.
2. Attach every rendered interaction to every complete path containing its flow segment.
3. Make every component and interaction selectable.
4. When an initiating endpoint or other interaction belongs to several caller/outcome paths, show those choices.
5. On path selection, highlight every participating interaction and box from actor through HTTP, application services, persistence, transport, consumers, downstream APIs, terminal writes, and notifications.
6. Keep unrelated architecture visible but dimmed.
7. Reuse the same stable box when a path loops back through a broker or service.

An endpoint selection must reveal everything that operation touches; highlighting only `BFF → API` is a failed projection.

## Workflow

1. Confirm the model uses the sibling `build-signal-graph` DSL and passes strict TypeScript checking.
2. Reject legacy/ambiguous steps that omit the executor or operation label for persistence and publication.
3. Compile `signal.ts` and root `architecture.ts` with the existing `tsc` to type-check them. Do not execute the compiled model.
4. Write `architecture.json` as a data-only projection of the root architecture object. Replace every declaration or flow reference with `{ "$ref": "ExportName" }`; do not put JavaScript, imports, or expressions in this file.
5. Compile [scripts/render.ts](scripts/render.ts) with the existing `tsc`; do not install loaders, React, layout libraries, or templates.
6. Run the compiled renderer against `architecture.json`. The renderer parses JSON and never loads the architecture as executable code.
7. Open the generated HTML and test component selection, interaction selection, all path choices, reset, arrow attachment, parallel-edge readability, loops, desktop width, narrow width, and keyboard access.

```sh
tsc --strict --target ES2022 --module commonjs --outDir .architecture-build architecture/signal.ts architecture/architecture.ts
tsc --strict --target ES2022 --module commonjs --outDir .architecture-build/render /absolute/path/to/render-signal-graph/scripts/render.ts
node .architecture-build/render/render.js architecture/architecture.json architecture/index.html
```

## Output

Write one `architecture/index.html` containing:

- one responsive SVG architecture canvas;
- one box per architectural identity;
- individually labelled directional interactions;
- complete selectable path variants derived from live object references;
- click and keyboard path highlighting;
- a path/details panel;
- deterministic embedded projection data;
- no external assets or network dependencies;
- contextual escaping and a restrictive CSP.

## Failure conditions

Fail rather than guessing when:

- the JSON has no architecture object;
- the JSON contains a reference that does not name a root declaration or flow;
- one object is exported under multiple keys;
- a relationship points outside the root architecture;
- an operation lacks an explicit executor or meaningful action label;
- a continuation cycle exists;
- a selected endpoint cannot be connected to its full modeled path;
- rendering would require duplicating an architectural identity.

## Quality gate

Run `node tests/run-tests.js`. Then inspect the generated result in a browser. Completion requires strict typing, deterministic output, one box per identity, separate parallel interactions, visible arrowheads touching their boxes, complete endpoint-to-terminal path highlighting, safe output, and usable desktop/mobile rendering.

Apply [evals/evals.json](evals/evals.json) and preserve every iteration's TypeScript, HTML, validation, screenshot, grading, and benchmark artifacts for regression comparison.

# Execution

## Eval prompt

"Using only the supplied Microsoft eShopOnContainers evidence, create the most useful broad architecture diagram for an engineer who needs to understand the system's callers, ownership boundaries, runtime services, stores, external infrastructure, and major directed HTTP, persistence, messaging, and notification relationships. This is a structural overview, not a request timeline. Do not invent unsupported components or interactions. Preserve the source used to generate the diagram and make the final artifact self-contained and reviewable offline."

## Skill pair used

- `skills/mermaid-diagrams/SKILL.md`
- `skills/show-me/SKILL.md`

No other visualization skill was used.

## Outputs

- `architecture.mmd` — authoritative Mermaid structural source.
- `architecture-review.html` — self-contained offline review page; includes the authoritative source and a non-rendered semantic index.
- `validation-notes.md` — coverage, offline, and rendering-status checks.
- `execution.md` — this execution record.

## Decisions and uncertainties

A left-to-right flowchart was selected because the request is a broad topology and ownership view, not a timeline. The compact HTML view supplements the source with boundary cards and a relationship index without pretending to render Mermaid. Unsupported payment-failure details, SignalR recipients, AwaitingValidation producer details, and a Payment store were omitted and recorded in validation notes.

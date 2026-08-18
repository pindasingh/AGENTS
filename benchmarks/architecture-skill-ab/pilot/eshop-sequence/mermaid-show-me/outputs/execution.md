# Execution

## Eval prompt

> "Using only the supplied Microsoft eShopOnContainers evidence, create the most useful sequence diagram for an engineer who needs to understand checkout acceptance followed by asynchronous order processing. Show the web caller path, the exact point of the HTTP 202 response, successful completion, stock rejection, and every evidenced store, event, consumer, and notification involved. Preserve exact contract names where the evidence provides them, do not invent unsupported behavior, and make the final artifact self-contained and reviewable offline."

## Skill pair used

- `skills/mermaid-diagrams/SKILL.md`
- `skills/show-me/SKILL.md`

No other visualization skill was used.

## Outputs

- `checkout-order-processing.mmd` — authoritative Mermaid sequence source.
- `review.html` — self-contained offline review artifact, with a compact visual walkthrough and embedded source.
- `validation.md` — coverage, safety, and validation record.

## Uncertainties

The fixture says payment failure is a required path variant, but does not provide its contract, state transition, persistence effect, or notification. It also does not name the stock-confirmed result, stock-rejected result, or paid-status contracts. These gaps are called out rather than filled with likely names. The mobile BFF is evidenced but omitted from the sequence because the requested caller path is specifically the web path; no mobile-specific checkout interaction is supplied.

No Mermaid renderer was used, so the source is not claimed to have been renderer-validated.

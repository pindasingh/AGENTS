# Map-to-C4 evaluations

These evaluations use the live official pages at [c4model.com](https://c4model.com/) as the normative source. They cover:

- Software System boundary uncertainty and repository overlap;
- Containers, web process boundaries, managed data stores, microservices, queues, and topics;
- correct System Context, Container, Component, and Code scopes;
- evidence thresholds and optional lower-level views;
- notation and the official review checklist;
- System Landscape, Dynamic, and Deployment views;
- canonical modelling, filtered views, scale, terminology, and C4's scope limits.

Each Markdown file is a reasoning eval with a prompt, required result, and explicit fail conditions. A response fails if it matches any fail condition, even if other parts are correct. Official URLs in each file identify the grading authority.

Run the deterministic portion from the skill directory:

```bash
python evals/run_evals.py
```

The runner verifies that every eval is linked from `SKILL.md`, all normative site topics remain covered, all four core views render as connected annotated SVG, invalid abstraction mixing is rejected, Dynamic interactions are numbered, and generated packages pass the bundled validator. It does not pretend to execute an LLM; architectural reasoning cases must also be applied to the agent response being reviewed.

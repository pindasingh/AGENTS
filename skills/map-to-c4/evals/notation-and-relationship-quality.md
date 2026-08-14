# Evaluation: notation and relationship quality

## Official sources

- https://c4model.com/introduction
- https://c4model.com/diagrams/notation
- https://c4model.com/diagrams/checklist
- https://c4model.com/diagrams/faq

## Prompt

Review a proposed Container diagram page. It has blue and grey cards in an HTML grid, a prose relationship table below, arrow characters used as bullets, no legend, relationships labelled `Uses`, container technology only in tooltips, no protocol labels, and acronyms `OMS` and `AMQP` without explanation. The author says C4 is notation independent, so visible connectors are optional and blue is mandatory.

## Required outcome

- Reject the page as a diagram under the skill's boxes-and-lines rendering profile because relationships are not visible connectors on the same canvas.
- Require a title naming diagram type and scope plus a key explaining all visual semantics.
- Require every element's name, explicit type, short responsibility; every Container/Component needs visible technology.
- Require every relationship to be unidirectional, visibly arrowed, and specifically labelled in wording that matches its direction.
- Require protocol/technology where applicable, especially inter-Container communication.
- Explain all acronyms, abbreviations, colours, shapes, borders, sizes, line styles, and arrowheads.
- State that dependency or data-flow direction is acceptable when the label matches.
- State that C4 mandates neither blue/grey colours nor boxes-and-arrows, but any chosen notation must be understandable and consistent without relying on colour alone.

## Fail conditions

Fail if the response:

- accepts the prose table as a substitute for connectors;
- accepts bidirectional, unlabelled, or vague `Uses` arrows;
- hides required information exclusively in interaction such as tooltips;
- claims a fixed colour or shape is required by C4;
- omits a key because the notation looks familiar;
- approves without inspecting the rendered artifact.

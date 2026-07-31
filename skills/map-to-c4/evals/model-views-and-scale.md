# Evaluation: model, views, and scale

## Official sources

- https://c4model.com/tooling
- https://c4model.com/faq
- https://c4model.com/diagrams/faq
- https://c4model.com/diagrams/notation

## Prompt

A reconciled model has 80 Containers and 400 relationships. A user requests one tiny Container diagram and proposes copying boxes into eight pages, renaming them independently, mixing Components into sparse areas, and creating `Payments group` and `Data stores group` pseudo-elements to reduce line count.

## Required outcome

- Keep one non-visual authoritative directed graph of stable elements and relationships, then render filtered views from it.
- Split the crowded Container story into focused diagrams at the same abstraction level, for example by business area, feature, use case, or inbound/outbound dependency neighbourhood.
- Preserve stable names, IDs, C4 types, direction, and relationship meaning across views.
- Do not mix Components into Container views or invent group pseudo-elements as architectural identities.
- Accept the trade-off that filtered views lose some big-picture detail; optionally supplement them with a suitable landscape or alternative visualisation.
- Prefer repeatable modelling/generation over copied diagram elements so changes remain consistent and reviewable.

## Fail conditions

Fail if the response:

- forces the entire model onto one unreadable canvas;
- solves crowding by shrinking text until it is illegible;
- changes an element's C4 type between filtered views;
- duplicates or independently renames model elements;
- creates organisational/group boxes as Software Systems, Containers, or Components;
- mixes abstraction levels to fill whitespace.

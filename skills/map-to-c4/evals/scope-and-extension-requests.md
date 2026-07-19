# Evaluation: scope and extension requests

## Official sources

- https://c4model.com/abstractions/faq
- https://c4model.com/faq
- https://c4model.com/abstractions

## Prompt

A user asks to: (1) rename Container to `Runtime Unit`, (2) add `Domain`, `Layer`, and `Shared Library` as abstraction levels between Software System and Container, (3) model a business approval workflow and state machine as Components, and (4) document a standalone SDK as a Software System despite having no running application or data store.

## Required outcome

- Allow local terminology such as `Runtime Unit` only when its mapping to the C4 Container definition is explicit and understood by the audience.
- Preserve the fixed hierarchy and do not add Domain, Layer, or Shared Library merely as organisational groupings.
- Treat extra abstraction levels as an advanced exception requiring a genuine need and precise definition, not as a convenience.
- Keep business processes, workflows, state machines, and domain models outside C4's static-structure abstractions; recommend appropriate supplementary notation.
- Explain that C4 is designed around software systems and is often not the best primary notation for a standalone library/framework/SDK.
- Offer a code-oriented view such as UML or a C4 usage example showing how an evidenced Software System embeds the SDK.

## Fail conditions

Fail if the response:

- equates renamed terminology with permission to change the abstraction meaning;
- creates `Domain`, `Layer`, or `Shared Library` C4 element types without precise justification;
- labels workflow steps or states as Components;
- invents runtime Containers for a non-running SDK;
- claims C4 universally covers every architectural concern;
- refuses all terminology adaptation even when the mapping remains explicit.

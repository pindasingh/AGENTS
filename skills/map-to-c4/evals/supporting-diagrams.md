# Evaluation: supporting diagrams

## Official sources

- https://c4model.com/diagrams/system-landscape
- https://c4model.com/diagrams/dynamic
- https://c4model.com/diagrams/deployment
- https://c4model.com/diagrams

## Prompt

An enterprise has Ordering and Billing Software Systems. The user wants: (1) a portfolio overview, (2) the runtime sequence for checkout, and (3) production infrastructure. They propose using these three views instead of System Context and Container diagrams, putting load balancers on the Container diagram, and drawing unnumbered runtime arrows between invented temporary elements.

## Required outcome

- Use a System Landscape for the portfolio: People and peer Software Systems in the enterprise/organisation scope, without one focused Software System.
- Retain System Context and Container diagrams for each in-scope Software System; supporting diagrams do not replace the core views.
- Use a Dynamic diagram only for the checkout story when useful; reuse static-model elements and number interactions in runtime order.
- Make Dynamic labels directional and specific about requests, responses, events, commands, or mutations.
- Use a production Deployment diagram to map Software System/Container instances to nested deployment nodes and supporting infrastructure nodes.
- Keep each Deployment diagram scoped to one named environment and create separate views when environments differ.
- Put load balancers, DNS, firewalls, replicas, pods, and similar infrastructure in Deployment rather than Container views.

## Fail conditions

Fail if the response:

- uses System Landscape, Dynamic, or Deployment as a replacement for core static views;
- gives a System Landscape one focused Software System and calls it System Context without the direct-neighbour scope;
- invents Dynamic-only pseudo-elements instead of reusing the static model;
- leaves Dynamic interactions unnumbered;
- mixes production and staging nodes without a clear environment scope;
- treats deployment nodes or infrastructure nodes as C4 Containers.

# Evaluation: core diagram scopes

## Official sources

- https://c4model.com/diagrams
- https://c4model.com/diagrams/system-context
- https://c4model.com/diagrams/container
- https://c4model.com/diagrams/component
- https://c4model.com/diagrams/code

## Prompt

A confirmed Ordering Software System has customers, a Payment Software System, a web application, an API, a database, internal order and payment components in the API, and classes implementing the order component. A stakeholder asks for one “complete C4 diagram” containing every item, HTTP details, Kubernetes replicas, and class methods.

## Required outcome

- Reject the single mixed-abstraction diagram and provide a navigable zoom chain.
- System Context scope is Ordering; include only Ordering, directly connected People, and external Software Systems. Omit protocols, technologies, Containers, Components, and code.
- Container scope is Ordering; include its applications/data stores and directly connected People/Software Systems. Show responsibilities, technologies, and communication protocols; omit replicas/topology.
- Component scope is the API Container only; include its Components and directly connected Containers, People, or Software Systems. Do not include Components from another Container.
- Code scope is the selected order Component only; include observed code elements and static code relationships, showing only useful members.
- Treat System Context and Container as recommended; create Component/Code only if they add value and evidence supports them.

## Fail conditions

Fail if the response:

- mixes Software Systems, Containers, Components, and classes inside one scoped boundary;
- places the Payment Software System inside Ordering;
- includes HTTP/Kubernetes detail on System Context;
- labels Kubernetes replicas as Containers;
- scopes a Component diagram to several Containers;
- scopes a Code diagram to the repository or entire API;
- claims all four diagrams are mandatory.

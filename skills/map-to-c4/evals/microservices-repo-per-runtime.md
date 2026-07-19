# Evaluation: microservices split across repositories

## Official sources

- https://c4model.com/abstractions/software-system
- https://c4model.com/abstractions/container
- https://c4model.com/abstractions/component
- https://c4model.com/abstractions/microservices
- https://c4model.com/diagrams/container

## Prompt

You are given six repositories that contribute to one product owned by one team:

1. `fulfilment-api` builds and deploys an HTTP API process.
2. `fulfilment-worker` builds and deploys a queue-consuming worker process.
3. `fulfilment-scheduler` builds and deploys a scheduled-job process.
4. `fulfilment-database` owns one relational database schema and its migrations.
5. `fulfilment-contracts` publishes a library of message/request types but does not run.
6. `fulfilment-client` contains a generated API client and does not run independently.

The API, worker, scheduler, and schema jointly deliver one user-valued Fulfilment software system. Produce the C4 classification and describe how repository overlap is condensed.

## Required classification

- `Fulfilment` is one **Software System** because the scenario explicitly establishes shared ownership and one user-valued system boundary.
- `fulfilment-api` maps to an **Application Container**.
- `fulfilment-worker` maps to an **Application Container**.
- `fulfilment-scheduler` maps to an **Application Container**.
- `fulfilment-database` maps to a **Data Store Container** representing the owned schema.
- `fulfilment-contracts` is shared code/contract evidence attached to the containers that embed it; it is not a Container because it does not run or store data.
- `fulfilment-client` is a contract mirror/generated client attached to its consuming container; it is not a Software System or Container.
- Components are identified separately inside each application Container from cohesive functionality and interfaces. Repository identity alone does not create a Component.
- The canonical model contains one element per established runtime/data boundary with evidence links back to all repositories.

## Required diagrams

- System Context: one Fulfilment Software System, its people, and directly connected external Software Systems.
- Container: API, worker, scheduler, and database schema inside the Fulfilment boundary with labelled communication/protocol relationships.
- Component: a separate diagram for a selected API, worker, or scheduler Container only when internal components add value.
- Code: a selected important/complex Component only.

## Fail conditions

Fail the evaluation if the response:

- creates one Software System per repository without ownership/value evidence;
- calls the API, worker, scheduler, or database a C4 Component merely because the user used the word “component”;
- calls the database schema a code Component rather than a Data Store Container;
- treats the contracts or generated-client repository as a running Container;
- combines components from different runtime Containers into one Component diagram;
- treats a Docker image/pod/VM as the definition of a C4 Container;
- omits labelled relationships and protocols between runtime Containers.

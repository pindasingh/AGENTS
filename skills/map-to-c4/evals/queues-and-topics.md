# Evaluation: queues and topics

## Official sources

- https://c4model.com/abstractions/container
- https://c4model.com/abstractions/queues-and-topics
- https://c4model.com/diagrams/notation

## Prompt

Inside one Software System, Producer A sends commands consumed only by Consumer C through queue X. Producer B publishes account events to topic Y, and Consumers C and D subscribe. All queues/topics happen to run on one RabbitMQ cluster in development and on three brokers in production. Model the static architecture and explain ownership if Producer B later becomes a separately owned Software System.

## Required outcome

- Do not model the generic RabbitMQ message bus/cluster as the single C4 Container merely to form a hub-and-spoke picture.
- Either model queue X and topic Y as distinct Data Store Containers or, for the genuine point-to-point X interaction, omit X and name it on the A-to-C relationship.
- Preserve directional publisher/producer and subscriber/consumer relationships with specific labels and messaging technology.
- Keep broker counts and topology in Deployment diagrams, separate from logical queue/topic Containers.
- If Producer B becomes a separate Software System, explicitly determine who owns topic Y; do not silently place the same Container inside two Software Systems.
- If topic Y is implicit, ensure relationships still expose the coupling and topic name.

## Fail conditions

Fail if the response:

- treats the RabbitMQ cluster as the only C4 Container and hides producer/consumer coupling;
- models each broker instance as a Container on the Container diagram;
- uses bidirectional or unlabelled messaging lines;
- loses queue/topic identity entirely;
- assigns a queue/topic to two parent Software Systems;
- calls a queue a Component.

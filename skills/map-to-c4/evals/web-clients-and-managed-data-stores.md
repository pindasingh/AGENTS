# Evaluation: web clients and managed data stores

## Official sources

- https://c4model.com/abstractions/container
- https://c4model.com/diagrams/container
- https://c4model.com/diagrams/deployment

## Prompt

A product has a substantial React single-page application delivered by an ASP.NET server. The browser app calls the server over JSON/HTTPS. The server uses an owned Azure SQL schema and an owned S3 bucket. Azure and AWS host those services. Production also has a CDN, load balancer, three server replicas, and Docker pods. Classify all items and describe the required diagrams.

## Required outcome

- Model the substantial browser application and server application as two Containers because they run in separate process spaces and communicate remotely.
- Model the owned SQL schema and owned S3 bucket as Data Store Containers inside the Software System despite external hosting.
- Label browser-to-server and server-to-store relationships with the observed protocols/technologies on the Container diagram.
- Keep CDN, load balancer, replicas, pods, and environment topology off the Container diagram.
- Put instances and infrastructure into a production Deployment diagram when that view adds value.
- Explain that a mostly server-rendered application with little client-side code could instead be one Container.

## Fail conditions

Fail if the response:

- treats the SPA and server as one Container solely because they share a deployment artifact or repository;
- treats Azure SQL or S3 as external Software Systems solely because another provider hosts them;
- treats Docker pods as the definition of C4 Containers;
- puts replica counts, load balancers, or production nodes on the Container diagram;
- omits technology/protocol from communication between Containers.

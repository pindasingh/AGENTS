# Evaluation: authoritative sequenced end-to-end flows

Apply all cases to representative agent runs and artifact review. Any fail condition is a regression.

## Opportunity search POST — complete successful path

### Prompt

Repositories contain an Opportunities MFE, Mobile App, Opportunity Search API, Eligibility API, Opportunity Details API, and search-index adapter. Evidence shows both clients call `POST /api/opportunities/search` with `SearchRequest v2`. The Search API authenticates the request, dispatches a handler, evaluates a LaunchDarkly flag, reads central configuration, queries Elasticsearch, reads SQL, calls Eligibility and Details, emits Application Insights telemetry, and returns `SearchResponse v2`. Many unrelated Opportunity components and a message bus exist elsewhere.

Build the architecture model for the successful Search Opportunities path.

### Required outcome

- Keep Opportunity as the subject and Search Opportunities as the scenario/path.
- Corroborate each caller from compatible outbound and inbound evidence; do not infer callers from the route alone.
- Store an authoritative flat `sequence` array with hierarchical string numbers such as `1`, `1.1`, `1.2`, `2`, and `2.1`.
- Record authentication, controller/handler hand-offs, LaunchDarkly, configuration, Elasticsearch, SQL, Eligibility, Details, telemetry, and the returned response at their exact execution positions.
- Include dependencies regardless of domain or ownership because the path touches them.
- Exclude the unrelated Opportunity components and unused message bus because the path does not touch them.
- Continue through supplied downstream implementations when compatible interface and operation evidence exists.
- End at the returned `SearchResponse v2` outcome.
- Use a separate final return interaction from the Search API to the originating caller set; do not combine response mapping and network return.
- Create matching `numbered-sequence.md` and `sequence-diagram.txt` artifacts under the flow ID.
- Make JSON, Markdown, and ASCII participant sets, step numbers, order, operations, direction, dependencies, and outcome identical.

### Fail conditions

- Produces a valid node/relationship inventory without a complete sequence.
- Renames the subject to Opportunity Search.
- Uses domain ownership as the dependency inclusion rule.
- Omits LaunchDarkly, central configuration, telemetry, or another touched dependency because it is shared, infrastructural, external, or cross-domain.
- Includes the message bus or unrelated components merely because they exist in the domain.
- Lists dependencies without saying exactly when and why they are used.
- Assigns sequence numbers during Markdown/ASCII generation instead of storing them in `model.json`.
- Stops at the first outbound API despite compatible downstream source being supplied.
- Ends without a response, terminal effect, one-way completion, or explicit gap.
- Treats a local options/appsettings read as a remote configuration service without runtime-call evidence.
- Promotes an unidentified `rules` or `repository` receiver to a stable component from its call-site name alone.
- Combines response mapping and return to the caller into one local API step.

## Hierarchical sequence and artifact drift

### Prompt

A model flow has JSON numbers `1`, `1.1`, `1.2`, `2`, `2.1`, `2.2`. Its Markdown omits `1.2`, renames `2.1`, and calls it `3.1`; its ASCII diagram reverses the dependency at `2.2`. Progress marks every flow-review gate true.

### Required outcome

- Fail projection validation.
- Reset `projectionsValidated` and the flow-review completion state.
- Require the exact JSON number set and order in both artifacts.
- Require the same operation text/meaning, participants, direction, dependency, inputs/outputs or effects, and outcome.
- Treat the model JSON sequence as authoritative; repair projections unless the evidence proves the model itself is wrong.

### Fail conditions

- Accepts approximate semantic similarity.
- Renumbers steps for prettier presentation.
- Treats Markdown or ASCII as independent architecture authority.
- Leaves progress complete after detecting drift.

## Caller and continuation uncertainty

### Prompt

An API exposes `POST /api/v2/search`. A mobile repository contains a similarly named method but uses v1 and an unresolved base URL. The API calls an Eligibility client. The Eligibility repository exposes a compatible v2 route, but its contract fingerprint differs. Production configuration is unavailable.

### Required outcome

- Do not confirm the mobile application as a v2 caller.
- Record caller/target searches and gaps.
- Do not stitch the Eligibility continuation across the incompatible fingerprint.
- Trace the path only to the observed outbound boundaries, mark continuation unresolved, and end the partial path at explicit gaps.
- Set coverage to partial or blocked rather than complete.
- Preserve the unresolved steps in the numbered Markdown and ASCII artifacts.

### Fail conditions

- Matches callers or continuations by similar names alone.
- Hides the unresolved boundary to make the sequence look complete.
- Marks coverage complete with unresolved continuation gaps.
- Omits the partial review artifacts because the path is not fully known.

## Asynchronous continuation

### Prompt

A POST handler writes SQL, publishes `OpportunityChanged v3` to topic `opportunity-changed`, and returns HTTP 202. A worker repository consumes v3 from subscription `search-indexer`, reads the record, updates Elasticsearch, and records telemetry. A legacy worker consumes v2.

### Required outcome

- Model the HTTP response and asynchronous continuation in correct evidence-backed order.
- Preserve publish, named channel, delivery/subscription, consume, SQL read, Elasticsearch update, telemetry, and terminal effect as distinct numbered steps.
- Stitch only the v3 consumer path.
- Preserve the v2 incompatibility as a conflict, not an alternative successful continuation.
- Use a separate path if the HTTP-accepted outcome and background-completion outcome need distinct review stories, with explicit linkage between them.

### Fail conditions

- Treats publish as the terminal architecture outcome when the supplied consumer continuation is evidenced and selected.
- Omits the topic, subscription, contract version, or consumer stage.
- Reverses consumer-to-publisher direction.
- Flattens v2 and v3 into one sequence.

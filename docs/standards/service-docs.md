# Standard: every service documents itself

Status: proposed (this PR). See [Is an ADR needed?](#is-an-adr-needed).

## Why

A platform is only as usable as its documentation. When services talk through
topics rather than calls, the code of one service tells you nothing about who
reacts to its events, so the contract has to be written down. Each service
documents itself in the same shape so a reader can compare any two services in
a minute, and the [airport overview](../architecture/airport-overview.md) can
be assembled from them.

## The rule

Every `svc-*` repository has `docs/service.md`, started from
[`templates/service-doc.md`](../../templates/service-doc.md) (also shipped in
`template-dotnet-service`). It has these sections, in this order:

1. **Purpose**: what it owns and what it deliberately does not do.
2. **Design decisions**: service-level choices with reasons; links to ADRs.
3. **Architecture**: components and how a request or event flows through them.
4. **Inputs**: HTTP API (routes, responses, error shape, where the OpenAPI
   doc is), **events consumed** (topic, subscription, event types, effect,
   what is ignored, contract source) and configuration.
5. **Outputs**: **events published** (topic, event types, when, payload,
   message conventions) and other side effects. "None" is a valid answer.
6. **Dependencies**: what it needs and how it behaves without it.
7. **Failure modes**: each failure, how it shows up (log line, HTTP code,
   dead-letter queue, missing event), impact and what to do. Plus delivery
   semantics: at-least-once, idempotency, what gets dead-lettered.
8. **Running and testing**: standalone, inside the aeroflow-local AppHost,
   tests, and what healthy logs look like.
9. **Known gaps**: each with an issue link.

Keep every heading; write "None" rather than deleting one.

## When to update it

In the same PR as the change. A PR that adds or changes an endpoint, a topic,
a subscription, an event type or a failure path updates `docs/service.md`, and
reviewers ask for it the same way they ask for tests. If a change adds a topic
or a subscription, update the
[airport overview](../architecture/airport-overview.md) too.

## What it is not

- Not a replacement for ADRs. Decisions that bind other services go in
  `docs/decisions/`; the service doc links them.
- Not the API reference. Scalar/OpenAPI (ADR-0015) is the reference for
  request and response shapes; the service doc says what the API is for.
- Not a design doc. It describes what the code does today.

## Enforcement

Review only, for now. A cheap later step is a CI check that `docs/service.md`
exists and has the nine headings, in the shared `dotnet-ci` workflow. Checking
that the content is *true* stays review's job. Trigger to add the check: a
service ships without the doc, or a doc is found out of date with its topics.

## Is an ADR needed?

Probably yes, but small. "Docs are part of the service contract" binds every
squad, changes the definition of done and is the kind of rule that gets
re-litigated, which is what decision records are for. It should record the
rejected alternatives: a central wiki or catalogue (Backstage) that drifts from
the code; generated-only docs (OpenAPI/AsyncAPI) that describe shape but not
behaviour or failure modes; and per-squad freedom of format. AsyncAPI is worth
naming as the revisit trigger if event contracts move to a shared package
(#71). This PR does not add the ADR so it can be written once the shape has
been tried on three services.

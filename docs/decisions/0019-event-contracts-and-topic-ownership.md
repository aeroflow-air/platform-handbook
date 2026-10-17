---
id: 19
title: Event contracts owned per topic, copied per consumer, checked by contract tests
status: draft
date: 2026-10-17
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "aeroflow-local", "aeroflow-workflows", "infra-platform", "template-dotnet-service"]
design-doc: null
---

## Context

Issue #71 asks where shared event contracts live, how `<domain>-events`
topics are named and owned, and how `workload.yaml` declares publish and
subscribe so the generator can wire Service Bus RBAC. ADR-0013 already chose
the bus and one topic per owning service, and left the contract package
layout open. #84 is now settled by ADR-0017 (outbox, deterministic ids,
de-duplication). This record settles the layout ADR-0013 left open; it
supersedes neither ADR-0013 nor ADR-0017.

What the code actually does today (surveyed 2026-10-17):

- **No shared contract package exists.** There is no `lib-*` repo in the org
  and no NuGet publishing between service repos. The only shared contract
  code is inside aeroflow-local: `AeroFlow.Local.FlightEvents`, referenced
  by the flight simulator, the ops dashboard and the placeholders.
- **`flight-events` is copied three times.** svc-gate-allocation,
  svc-flight-status and svc-baggage-reclaim each keep an identical local
  `FlightEventMessage` ("keep the two in step until the contract moves to a
  shared package"). The dashboard likewise keeps local copies of the gate
  and baggage contracts — and one has already drifted in miniature: its
  `GateEventMessage.FlightId` is nullable, the producer's is not.
- **Producers define their own wire types in their domain layer**:
  `GateEvent` (GateAssigned/GateChanged/GateReleased) and `BaggageEvent`
  (BeltAssigned, BagsOnBelt, LastBagOnBelt, ReclaimComplete, BagDelayed).
  Topics are `flight-events`, `gate-events`, `baggage-events`; each service
  publishes only to its own and subscribes on a subscription named after
  itself (ADR-0013). One anomaly: `flight-events` is owned by the
  aeroflow-local flight simulator, a local tool, not by svc-flight-status as
  ADR-0013 assumed.
- **The envelope is a convention, not a schema.** No version field anywhere.
  JSON body (web casing, string enums, nulls omitted when writing):
  `EventId`, `EventType`, `FlightId`, `FlightNumber`, `OccurredAt` plus
  optional per-type fields. Service Bus properties carry the same facts:
  `MessageId` = `EventId`, `Subject` = event type, `CorrelationId` =
  flight id. No trace context is set yet (ADR-0013 wanted it; nothing does).
- **Evolution is fragile in one specific way.** Unknown JSON fields are
  ignored by `System.Text.Json`, so additive fields are safe. But an
  unknown enum value fails deserialisation and every consumer dead-letters
  the message as `unreadable` — a new event type breaks existing consumers
  until they are updated first (each service's CLAUDE.md already warns of
  this). Removing, renaming or retyping a field breaks copies silently:
  nothing today compares a consumer's copy against the producer's shape.
- **`workload.yaml` cannot say any of this.** Every service declares only
  `capabilities: [http]`; the schema (aeroflow-workflows) already allows a
  `queue` capability but no manifest uses it and the generator wires no
  topics, subscriptions or RBAC. This is tracked as part of #64.

## Decision

**Each topic's contract is owned by its producer and lives in the
producer's repo. Consumers keep deliberate local copies, pinned by contract
tests. No shared contract package and no schema registry for now.**

1. **Ownership and naming.** One topic per owning context, named
   `<domain>-events`: the producer is the only publisher, owns the event
   types, fields and their meaning, and documents them in its
   `docs/service.md`. Subscriptions are named after the consuming service
   (`gate-allocation`, `flight-status`, `baggage-reclaim`,
   `ops-dashboard`). `flight-events` ownership stays with the flight
   simulator in aeroflow-local until a real flight service owns the flight
   lifecycle; this corrects the assumption in ADR-0013 rather than hiding
   it. A service never publishes to another service's topic.
2. **Where contracts live.** The producer's wire record (for example
   `GateEvent`, `BaggageEvent`, the simulator's `FlightEvent`) plus its
   service doc is the authoritative contract. Consumers keep a local copy
   shaped for what they read, in their `Messaging` layer (ADR-0004: wire
   types stay at the edge; domain types stay their own). Copies are a
   feature, not a smell: a consumer can ignore fields and event types it
   does not care about without waiting on a package release. Auth is
   unaffected: contracts carry no caller identity (ADR-0018).
3. **Contract tests instead of a package.** Every consumer copy gets a
   wire-compatibility test: a canonical example message per event type it
   handles, taken from the producer's documented contract, must deserialise
   and be handled; an unknown extra field must be tolerated. The producer
   keeps the matching serialisation test for the same examples. Changing a
   contract therefore means changing the producer and then each consumer's
   examples in step — in separate PRs per repo, producer documented first.
   (Implementation is follow-up #111, not part of this record.)
4. **Envelope stays as surveyed.** `MessageId` = `EventId`,
   `Subject` = event type, `CorrelationId` = flight id, JSON body with the
   fields above. No version field is added: at three topics, versioning is
   done by the evolution rules below, and an unused version number would be
   theatre.
5. **Evolution rules.**
   - *Additive is safe and needs no ceremony*: new optional (nullable)
     field, new consumer, new subscription.
   - *A new event type on an existing topic is a breaking change for
     current consumers* (unknown enum → dead-letter). The producer may
     only start emitting it after every current consumer has been updated
     to at least ignore it, or the new type goes on the producer's own
     schedule behind a flag. Consumer-first, producer-second.
   - *Breaking field changes* (remove, rename, retype, new required field,
     changed meaning) never reshape an existing event type. Ship a new
     event type with the new shape and retire the old one once consumers
     have moved, or — only if the whole topic's envelope must change — a
     new topic `<domain>-events-v2` alongside the old. Dual-publish during
     migration is the producer's problem, stated in its service doc.
6. **Ids and duplicates are ADR-0017, unchanged.** Derived events use
   deterministic RFC 9562 v5 ids (`EventIds.Derive(source, type)`; tick
   events use a fixed namespace); the simulator's origin events are the
   exception, minted fresh per flight occurrence. Delivery is at least
   once: consumers must de-duplicate by `EventId` and be idempotent —
   topic duplicate detection (10 minutes, on in the local AppHost) is a
   first line, never the guarantee.
7. **`workload.yaml` declares intent; the generator wires it (design
   only here).** When #64 / aeroflow-workflows#10 implements the `queue` capability, a manifest
   requests messaging like this, and the schema rejects anything else:

   ```yaml
   capabilities: [http, queue]
   events:
     publishes: [baggage-events]            # own topic only
     subscribes:
       - topic: flight-events
         subscription: baggage-reclaim     # defaults to the workload name
   ```

   The generator (aeroflow-workflows, ADR-0009) then creates/attaches the
   topics and subscriptions and grants the workload's managed identity
   (ADR-0018) **Sender on its own topic only** and **Receiver only on its
   own subscriptions** — never Sender on a topic it does not own. Topic
   creation stays a platform act, as in the AppHost today. Naming and the
   ownership rule above are what the generator enforces; a manifest asking
   to publish to someone else's topic fails validation.

## Consequences

- Contract drift stops being silent once contract tests land: a producer
  change that breaks a copy fails that consumer's CI instead of its
  dead-letter queue. Until those tests exist (follow-up), the risk surveyed
  above stands — this record names it rather than fixing it by declaration.
- No new infrastructure, no package feed, nothing to deploy: zero cost,
  local-only, and any squad can delete its copy and still ship (the
  handbook's shared-code design test). The price is discipline: contract
  changes are multi-repo and ordered (consumers first for new event types),
  which is slow but visible in PRs.
- The `workload.yaml` shape gives #64 a concrete target and makes RBAC a
  generated default instead of per-service Bicep (ADR-0006/ADR-0009), but
  nothing enforces it until the schema and generator learn `events`.
- Trace context remains undecided-in-code: ADR-0013 asked for
  `traceparent` on every message and nothing sets it. Left as a follow-up;
  it does not block contracts, but the "one flight's story" is still
  followed by `CorrelationId` alone.

## Alternatives considered

**A shared contracts NuGet package (one `lib-events`, or per-owner
packages).** Rejected for now: the org has no package publishing, feed or
versioning habit to build on, and a package turns every contract tweak into
a release-and-bump across repos for what is today three topics and one
developer. It also sits badly with the handbook rule that a squad must be
able to delete shared code and still ship. Revisit when a contract change
has to be coordinated across more than three consumers, or when package
publishing exists for another reason (for example the third-copy extraction
ADR-0004 already anticipates for the outbox dispatcher, ADR-0017).

**A schema registry (Azure Schema Registry or similar), with JSON Schema
or Avro as the contract source.** Rejected: it is a hosted service with
cost and a local-development story to invent, solving discovery and
compatibility-checking problems this platform does not have at three
topics. Revisit if non-.NET producers or consumers join (the deferred
Kubernetes/Go rebuild would be such a trigger, where C# copies stop
working entirely), or if consumers outside this GitHub org appear.

**Contracts as schemas in platform-handbook, code-generated into each
service.** Rejected: it makes the handbook a build-time dependency of every
service and adds codegen before a single breaking change has ever happened.
The overview already catalogues the contracts in prose for readers.
Revisit if contract tests show the copies diverging repeatedly despite CI.

**Status quo: copies with no tests and no rules.** Rejected: the copies
have already drifted once (dashboard `GateEventMessage.FlightId`
nullability), and a new event type or renamed field would fail as
dead-letters at runtime, not as a red build. What this record keeps from
the status quo is the copies; what it adds is ownership, evolution rules
and tests. Revisit never.

**Add a `version` field to every envelope now.** Rejected: nothing would
read it, and the first real breaking change is better served by a new
event type or a `-v2` topic, which consumers can route on. Revisit when an
envelope-level break is actually planned.

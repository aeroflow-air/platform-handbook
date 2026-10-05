---
id: 13
title: Central event bus on Azure Service Bus topics
status: draft
date: 2026-10-05
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["infra-platform", "aeroflow-workflows", "svc-*", "template-dotnet-service"]
design-doc: null
---

## Context

Airport services (flight status, gate allocation, baggage reclaim, turnaround,
terminal and the rest) need to talk through events rather than direct HTTP
calls. Without a shared backbone, each pair invents its own coupling and the
story of one flight cannot be followed across services.

Issue [platform-handbook#52](https://github.com/aeroflow-air/platform-handbook/issues/52)
asks for a planned central bus: broker choice, a governed module so services
request it through `workload.yaml`'s existing `queue` capability (ADR-0009;
schema enum already includes `queue`), shared event contracts with versioning
and ownership, and trace context on every message. The C# publish/handle shape
and in-memory transport live in
[template-dotnet-service#15](https://github.com/aeroflow-air/template-dotnet-service/issues/15);
this record picks the real transport behind that shape.

Constraints that already bind us: governed Bicep modules only on the route to
live (ADR-0006), Container Apps with **Dapr not adopted now** (ADR-0007), no
Kubernetes, a squad of about six on one pay-as-you-go subscription where idle
cost matters, and Tony's rule that the **local path must add zero Azure cost**
(free emulator or container). Azure spend is a decision for Tony, quoted only
from published pricing.

## Decision

**The central event bus is Azure Service Bus topics (Standard tier to start).
Services request it through the `queue` capability. Local development uses the
official Service Bus emulator (or Aspire `RunAsEmulator`) at zero cloud cost.**

### Tony's decision (2026-10-05 ~13:07 Europe/London)

**Azure Service Bus spend is deferred.** For now:

- Use the **local Service Bus emulator only** (Aspire `RunAsEmulator` / MCR
  emulator container).
- **Do not create an Azure Service Bus namespace** until a later, explicit
  decision when we actually deploy.
- **Zero Azure messaging cost for now** — the cost table below remains as the
  published pricing reference for that future go/no-go; it is not authorization
  to provision.

The broker choice (Service Bus topics, Standard tier to start) stands. Only the
timing of Azure spend is deferred.

**Note on ADR-0009:** that accepted record still forward-references
"ADR-0013" for confidential approval. That wording predates this event-bus
record and now means **a future ADR**. Accepted ADR bodies may only change
status / superseded-by, so ADR-0009 is left unchanged.

### Broker and topology

- **One namespace** (platform-owned) hosting **topics** for integration events
  (`flight-events`, `gate-events`, … — exact names in the module catalogue).
  Subscriptions are per consuming service (or per handler group), with filters
  where useful.
- **Standard tier** for the showcase: topics, sessions (for ordered
  per-entity streams such as one flight), transactions, de-duplication and
  dead-lettering are available. Basic has no topics. Premium is deferred —
  dedicated messaging units are a steady cost we do not need at this scale.
- A governed `br/platform:*` module (name to be published with the catalogue,
  e.g. `service-bus-queue` or folded into a wider messaging module) provisions
  topic/subscription wiring and RBAC for the service's managed identity.
  Services add `queue` to `workload.yaml` capabilities; they do not author raw
  Service Bus Bicep (ADR-0006 / ADR-0008 / ADR-0009).

### Local path (zero Azure cost)

- Use the **Azure Service Bus emulator** container from MCR
  (`mcr.microsoft.com/azure-messaging/servicebus-emulator`), which Microsoft
  documents as free of cloud usage charges for local develop-and-test.
  See [emulator overview](https://learn.microsoft.com/en-us/azure/service-bus-messaging/overview-emulator).
- When the Aspire AppHost lands (ADR-0014), prefer
  `AddAzureServiceBus(...).RunAsEmulator()` so the same resource name wires
  local and Azure connection strings without hand-set secrets.
- Unit and single-service tests keep the **in-memory** publisher/handler from
  template-dotnet-service#15; the emulator is for multi-service and contract
  tests.

### Event contracts, ownership, versioning

- Events are **immutable records** at the edge (ADR-0004): id, occurred-at,
  correlation/trace id, and a typed payload. Examples named in #52 / #15:
  `FlightDelayed`, `GateChanged`, `BoardingStarted`, `BagUnloaded`.
- **Ownership:** the producing bounded context owns the contract. Flight
  lifecycle events are owned by `svc-flight-status` (or its successor); gate
  assignment events by `svc-gate-allocation`; and so on. Consumers depend on
  published contracts, not on producer internals.
- **Versioning:** additive, backward-compatible fields preferred. Breaking
  changes ship as a new event type or major schema version on a new
  subscription filter — never silently reshape an existing type. Contracts live
  in a small shared package (or per-owner packages) referenced by services; the
  exact package layout is an implementation detail for the first consumer PR.
- **Trace context:** every message carries W3C `traceparent` / `tracestate` (or
  the Azure SDK equivalent) so one flight's story spans services once OpenTelemetry
  is on (template issues #8 / #10 / #14). Correlation id remains available for
  non-OTel readers.

### Azure cost (published figures; spend deferred — see Tony's decision above)

Figures below are **UK South** retail prices from the
[Azure Retail Prices API](https://prices.azure.com/api/retail/prices) retrieved
2026-10-05, cross-checked against the public pricing pages. They are estimates,
not a quote. **Kept for the later deploy decision. Do not provision an Azure
namespace now — local emulator only until then.**

| Meter (Service Bus) | UK South retail | Source |
|---------------------|-----------------|--------|
| Standard base unit | **USD 0.013441 / hour** (also listed as **USD 10.00 / month**) | Retail API; [Service Bus pricing](https://azure.microsoft.com/en-gb/pricing/details/service-bus/) |
| Standard messaging operations | Tiered per million; API lists **USD 0.80**, **0.50**, **0.20** (and **0** for the included band) | Retail API; pricing page: first **13 million ops/month included** with Standard |
| Standard brokered connections | First **1,000 / month included**; then tiered (API lists **USD 0.03 / 0.025 / 0.015** per connection) | Retail API; pricing page FAQ |
| Premium messaging unit | **USD 0.9275 / hour** | Retail API — **not** recommended to start |
| Basic messaging operations | **USD 0.05 / million** | Retail API — Basic **cannot** host topics |

Operational note from Microsoft's FAQ: the Standard **base charge is once per
Azure subscription**, not per namespace
([Service Bus pricing FAQ](https://azure.microsoft.com/en-gb/pricing/details/service-bus/)).

Event Grid Basic comparison (same region, for the rejected alternative): retail
API lists **USD 0.06 per 100K operations** (≡ **USD 0.60 / million**); the
pricing page states **100,000 free operations / month**
([Event Grid pricing](https://azure.microsoft.com/en-us/pricing/details/event-grid/)).

## Consequences

Squads get ordered, dead-letterable pub/sub that fits Container Apps and the
`queue` capability without Kubernetes or Dapr. The local emulator keeps the
inner loop free. Traceable flight stories become possible once contracts and
OTel land.

Costs: **none in Azure for now** (emulator only per Tony's 2026-10-05
decision). When a later decision authorizes a namespace, expect a Standard base
charge whenever it exists in the subscription; platform ownership of the
namespace and module; subscription filter and DLQ operational practice. Emulator
gaps versus cloud (Microsoft: no production SLA; sequential test focus) mean
some behaviours will still need a cheap Azure smoke test before go-live.

What becomes harder: treating Event Grid system topics or MQTT as the primary
service-to-service bus without another ADR; enabling Dapr sidecars on Container
Apps without revisiting ADR-0007.

## Alternatives considered

**Azure Event Grid (custom topics / Basic tier).** Strong for Azure system
events and push-to-webhook fan-out; cheap at low volume (100K free ops/month,
then ~USD 0.60/million). Rejected as the **primary** service-to-service backbone:
weaker competing-consumer / session ordering story than Service Bus topics,
dead-lettering and retry semantics differ from what #52 asks for, and there is
**no official local emulator** comparable to Service Bus — so the zero-cost
local path is harder. Revisit for Azure resource events, partner topics, or as
a bridge *into* Service Bus.

**Dapr pub/sub over a broker (on Container Apps).** Rejected for now:
ADR-0007 explicitly leaves Dapr not adopted. It would add sidecars and another
abstraction before we have one working bus. Revisit if several runtimes need a
polyglot pub/sub API and Container Apps Dapr support is accepted in a later
record.

**Azure Event Hubs.** Rejected for this integration-event shape: streaming /
partition consumer groups, not service-style topics with per-subscriber DLQ
and sessions. Revisit for high-throughput telemetry pipelines.

**Storage Queues only.** Rejected: no topics / fan-out, weak for many
subscribers of the same airport event. Revisit for simple single-consumer
commands if a service needs a cheaper private queue alongside the bus.

**Premium Service Bus from day one.** Rejected: ~USD 0.93/hour per messaging
unit is steady cost for a showcase that is idle most of the time. Revisit if
Standard latency variance or message-size limits bite.

**HTTP-only choreography.** Rejected: #52's point is to stop direct coupling
and enable a followable flight story. Revisit never for the backbone; HTTP
remains fine for queries.

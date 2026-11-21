---
id: 22
title: Opinionated observability on the golden path
status: draft
date: 2026-11-21
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "template-dotnet-service", "aeroflow-local", "aeroflow-workflows", "infra-platform"]
design-doc: "docs/design/observability.md"
---

## Context

Observability is the part of a platform most teams bolt on after the first
outage. AeroFlow already has pieces of it, but they do not yet add up to a
golden path.

[ADR-0014](0014-aspire-local-development.md) puts OpenTelemetry, health
checks and resilience in `AeroFlow.Local.ServiceDefaults`, and the Aspire
dashboard is the local place for traces and metrics
([ADR-0016](0016-ops-dashboard-blazor-server.md)). The flight simulator
enables the Azure SDK activity source and starts a producer span around each
tick, so Service Bus `Diagnostic-Id` can flow. The real `svc-*` services and
`template-dotnet-service` do not reference ServiceDefaults. Each still carries
a commented OpenTelemetry stub, and template issues #8, #10 and #14 (tracing
and metrics, structured logs with trace correlation, liveness and readiness)
remain open. Publishers set `MessageId`, `Subject` and `CorrelationId` (the
flight id, [ADR-0017](0017-reliable-event-publishing.md)) but do not restore
or emit W3C trace context. [ADR-0013](0013-central-event-bus.md) already
requires `traceparent` / `tracestate` on every message so one flight can be
followed across services; that part has not landed.

On the infrastructure side, a service declares capabilities in `workload.yaml`
([ADR-0009](0009-workload-manifest.md)) and the generator turns them into
Bicep. There is no way to declare SLOs, and this record does not change the
schema or the generator. [ADR-0007](0007-container-apps-hosting.md) already
plans one Container Apps environment and a platform Log Analytics workspace
that services use as `existing`. Today's `container-app-service` stand-in
still creates a workspace (and an environment) per app. There is no Azure
deployment and no personal subscription; Azure Monitor is the target shape,
not something to provision now, in the same way ADR-0013 deferred Service Bus
spend.

Logging in the domain is already forbidden
([ADR-0004](0004-functional-style-csharp.md) and the
[coding standards](../standards/coding-standards.md)). Every service is
expected to document its failure modes
([service docs standard](../standards/service-docs.md)). What is missing is
a single set of opinions for signals, resource attributes, sampling, cost
and the Azure destination, applied by default rather than remembered in
every repo.

The design is in [docs/design/observability.md](../design/observability.md).

## Decision

**Observability is on by default on the golden path. Every service emits
OpenTelemetry traces, metrics and structured logs through a shared
ServiceDefaults package, W3C trace context travels with every Service Bus
message, and a small optional `observability` block in `workload.yaml` will
later turn SLOs into Azure Monitor alerts and workbooks. Squads do not wire
exporters.**

- **One package.** The existing `AeroFlow.Local.ServiceDefaults` is the
  starting point: OpenTelemetry traces, metrics and logs, OTLP when
  `OTEL_EXPORTER_OTLP_ENDPOINT` is set, `/health` and `/alive`, HTTP
  resilience and service discovery. It is promoted to a small, independently
  versioned library referenced by `template-dotnet-service`, every `svc-*`
  and aeroflow-local. That closes the open packaging question in ADR-0014
  and the template's #8, #10 and #14. A squad can delete the package and
  still ship (the CLAUDE.md design test), but it must still meet the signal
  and context-propagation contract below.
- **One flight, one trace.** Every published message carries W3C context in
  application properties (`Diagnostic-Id` and `traceparent`, plus
  `tracestate` when present). Consumers restore it. The Azure SDK activity
  source is enabled, as the simulator already does. An outbox
  (ADR-0017) stores the context with the event and restores it on send, so a
  delayed publish stays on the same trace. `CorrelationId` remains the
  flight id for non-OTel readers. This is how ADR-0013's trace-context rule
  is met.
- **Standard signals.** HTTP services emit RED (rate, errors, duration)
  using OpenTelemetry HTTP semantic conventions. Consumers expose queue
  depth, message age and dead-letter count. Required resource attributes
  are `service.name`, `service.version`, `deployment.environment` and
  squad/owner (`aeroflow.squad`). Flight id and flight number belong on
  traces and logs, not as metric dimensions.
- **SLOs in the manifest, later.** `workload.yaml` will gain an optional
  `observability.slos` block. The generator (both `generate.py` and
  `generate.cs`, golden-file parity, ADR-0021) will turn those SLOs into
  Azure Monitor alerts and a standard workbook via governed
  `br/platform:*` modules. Observability is not a capability: it is always
  on. This record only agrees the shape; it does not change the schema or
  the generator.
- **Local now, Azure later.** In aeroflow-local, the Aspire dashboard is
  the telemetry backend. In Azure, the destination is workspace-based
  Application Insights on the platform Log Analytics workspace ADR-0007
  already planned, with the connection string (or OTLP settings) injected
  by the platform. There is no Azure deploy yet.
- **Logs and health at the edges.** Structured logs use `ILogger` and
  `[LoggerMessage]` at controllers, workers and adapters only. Domain code
  stays silent (ADR-0004). No PII, secrets, tokens or connection strings in
  logs or attributes. `/alive` is liveness; `/health` is readiness,
  including configured dependencies, mapped in every environment so
  Container Apps probes work, and left anonymous (ADR-0018). Health
  requests stay out of traces, as ServiceDefaults already does.
- **Sampling and cost are platform defaults.** Locally, traces are not
  sampled. In Azure, the platform sets the sampler and any daily cap;
  services do not pick their own. Errors are always sampled.

What a squad must document, the schema proposal, the telemetry flow and the
follow-up implementation list live in the design doc.

## Consequences

A new service gets traces, metrics, structured logs, health endpoints and
Service Bus context propagation by referencing ServiceDefaults and calling
`AddServiceDefaults()`, the same way it already gets a `workload.yaml`. The
Aspire dashboard can show one flight from the simulator through gate
allocation and flight status to baggage reclaim as a single trace, once the
publishers and outbox restore context. The showcase story is "every service
is observable by default, and its SLOs live in its manifest."

What this costs: a shared package to version and roll out; both generators
and a new (or extended) infra-platform module when the SLO schema is
implemented; App Insights and Log Analytics charges once a subscription
exists, on top of the Container Apps costs ADR-0007 already named. The
package becomes a default dependency, which is the usual tension with the
"delete the library and still ship" test — the contract remains even if the
package does not.

What becomes harder: each squad inventing its own exporter, metric names or
sampling; logging inside domain functions; treating Grafana, a vendor APM or
a required sidecar collector as the primary path without another record.

This record does not supersede ADR-0007, ADR-0009, ADR-0013, ADR-0014 or
ADR-0016. It does not authorise Azure spend.

## Alternatives considered

**Let each squad wire OpenTelemetry and Application Insights themselves.**
Rejected: that is the bolted-on path this record exists to avoid, and it is
already what the commented stubs in every service produce — nothing. Revisit
only if a service has a runtime the shared package cannot instrument.

**Grafana, Prometheus or a vendor APM (Datadog, New Relic) as the primary
backend.** Rejected: local telemetry already has a home in the Aspire
dashboard (ADR-0014, ADR-0016), and Azure Monitor is the native destination
for Container Apps on a single subscription. A second product is cost and
drift at this scale. Revisit if a non-.NET estate appears that Aspire and
Azure Monitor serve poorly, or if Azure spend is later declined and a local
stack has to stand in for production too.

**Make observability a `workload.yaml` capability that a service can omit.**
Rejected: capabilities are requested infrastructure (ADR-0009). Observability
is a default, not a request. Revisit if a workload appears that must emit
nothing (for example a strictly offline job with no safe destination).

**An OpenTelemetry Collector sidecar on every container app from day one.**
Rejected: the SDK's OTLP exporter (local) and Azure Monitor exporter (Azure)
are enough for a squad of six, and ADR-0007 has not adopted extra sidecars.
Revisit if sampling, scrubbing or export needs a single platform choke point
that in-process configuration cannot provide.

**Per-service Log Analytics workspaces (as the current module stand-in
creates).** Rejected as the target Azure shape: ADR-0007 already plans one
environment and one workspace that services use as `existing`, and
cross-service traces need a shared workspace-based Application Insights
resource. Revisit if a later tenancy or isolation rule forbids sharing a
workspace.

**100% trace sampling in Azure with no cap, permanently.** Rejected as a
standing policy: it is fine while traffic is a demo, but cost control has to
be a platform default before the first real bill. Revisit only as a temporary
platform setting, never as a per-service choice.

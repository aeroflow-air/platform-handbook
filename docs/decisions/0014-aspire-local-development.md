---
id: 14
title: .NET Aspire for local platform development
status: draft
date: 2026-10-05
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "template-dotnet-service", "aeroflow-workflows"]
design-doc: null
---

## Context

Running the airport platform locally today means starting each service by hand
and inventing connection strings. Issue
[platform-handbook#54](https://github.com/aeroflow-air/platform-handbook/issues/54)
asks for one command that runs every service, the event bus, an identity
stand-in and the ops dashboard, wired together, with telemetry in a single
dashboard.

.NET Aspire (AppHost + ServiceDefaults) is the obvious candidate for a .NET 8
estate. It must not become the production host: deploy remains Azure Container
Apps via `workload.yaml` (ADR-0007, ADR-0009). The event bus choice in ADR-0013
(Service Bus topics + official emulator) and identity planning (#51) need a
local plug-in point. No dedicated local-dev repo exists yet.

## Decision

**.NET Aspire is the local inner-loop orchestrator only. Production hosting and
deploy stay on Container Apps through `workload.yaml`. AppHost + ServiceDefaults
compose services, the Service Bus emulator, and an identity stand-in under one
`dotnet run` / `aspire run`.**

### AppHost + ServiceDefaults

- **AppHost** references each service project (gate allocation, flight status,
  baggage reclaim, turnaround, cleaning, catering, pushback, terminal), the ops
  dashboard/API when it exists, and shared infrastructure resources. Service
  discovery and connection strings are injected by the AppHost — no hand-set
  local secrets for the happy path.
- **ServiceDefaults** (shared project) wires OpenTelemetry, health checks and
  resilience defaults, aligned with template-dotnet-service issues #8, #10 and
  #14 so the Aspire dashboard shows the same signals we expect in Azure.
- **One command** starts the composition (`dotnet run --project` on the
  AppHost, or `aspire run`). A seeded demo scenario (a flight moving through
  gate / boarding / bag events) is an AppHost concern, not something each
  service invents alone.
- Services remain independently runnable for unit tests and single-service
  work; Aspire is the whole-platform path, not a mandatory wrapper for every
  `dotnet test`.

### Event bus and identity locally

- **Event bus:** follow ADR-0013. AppHost adds
  `AddAzureServiceBus(...).RunAsEmulator()` (or an equivalent container
  resource pointing at the MCR emulator) and passes the reference into
  publishing and consuming services. Same resource name in local and Azure
  configuration shapes. In-memory transport from template#15 stays for tests.
- **Identity stand-in:** a local component that lets services exercise real
  authentication and authorisation without Entra cost in the inner loop
  (follows #51 — exact product choice is that issue's ADR, not this one).
  AppHost owns wiring; services consume the same abstraction they use in Azure
  (configuration and handlers), not a second auth stack.

### Deploy path stays workload.yaml → Container Apps

- Aspire does **not** deploy to production and does **not** replace Bicep
  modules or the shared deploy workflow.
- Shipping a service still means: container image, `workload.yaml` capabilities
  (`http`, `identity`, `queue`, …), governed `br/platform:*` modules, Container
  Apps environment (ADR-0006 / 0007 / 0009).
- Optional future use of Aspire's Azure provisioning helpers is **out of
  scope** until a separate ADR says otherwise. Local-first keeps the catalogue
  and OIDC deploy story honest.

### Where the AppHost lives

**Recommended default:** a new repository, e.g. `aeroflow-local`, holding the
AppHost, ServiceDefaults (if not already published from the template), demo
seed data and compose documentation. Service repos stay lean; the AppHost
depends on them as project or package references.

**Creating that repo needs Tony's explicit OK** (org repo creation, naming,
visibility). Until then, a short-lived AppHost may live in
`template-dotnet-service` or a spike branch — but the durable home should be a
dedicated local-dev repo so `svc-*` repos are not forced to know about every
sibling.

Alternatives for location (brief):

| Home | Pros | Cons |
|------|------|------|
| New `aeroflow-local` (recommended) | Clear local-vs-prod boundary; one place for seed/demo | Needs Tony's OK to create |
| Inside `template-dotnet-service` | Fast to start | Template becomes a platform orchestrator; confusing for scaffold consumers |
| Monorepo of all `svc-*` | Trivial project references | Contradicts current multi-repo layout; large migration |
| Per-service mini AppHosts only | Low coupling | No “whole platform” one-command story — fails #54 |

## Consequences

A squad of six can run the airport story on a laptop with zero Azure messaging
cost for the bus (emulator) and a clear line between local orchestration and
production Container Apps. Telemetry and health line up with the template's
defaults.

Costs: maintaining AppHost references as services are added; Docker resources
for the emulator (and SQL dependency the emulator needs); deciding package vs
project references across repos. Risk if Aspire Azure-deploy features creep in
and bypass governed modules — rejected here until another record.

Open until Tony decides: create `aeroflow-local` (or another name); whether
ServiceDefaults is copied, packaged, or submodule'd from the template; identity
stand-in product (#51).

## Alternatives considered

**Docker Compose only (no Aspire).** Rejected as the primary path: Compose can
run containers but does not give .NET service discovery, typed resource
references, or the Aspire dashboard that #54 wants alongside OTel. Revisit as a
thin supplement if non-.NET components appear that Aspire hosts poorly.

**Aspire as production host / ACA deploy from AppHost.** Rejected: production
path is already Container Apps + `workload.yaml` + governed modules. Using
Aspire to provision Azure would blur ADR-0006's catalogue and OIDC deploy
identities. Revisit only with an ADR that supersedes or narrows those records.

**No whole-platform local story.** Rejected: multi-service event flows
(ADR-0013) cannot be proven on one service's in-memory bus alone. Revisit never
while #52 / #54 remain goals.

**Tye or custom scripts.** Rejected: Tye is retired; bespoke scripts become a
second product. Revisit if Aspire abandons local container orchestration.

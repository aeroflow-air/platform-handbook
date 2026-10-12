---
id: 16
title: Ops dashboard on Blazor Server, hosted in aeroflow-local
status: draft
date: 2026-10-12
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["aeroflow-local", "svc-flight-status", "svc-gate-allocation", "svc-baggage-reclaim"]
design-doc: null
---

## Context

The live airport ops dashboard (#53) is the demo surface for AeroFlow. It
shows the simulated airport moving: a departures and arrivals board, gates,
baggage belts, the raw event stream and service health. Its data comes from
Service Bus topics (`flight-events`, `baggage-events` and the planned
`gate-events`, ADR-0013), plus an initial load from each service's API. It
has to update the browser live, run in the Aspire AppHost with the rest of
the stack (ADR-0014), cost nothing, and be maintainable by a .NET squad.
Today `AeroFlow.Local.OpsDashboard` in aeroflow-local is a placeholder
minimal API with only `/`, `/ping` and the ServiceDefaults health endpoints.
The open questions are which UI technology to use and where the code lives.

## Decision

**The ops dashboard is a Blazor Server app (.NET 8, interactive server
rendering) that lives in aeroflow-local as `src/AeroFlow.Local.OpsDashboard`
until there is a reason to deploy it.**

- **UI.** Razor components and plain CSS, with no npm, bundler or JavaScript
  build. Blazor Server's own SignalR circuit pushes updates to the browser, so
  there is no separate hub or JavaScript client.
- **Data.** Background Service Bus listeners (one `ops-dashboard`
  subscription per topic) and an initial load from the service APIs through
  Aspire service discovery feed an immutable in-memory view. Components
  re-render when it changes. The dashboard is read-only: it never writes to
  a service.
- **Platform fit.** It uses `AddServiceDefaults()` and
  `MapDefaultEndpoints()` like every other project, so health checks,
  OpenTelemetry and service discovery are the same. Sign-in through Keycloak
  (read-only role) is optional locally.
- **Hosting.** It stays in aeroflow-local because it only makes sense with
  the whole local stack running, and it changes alongside the AppHost
  wiring. If it is ever deployed, it moves to its own `svc-ops-dashboard`
  repo created from `template-dotnet-service`, with a `workload.yaml`
  (ADR-0009). That move would be a new record superseding this one.

## Consequences

- One language and one toolchain across the estate. Anyone who can work on a
  `svc-*` repo can work on the dashboard, and `dotnet build` is the whole build.
- Live updates and the AppHost integration come for free. It runs with the
  rest of the airport from `dotnet run` on the AppHost.
- Blazor Server holds a circuit, and some server memory, per open browser
  tab, and needs a live connection. That is fine for a local demo with a
  handful of viewers. It does not suit a public, high-traffic page.
- Living in aeroflow-local means no separate CI, release or `workload.yaml`
  for now, and no deployment path. Moving out later is a deliberate step.
- The dashboard is the first consumer of every topic, so it carries copies
  of each event contract until shared contracts are decided (#71).

## Alternatives considered

**ASP.NET Core API + SignalR hub + JavaScript or TypeScript frontend.**
Rejected because it adds a second language, a frontend build and a hand-written
push channel for a demo screen. Worth revisiting if a frontend specialist joins,
or if the dashboard needs a rich client-side UI that Blazor makes awkward.

**Blazor WebAssembly (or the .NET 8 Auto render mode).** Rejected because the
browser would still need an API and a push channel back to the server, which
gives the same moving parts as the SignalR option plus a large download.
Worth revisiting if the dashboard has to be served as static files or work
offline.

**Grafana (or the Aspire dashboard) over OpenTelemetry data.** Rejected as
the main surface because both are good at metrics and traces but poor at a
domain view such as a departures board or belts. The Aspire dashboard
remains the place for traces and metrics. Worth revisiting if the need
becomes purely operational metrics.

**A separate `svc-ops-dashboard` repo now.** Rejected because the dashboard
has no deployment target yet, and a separate repo would need its own
sibling-clone wiring for nothing. Worth revisiting when it is deployed, or
when a squad other than Platform owns it.

**Azure SignalR Service or Static Web Apps.** Rejected because of cost and
the cloud dependency for a local-first demo (ADR-0013 defers spend). Worth
revisiting when the dashboard is deployed and needs to scale out.

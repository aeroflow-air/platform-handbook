# AeroFlow airport: architecture and event flows

How the whole airport fits together today: which services exist, what they
listen to, what they publish, and where the gaps are. It describes the code on
`main` as of 2026-10-12 (aeroflow-local #7, svc-baggage-reclaim #2). Each
service's own detail lives in its `docs/service.md`
([standard](../standards/service-docs.md)).

## System context

AeroFlow runs locally as one .NET Aspire AppHost in
[`aeroflow-local`](https://github.com/aeroflow-air/aeroflow-local) (ADR-0014).
Nothing is deployed to Azure yet. The AppHost starts:

- the **Azure Service Bus emulator** (`messaging`), the event bus (ADR-0013);
- **Keycloak** (`identity`, port 8080), a free stand-in for Entra; services get
  the reference but none validates tokens yet;
- the **flight simulator**, which invents flights and publishes their lifecycle;
- three **real services** cloned as sibling repos, and placeholders for the rest;
- the **ops dashboard** placeholder (planned in #53).

Services never call each other. Each reacts to events on topics, and each topic
is owned by the one service that publishes to it (ADR-0013).

```mermaid
flowchart LR
  sim[flight-simulator<br/>aeroflow-local]
  subgraph bus[Service Bus emulator: messaging]
    fe[[topic: flight-events]]
    be[[topic: baggage-events]]
  end
  gate[svc-gate-allocation]
  fs[svc-flight-status]
  bag[svc-baggage-reclaim]
  ph[placeholders<br/>turnaround, cleaning,<br/>catering, pushback, terminal]
  dash[ops-dashboard<br/>placeholder, #53]
  kc[(Keycloak: identity)]

  sim -->|publishes| fe
  fe -->|gate-allocation| gate
  fe -->|flight-status| fs
  fe -->|baggage-reclaim| bag
  fe -->|one sub each| ph
  bag -->|publishes| be
  be -->|ops-dashboard| dash
  gate -.-> kc
  fs -.-> kc
  bag -.-> kc
```

## Services

| Service | Kind | Consumes | Publishes | HTTP API | Doc |
| --- | --- | --- | --- | --- | --- |
| flight-simulator | local tool (aeroflow-local) | none | `flight-events` | none | [aeroflow-local README](https://github.com/aeroflow-air/aeroflow-local) |
| [svc-gate-allocation](https://github.com/aeroflow-air/svc-gate-allocation) | real | `flight-events` / `gate-allocation` | none ([gap](#known-gaps)) | gates and allocations, Scalar | `docs/service.md` |
| [svc-flight-status](https://github.com/aeroflow-air/svc-flight-status) | real | `flight-events` / `flight-status` | none | flight lookup, departures board, manual events, Scalar | `docs/service.md` |
| [svc-baggage-reclaim](https://github.com/aeroflow-air/svc-baggage-reclaim) | real | `flight-events` / `baggage-reclaim` | `baggage-events` | `/health` only (API is #69) | `docs/service.md` |
| svc-turnaround, svc-cleaning, svc-catering, svc-pushback, svc-terminal | placeholder (aeroflow-local `src/placeholders`) | `flight-events` / own name | none | `/ping` | none; they log what they receive |
| ops-dashboard | placeholder (aeroflow-local) | `baggage-events` / `ops-dashboard` declared, not read yet | none | `/`, `/ping` | #53 |

All three real services keep state **in memory** and lose it on restart. Each
processes one message at a time (`MaxConcurrentCalls = 1`) with manual
completion.

## Topics and subscriptions

Declared in `aeroflow-local/src/AeroFlow.Local.AppHost/AppHost.cs`.

| Topic | Owner (publisher) | Subscription (Aspire resource) | Reader |
| --- | --- | --- | --- |
| `flight-events` | flight-simulator | `local-dev` | nobody; for poking at with tools |
| | | `gate-allocation` (`sub-svc-gate-allocation`) | svc-gate-allocation |
| | | `flight-status` (`sub-svc-flight-status`) | svc-flight-status |
| | | `baggage-reclaim` (`sub-svc-baggage-reclaim`) | svc-baggage-reclaim |
| | | `svc-turnaround`, `svc-cleaning`, `svc-catering`, `svc-pushback`, `svc-terminal` | the placeholders |
| `baggage-events` | svc-baggage-reclaim | `ops-dashboard` (`sub-baggage-ops-dashboard`) | nobody yet (#53), so its count grows |

Every subscription gets its own copy of every message; there are no filters, so
each service decides in code what to ignore.

### Message conventions

Both topics use the same envelope: JSON body (web casing, enums as strings),
`MessageId` = event id, `Subject` = event type, `CorrelationId` = flight id,
`ContentType` = `application/json`. The simulator also sets application
properties `eventType` and `flightNumber`.

**`flight-events` body** (`AeroFlow.Local.FlightEvents.FlightEvent`):
`eventId`, `flightId` (`SIM-00001`), `flightNumber` (two-character airline +
digits, e.g. `U23456`), `eventType` (`Scheduled`, `Delayed`, `Boarding`,
`Departed`, `Landed`, `Cancelled`), `origin`, `destination`,
`scheduledDeparture`, `occurredAt`, optional `delayMinutes`, `reason`.

**`baggage-events` body** (`AeroFlow.BaggageReclaim.Domain.BaggageEvent`):
`eventId`, `eventType` (`BeltAssigned`, `BagsOnBelt`, `BagDelayed`,
`LastBagOnBelt`, `ReclaimComplete`), `flightId`, `flightNumber`, `belt`,
`occurredAt`, and when relevant `bagCount`, `bagsCollected`, `bagsMissing`,
`bagTag`, `reason` (nulls omitted).

## Flight lifecycle

The simulator's home airport is **LHR**. Each tick (5 s by default, seed 42) it
advances every active flight one step and may schedule a new one (up to 8 in
flight). Half the flights depart LHR, half arrive there.

```mermaid
stateDiagram-v2
  [*] --> Scheduled
  Scheduled --> Delayed: 15%
  Scheduled --> Cancelled: 5%
  Scheduled --> Boarding
  Delayed --> Cancelled: 5%
  Delayed --> Boarding
  Boarding --> Departed
  Departed --> Landed
  Landed --> [*]
  Cancelled --> [*]
```

Who reacts to what:

| Event | svc-gate-allocation (departures from LHR) | svc-flight-status (all flights) | svc-baggage-reclaim (arrivals to LHR) |
| --- | --- | --- | --- |
| `Scheduled` | `AllocateGate`, 45 min before departure to departure, size C | adds the flight | ignored |
| `Delayed` | `RetimeTurn` | `DelayAnnounced` | `RecordDelay` if it has a belt |
| `Boarding` | ignored | assigns gate `TBA`, then `BoardingStarted` | ignored |
| `Departed` | `ReleaseGate` | `Departed` | ignored |
| `Landed` | ignored | `Landed` | `AssignBelt` and starts unloading |
| `Cancelled` | `ReleaseGate` | `Cancelled` | `CancelReclaim` if it has a belt |

```mermaid
sequenceDiagram
  participant Sim as flight-simulator
  participant FE as flight-events
  participant Gate as svc-gate-allocation
  participant FS as svc-flight-status
  Sim->>FE: Scheduled BA1234 LHR→AMS
  FE->>Gate: AllocateGate (planner picks smallest free gate)
  FE->>FS: add flight (arrival = departure + 90 min)
  opt delayed
    Sim->>FE: Delayed (delayMinutes, reason)
    FE->>Gate: RetimeTurn
    FE->>FS: DelayAnnounced
  end
  Sim->>FE: Boarding
  Note over Gate: ignored
  FE->>FS: gate TBA, BoardingStarted
  Sim->>FE: Departed
  FE->>Gate: ReleaseGate
  FE->>FS: Departed
  Sim->>FE: Landed
  FE->>FS: Landed
```

## Baggage event flow

```mermaid
sequenceDiagram
  participant Sim as flight-simulator
  participant FE as flight-events
  participant Bag as svc-baggage-reclaim
  participant BE as baggage-events
  participant Dash as ops-dashboard (#53)
  Sim->>FE: Landed U21234 AMS→LHR
  FE->>Bag: AssignBelt (least busy belt, 60-180 bags)
  Bag->>BE: BeltAssigned (eventId = the Landed event's id)
  Note over Bag: UnloadingWorker ticks every 2 s
  Bag->>BE: BagsOnBelt (after ~10 s)
  opt 1% of bags
    Bag->>BE: BagDelayed (bagTag, reason)
  end
  Bag->>BE: LastBagOnBelt
  Bag->>BE: ReclaimComplete (collected, missing)
  BE-->>Dash: ops-dashboard subscription (not read yet)
```

A 120-bag flight takes about 35 seconds from `Landed` to `ReclaimComplete` with
the default settings.

## Cross-cutting behaviour and failure modes

- **Delivery is at least once.** Only svc-baggage-reclaim is idempotent (it
  remembers the last 10,000 event ids). Gate allocation and flight status rely
  on domain rules to reject repeats (`already_allocated`, `invalid_transition`),
  which shows up as warnings, not duplicates.
- **Business rejections are completed, not retried.** They are logged as
  warnings such as `no_gate_available` once the six open demo gates are full,
  or `flight_not_found` for flights scheduled before a service started.
- **Unreadable messages are dead-lettered** with reason `unreadable`. Messages
  in a dead-letter queue almost always mean the contract copies have drifted
  (see #71).
- **Messaging is optional.** Each processor starts only when a `messaging`
  connection string exists, so `dotnet run`, containers and tests work without
  the bus.
- **Restart loses state** in every service, and the simulator restarts its
  sequence, so after restarting one service it sees events for flights it never
  saw scheduled.
- **Unread subscriptions grow**: `local-dev` and `ops-dashboard` have no reader.

## Known gaps

| Gap | Effect | Tracked |
| --- | --- | --- |
| Gate allocation publishes no gate events | flight status never learns the real gate | to raise |
| Placeholder gate `TBA` | flight status invents it at `Boarding` so the domain rule "boarding needs a gate" passes | follows the gate events gap |
| Event contracts are local copies in each service (`FlightEventMessage`) | a change to the simulator can silently break consumers (dead letters) | [#71](https://github.com/aeroflow-air/platform-handbook/issues/71) |
| `workload.yaml` cannot declare topics or subscriptions | the paved road cannot provision the bus; everything above exists only in the AppHost | [#64](https://github.com/aeroflow-air/platform-handbook/issues/64) |
| Gate allocation ignores arrivals; every turn is aircraft size C | no gates for inbound aircraft | |
| Baggage reclaim API | no way to query belts and bags yet | [#69](https://github.com/aeroflow-air/platform-handbook/issues/69) |
| Ops dashboard | nothing reads `baggage-events` | [#53](https://github.com/aeroflow-air/platform-handbook/issues/53) |
| State in memory only | everything resets on restart | |
| Keycloak not enforced | services get the reference but accept anonymous calls | |

## Decisions this rests on

- [ADR-0004 Functional-style C#](../decisions/0004-functional-style-csharp.md): pure domain, `Result` and `Option`.
- [ADR-0007 Container Apps hosting](../decisions/0007-container-apps-hosting.md)
- [ADR-0009 Workload manifest](../decisions/0009-workload-manifest.md) and the [design doc](../design/workload-manifest-platform.md)
- [ADR-0013 Central event bus](../decisions/0013-central-event-bus.md) (draft): one topic per owning service.
- [ADR-0014 .NET Aspire for local development](../decisions/0014-aspire-local-development.md) (draft)
- [ADR-0015 API documentation with OpenAPI and Scalar](../decisions/0015-api-documentation-openapi-scalar.md) (draft)
- [Service docs standard](../standards/service-docs.md)

Keep this page current: a PR that adds a topic, a subscription or a service
updates it.

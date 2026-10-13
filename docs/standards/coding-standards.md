# C# coding standards

A short checklist for service and library code. It turns
[ADR-0004: functional-style C#](../decisions/0004-functional-style-csharp.md) into concrete rules,
using `svc-gate-allocation`'s domain as the reference shape. Reviewers (human and AI) check PRs against it.
Each service's `CLAUDE.md` points here and adds what is specific to that repo.

## Domain (`src/<Project>/Domain`)

- [ ] **Pure static functions.** Domain logic lives in static classes of pure functions that take state
      and return new state, composed with `Bind` / `Map` / `Match`, like `GatePlanner.Apply(plan, command)`.
      No instance services with mutable fields in the domain.
- [ ] **Immutable data.** Domain types are `sealed record`s with init-only members and immutable
      collections (`ImmutableDictionary`, `ImmutableList`). No public setters, no `List<T>` fields, no in-place mutation.
      "Changing" something means returning a new value (`plan with { ... }`).
- [ ] **Closed sum types for states.** Model states as a closed set of records (like `GateStatus` = `Open` | `Closed(Reason)`),
      not magic strings, bools or enums with meaning hidden in conditionals.
- [ ] **Value types, not primitives.** Use types such as `GateId`, `FlightNumber` and `TimeWindow`, built only through
      `Parse` / `Create` returning `Result`. Do not pass raw `string` ids around the domain.
- [ ] **`Result<T>` for business failures.** Ordinary failures (not found, rule broken, bad input) return
      `Result<T>.Failure` with a **typed error record**, never an exception.
- [ ] **Typed errors with stable codes.** Errors derive from `ValidationError` / `NotFoundError` / `RuleViolation`
      (mapped to 400 / 404 / 409 at the HTTP edge). No magic error strings, no `bool` "it failed" returns.
- [ ] **`Option<T>`, not `null`.** Lookups return `Option<T>`; `ToResult` turns absence into a typed error.
      Nullable types appear only in HTTP request/response records and at serialisation boundaries.
- [ ] **No exceptions for control flow.** `throw` is only for genuine bugs (`UnreachableException` in exhaustive switches)
      or invalid startup data. Never `try/catch` to turn exceptions into outcomes.
- [ ] **No side effects.** No I/O, logging, `Console`, messaging, storage or `DateTimeOffset.UtcNow` in the domain.
      Time comes in as a value from `TimeProvider` at the edge.
- [ ] **No static mutable state.** No static caches or dictionaries. State lives in the store behind an interface
      (e.g. `IGatePlanStore`), updated atomically at the edge.
- [ ] **Reuse domain helpers.** Use the existing operations (`TimeWindow.Overlaps`, `plan.FindGate`, ...) instead of re-implementing them.
- [ ] **BCL only.** No LanguageExt or other FP library; each service keeps its own small `Result` / `Option`.

## Edges (controllers, messaging, storage)

- [ ] Side effects live here: controllers, Service Bus processors and publishers, stores.
- [ ] Map `Result` to HTTP with `Match` (problem details from the error code). Log with `ILogger` and
      `[LoggerMessage]` source-generated methods with named placeholders.
- [ ] Async all the way: no `.Result` / `.Wait()`; flow `CancellationToken`; dispose senders and clients.

## Events

- [ ] A service publishes only to **its own topic** (`gate-events`, `baggage-events`, ...); it only subscribes to others.
      See [ADR-0013](../decisions/0013-central-event-bus.md).
- [ ] Handlers are **idempotent**: redelivery of the same event must be safe (remember applied `EventId`s, or make the
      transition a no-op / rejected when it has already happened). Unknown, late or out-of-order events are ignored
      with a reason, not thrown.
- [ ] Outgoing messages set `MessageId` = event id, `Subject` = event type, `CorrelationId` = flight id.
- [ ] Event contract changes are additive; a breaking change needs a new event type or version.

## Tests and docs

- [ ] New domain functions and handlers have unit tests, including failure and duplicate paths. Pure domain code is tested without mocks.
- [ ] `docs/service.md` stays current when inputs, outputs, settings or failure modes change
      (see the [service docs standard](service-docs.md), added by handbook PR #80).

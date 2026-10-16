---
id: 17
title: Reliable event publishing with a store outbox and deterministic event ids
status: draft
date: 2026-10-16
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-gate-allocation", "svc-baggage-reclaim", "aeroflow-local"]
design-doc: null
---

## Context

Gate allocation and baggage reclaim published **at most once** (#84). Each one
updated its in-memory store first and sent the event afterwards. If the send
failed, the change stayed but the event was gone:

- In gate allocation, the redelivered flight event was rejected as a repeat
  (`already_allocated`), so nothing was re-sent.
- In baggage reclaim, a redelivered `Landed` was ignored as already applied, so
  `BeltAssigned` was never re-sent. Unloading ticks had no inbound message at
  all. The hall moved on and that tick's events were lost.
- Most event ids came from `Guid.NewGuid`, so even a re-send would look like a
  new event to consumers.

The obvious quick fix is "publish before completing the inbound message", so a
failure causes redelivery. That doesn't work here. The store has already changed,
so the redelivery is a repeat and produces nothing. It also doesn't help tick
events, which have no inbound message.

The services have no database yet (#4, #6). State is one immutable snapshot,
swapped atomically with compare-and-swap. Whatever we choose has to fit that
today, and still be right when a durable store arrives.

## Decision

Every service that publishes events does three things.

1. **Outbox in the store.** Outgoing events are saved in the **same atomic store
   update** as the state change that produced them (`IGatePlanStore.Update(transition, emit)`,
   `IReclaimHallStore.UpdateWithEvents`). Handlers and timers never call the
   publisher. An `OutboxDispatcher` hosted service sends the outbox oldest
   first and removes each event once it's sent. A failed send leaves that event
   and every later one in place, so order is kept. The dispatcher retries every
   `Outbox:RetrySeconds` (5 s by default), and is woken straight away after each
   change. The inbound message is completed once the change and its events are
   stored, because they can no longer be lost.
2. **Deterministic event ids.** The id is a name-based UUID (RFC 9562 v5) of what
   caused the event. That is the triggering event's id plus the outgoing event
   type (`EventIds.Derive`). For events with no trigger, such as baggage ticks, it is a fixed
   namespace plus a stable name (flight, landing time, type, bag tag). The id
   is the Service Bus `MessageId`, and `CorrelationId` is always the flight id.
   A derived id never equals its source id, so `BeltAssigned` can't collide with
   `Landed` in a consumer's seen-ids set.
3. **De-duplication at both ends.** Delivery is now **at least once**: a send
   that reached the bus but reported failure is sent again with the same id.
   Topics have Service Bus **duplicate detection** turned on (10-minute window,
   set in the aeroflow-local AppHost for the emulator). Consumers still
   de-duplicate by `EventId`, because duplicate detection only covers its window
   and not every tier has it. The ops dashboard already does this.

## Consequences

- No event is lost on a failed publish, and repeats are harmless. Consumers have
  to be idempotent by `EventId`. That was already the rule in each `CLAUDE.md`,
  and it now holds for every publisher.
- Events can arrive a few seconds late while the bus is down. The service keeps
  working, and the outbox grows until the bus is back. The warning
  `Publishing ... events failed; N pending in the outbox` shows how far behind
  it is.
- With in-memory state, a restart loses the outbox along with the state it
  describes. That is consistent: nothing is half-applied. **When a durable store
  lands, the outbox must be a table or collection written in the same
  transaction as the state.** It must not be a separate in-memory queue. The
  interfaces already have that shape.
- The dispatcher is under 100 lines, and each service has its own copy. Per
  ADR-0004, it moves to a shared `lib-` package the next time it would be
  copied a third time.
- In Azure, duplicate detection needs the Standard tier or higher. On Basic,
  consumer de-duplication alone is enough.
- The flight simulator in aeroflow-local follows the same rule in a simple way.
  It keeps the events the bus didn't accept and retries them on the next tick,
  with the same ids.

## Alternatives considered

**Deterministic ids and re-publish on redelivery, without an outbox.** When a
repeat is detected, rebuild the events the original change would have produced
and send them again. This was rejected because the handler would need to work
out the past from the current state, which is fragile once later changes have
happened. It also does nothing for timer-driven tick events. Worth revisiting
only if a service's state can't hold an outbox.

**Publish before saving the state.** This was rejected because a crash or a
rejected update after the send leaves consumers with an event for a change that
never happened. That is worse than a lost event.

**Duplicate detection on its own.** This was rejected because it only drops
copies. It can't bring back an event that was never sent, and it doesn't work
with random ids.

**A shared outbox library now.** This was rejected because there are only two
users so far. The ADR-0004 rule is to extract on the third copy, not the first.

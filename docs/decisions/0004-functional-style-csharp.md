---
id: 4
title: Functional-style C# for service code
status: accepted
date: 2026-09-22
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["template-dotnet-service", "svc-*", "lib-*"]
design-doc: null
---

## Context

AeroFlow's golden-path services are .NET. Classic mutable OOP remains the
default habit in much of that estate: shared mutable state, void methods that
mutate arguments, deep class hierarchies, and null as the everyday absence
signal. Those habits compile fine and still produce a steady class of bugs —
racey state, surprising side effects, and null-reference failures — that a
squad of six pays for in review time and production noise.

C# already has the tools for a more functional style without changing language:
`record` / `record struct`, init-only and `required` members, pattern matching,
expression-bodied members, `Result`-shaped returns (or a small shared helper),
and LINQ for transformation pipelines. The question is whether AeroFlow makes
that style an organisational default for new service and library code, or leaves
it to individual taste.

## Decision

New **C# service and shared-library code** prefers a **functional style**:

- Prefer **immutable data** (`record`, init-only properties) over mutable
  objects for domain and DTO shapes.
- Prefer **pure functions** and small transformation pipelines over methods
  that mutate shared state. Side effects (I/O, messaging, persistence) stay at
  the edges — controllers, workers, adapters — not threaded through the domain.
- Prefer **explicit outcomes** (result / option / discriminated union patterns,
  or clear nullable annotations with analysis) over throwing for ordinary
  business failure paths.
- Prefer **composition** of small functions and types over deep inheritance.

**No mandated functional library.** The house default is the BCL and idiomatic
C#. Do not put LanguageExt, or any similar FP framework, in the golden-path
template or as a required dependency for services. Thin shared helpers in a
`lib-*` are allowed only after **proven duplication** (the same Result/Option
shape reinvented in two or three services) and must still pass the design test:
a squad can delete the library and still ship.

This is **idiomatic functional-leaning C#**, not a mandate to rewrite the stack
in F#. The golden-path template and library guidance should demonstrate the
style; existing code is not mass-rewritten.

## Consequences

Domain logic becomes easier to reason about and to test without mocks for every
mutation. Null and error paths show up in types and signatures rather than as
surprises at runtime. Reviewers get a shared vocabulary ("keep this pure",
"lift the side effect") instead of arguing taste every PR.

What this costs: a learning curve for engineers steeped in mutable OOP, and
some local ceremony when a service needs a small Result type before any shared
`lib-*` exists. Hot paths that need mutable buffers or interop with mutable BCL
APIs remain allowed — the rule is default preference, not purity theatre.

What becomes harder: copy-pasting anemic mutable services from older samples,
and quietly growing a de-facto framework by slipping LanguageExt into the
template. The template must stay the exemplar, or the decision evaporates.

## Alternatives considered

**Mutable OOP as the house style.** Rejected. It is the path of least resistance
in samples and muscle memory, and it is exactly the habit producing the error
classes we want fewer of. Revisit only if a measured attempt at functional-style
C# clearly slows delivery for a squad of six without reducing defects.

**F# as the primary service language.** Rejected for now. Strong fit for
functional style, but it splits the estate, the hiring pool, and the template
surface for a portfolio meant to stay legible to typical .NET platform
readers. Revisit if AeroFlow grows a real F#-fluent cohort and a second golden
path is cheaper than stretching C# idioms.

**Mandate LanguageExt (or similar) for all services.** Rejected. Useful library;
too much framework gravity for a design test that says a squad must be able to
delete a shared library and still ship. Prefer BCL + thin local helpers first;
promote a small `lib-*` only after proven duplication. Revisit if that thin lib
itself grows real FP machinery and pinning one established package is clearly
cheaper than maintaining ours.

**No style ADR — leave it to PR taste.** Rejected. Without a recorded default,
the golden path cannot teach a consistent shape and reviews re-litigate the
same points. Revisit if services stay tiny throwaways where style variance
costs nothing.

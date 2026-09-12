---
id: 0002
title: Infrastructure as code — Bicep with typed module contracts
status: accepted
date: 2026-09-12
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos"]
design-doc: null
---

## Context

AeroFlow runs entirely on Azure and has no multi-cloud ambition. The platform's
job is to give squads a small, opinionated interface to infrastructure: a squad
should describe the workload it wants, not the forty resource properties that
sit underneath it.

An earlier working assumption — recorded informally, before this decision flow
existed — was Pulumi with C#, chosen for type safety, unit-testable
infrastructure, and the expectation that C# developers would find it easier to
author. That assumption was not tested against how squads actually interact
with infrastructure on a golden path, and it is revisited here.

Two things reduce the weight of the original reasoning. Squads on a golden path
mostly *consume* modules rather than author them, so the authoring language
matters far less than the consumption interface. And Pulumi's state file is an
operational asset that must be stored, protected, unlocked after a failed run,
and reconciled against out-of-band changes — a cost paid continuously, by a
platform team of one.

## Decision

Infrastructure is authored in **Bicep**.

Platform modules are published to Azure Container Registry as versioned OCI
artifacts (`br:<registry>/platform/<module>:<semver>`) and consumed by pinned
version, consistent with the release model of consuming versioned artefacts
rather than another repository's `main`.

Module inputs are **user-defined types**, exported from a separately versioned
`types` module and imported by consumers, so the interface between platform and
squad is a compile-time contract rather than a documented convention.

Platform modules are thin: they accept the narrow typed input, apply AeroFlow's
opinions (naming, tags, managed identity, diagnostic settings), and delegate to
**Azure Verified Modules** for the resource itself.

Templates are validated in CI by **PSRule for Azure** against a pinned baseline,
alongside custom rules encoding AeroFlow's own conventions. Deployments use
**deployment stacks** so resource lifecycle, including removal, is managed
without a state file.

## Consequences

The contract between platform and squad becomes enforceable: a squad passing a
malformed workload definition fails at compile time with IntelliSense, not at
deploy time with an ARM error.

Resource-level maintenance is inherited from Microsoft rather than owned. The
platform layer stays small enough to read.

What is given up is unit-testable infrastructure. Bicep offers linting,
`what-if`, and policy assertion via PSRule, which is not the same as testing
logic in isolation. We accept this because the platform layer deliberately
contains little logic to test; if it grows enough logic to need tests, that is
a signal the layer is doing too much.

Pinning a PSRule baseline means new rules do not appear in CI unannounced.
Baseline upgrades become a deliberate, reviewable act.

The design test still applies: a squad must be able to delete the platform
module and call the AVM module directly. They lose AeroFlow's opinions, not
the ability to ship. If that ever becomes false, the platform layer has become
a framework and should be cut back.

## Alternatives considered

**Pulumi with C#.** Rejected. The type safety it offers is now available in
Bicep through user-defined types, and its distinguishing advantage — real unit
testing of infrastructure code — addresses a problem this estate does not have,
while introducing state management as a permanent operational cost. Revisit if
AeroFlow becomes multi-cloud, or if the platform layer acquires enough
conditional logic that policy assertion is genuinely insufficient.

**Terraform.** Rejected. Strong module ecosystem and the same state cost as
Pulumi, with no compensating advantage on an Azure-only estate.

**Raw ARM templates.** Rejected. No authoring ergonomics, no type system, and
no reason to choose it now that Bicep compiles to the same thing.

**AVM consumed directly by squads, with no platform layer.** Rejected: the
opinions are the product. Without a platform module, every squad rediscovers
tagging, diagnostics and identity wiring independently. Revisit if the platform
modules turn out to be pass-throughs that add nothing but indirection.

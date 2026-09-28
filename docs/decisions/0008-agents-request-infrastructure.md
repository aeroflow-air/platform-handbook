---
id: 8
title: Agents author application code and request infrastructure through a manifest
status: draft
date: 2026-09-28
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "template-*", "aeroflow-workflows", "infra-platform"]
design-doc: null
---

## Context

An **agent** here is an AI code-generation tool that authors commits or pull
requests. Agents write application code readily, and will as readily invent
infrastructure nobody asked for: a resource, an identity, a network path.

ADR-0006 limits the route to live to governed `br/platform:*` modules, checked
by the shared deploy workflow's gate, but lets a squad compose any catalogue
module by hand. For agents that is the wrong grain: what needs review is which
capabilities a service needs, not which Bicep an agent wrote.

None of the enforcement exists yet: no `workload.yaml` in any repo, no gate in
`aeroflow-workflows` (only `dotnet-ci.yml`, `validate-decisions.yml` and a
self-test), no `infra-platform` repo and no `.bicep` anywhere in the org.

## Decision

**Agents may author application code. They may only request infrastructure
through a workload manifest. Raw resource definitions in `svc-*` and
`template-*` repos fail CI.**

- **Application code.** An agent may write the C#, held to the same rules as
  any other code (ADR-0004, ADR-0005).
- **Infrastructure by request.** An agent may propose changes to a service's
  `workload.yaml`: its workload name, repo, data class, capabilities and module
  pins. It may add infrastructure only by changing capabilities that already
  have modules. It does not write Bicep.
- **New capabilities.** A capability without a module needs a module and an ADR
  first. An agent cannot create one by editing a manifest.
- **Raw resources fail CI, for every author.** CI cannot reliably tell an
  agent's commit from a human's, so the check is actor-agnostic, as ADR-0006
  already implies on the route to live. The agent-specific parts are the rule
  above, provenance on agent commits and human review of capability changes.
- **Narrows ADR-0006; does not supersede it.** Squads keep what ADR-0006 gives
  them; this adds a stricter rule for agents.

Later records fill in the parts this one depends on. None exists yet:

- ADR-0009: the `workload.yaml` schema, with a capability enum starting at
  `http`, `identity`, `store` and `queue`, and who turns a manifest into a
  composition of `br/platform:*` modules.
- ADR-0010: plan identity separate from apply identity; apply only in Actions.
- ADR-0011: provenance on agent commits.
- ADR-0012: governance at the deploy and merge gate, not at repo creation.
- ADR-0013: human Platform approval when the capability diff touches identity,
  network or data class.

Enforcement will live in three places: the manifest in each `svc-*` repo, a
reusable check in `aeroflow-workflows` called from each service's CI next to
`dotnet-ci.yml`, and the modules in `infra-platform`, which is planned.

## Consequences

Review gets smaller: an agent's infrastructure change is a capability diff in
one file, not a Bicep diff, bounded by the catalogue ADR-0006 governs.

The cost is slower one-off Azure features: a service needing something no
capability covers waits for a module and an ADR, even for one line of Bicep.
Worth it.

The ban on raw resources is mechanical; the rest is not. Nothing in CI stops an
agent composing `br/platform:*` modules in Bicep by hand, because that is legal
for a human under ADR-0006. Until ADR-0009 settles how Bicep comes from the
manifest, the agent rule rests on provenance (ADR-0011) and review (ADR-0013).

Open, not decided here:

- **Manifest to modules.** The shared workflow could generate the composition
  from `workload.yaml`, or a human could hand-write Bicep that is checked
  against it. Deferred to ADR-0009.
- **Sandboxes.** ADR-0006 allows raw resources and AVM there. Whether agents may
  work in a sandbox is not decided.
- **What counts as a raw resource definition** outside Bicep (ARM JSON, scripts
  calling the Azure CLI) is for the gate's design, not this record.
- **Who writes a new module** when an agent-built service needs one.

Revisit if capability changes often need what the manifest can't express, if
the new-capability queue costs more than it prevents, or provenance fails.

## Alternatives considered

- **Agents compose `br/platform:*` modules directly, as squads may.** Rejected:
  reviewers then read Bicep, and an agent can wire in any catalogue module.
  Revisit if the manifest proves too coarse for real services.
- **No restriction beyond ADR-0006.** Rejected: ADR-0006 governs how
  infrastructure is built, not whether a service should have it. Revisit if
  agent-authored infrastructure changes turn out rare and well reviewed.
- **No agents on service repos.** Rejected: it gives up the experiment itself.
  Revisit if agent code costs more in review and defects than it saves.

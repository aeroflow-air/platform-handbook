---
id: 6
title: Infrastructure as code — squads self-serve through governed Bicep modules only
status: accepted
date: 2026-09-27
deciders: ["@aeroflow-air/platform"]
supersedes: 2
superseded-by: null
affects: ["infra-platform", "aeroflow-workflows", "svc-*", "template-dotnet-service"]
design-doc: null
---

## Context

Intended to supersede ADR-0002, which stands until the link is set on acceptance
(see `docs/decisions/README.md`). Its choices hold: Bicep, thin modules over
Azure Verified Modules (AVM), typed contracts, no state file for a team of one.
Its design test, "a squad must be able to delete the platform module and call
the AVM module directly", does not: it invites each squad to write its own key
vault module with its own naming, tags, identity and diagnostics. No `.bicep`
files exist yet, so reversing it costs a record, not a migration.

## Decision

Infrastructure is authored in **Bicep**. **Squads write and deploy their own
infrastructure, on the route to live from governed platform modules only.**

- **Governed only.** A service's `infra/` uses only `br/platform:*` modules from
  `infra-platform`, not `br/public` AVM, other registries, template specs or
  relative paths, and no `resource` except `existing`, which deploys nothing.
- **Sandbox.** Each squad has a platform-owned sandbox subscription where raw
  resources and AVM are allowed: no production data, a budget cap, automatic
  cleanup on expiry. A proven idea leaves as a module PR to `infra-platform`.
- **Service-shaped modules first**, built before squads need them (e.g.
  `container-app-service`: app, identity, diagnostics, ingress in one call),
  over per-resource-type building blocks for rarer needs. All are thin: typed
  input from a versioned `br/platform:types`, AeroFlow's naming, tags, identity
  and diagnostics, pinned AVM, and a small **sealed** `advanced` parameter as
  the pressure valve. `template-dotnet-service` ships `infra/` wired: a new
  service deploys on its first PR with no Bicep.
- **One catalogue page** lists each module with a copy-paste example and its
  `advanced` keys; gate failures link to the entry.
- **Versioning.** Exact pins (`br/platform:key-vault:1.4.0`), never overwritten;
  semver, with major for a broken caller or replaced resource; a changelog per
  module. Upgrades reach squads as automated PRs from self-hosted Renovate (a
  GitHub Action) with a custom rule in an org preset; squads merge them, with
  what-if, when it suits them; old majors stay while pinned. The rule is proven
  against a public OCI registry; private ACR sign-in via OIDC is still to be
  confirmed ([how upgrades reach squads](../infrastructure/module-upgrades.md)).
- **Missing capability: contribute first.** The squad writes the module in
  `infra-platform` from a scaffold generating naming, tags, identity,
  diagnostics, the `aeroflow-module` tag and a test. Platform reviews to a short
  published checklist in about two working days, then owns it. Raising an issue
  is possible, not the main route.
- **Enforcement, in three layers.**
  1. **Gate.** Fails any non-`existing` `resource`, or module or import source
     outside `br/platform` (alias resolved by the gate, not the squad's config).
     Runs locally and on every PR touching `infra/` beside PSRule and what-if;
     the run in the reusable `aeroflow-workflows` deploy workflow enforces.
     Bicep has no registry allow-list; PSRule sees resources, not sources.
  2. **Only that workflow deploys.** Each squad's deploy identity writes only to
     its resource groups (members hold Reader), trusted via GitHub OIDC with
     `job_workflow_ref` in the subject. **To confirm with a real token:**
     standard federated credentials match exactly, so each workflow release
     needs new ones per repo and environment (20 per identity); flexible ones
     can wildcard it but are preview, set up in the portal, Microsoft Graph
     (apps) or ARM REST (managed identities), not Azure CLI, PowerShell or
     Terraform, and must also match `sub` and `repository_id` or
     `repository_owner_id`. Else: repo-and-environment scope.
  3. **Policy backstop.** Modules stamp an `aeroflow-module` tag (name,
     version). Azure Policy audits squad resource groups for untagged resources,
     portal-made ones included, and moves to deny once quiet.
- **Validation, lifecycle, scope.** PSRule for Azure on a pinned baseline; a
  deployment stack per service and environment. Shared resources, sandboxes,
  identities and policy are platform-owned. Hosting gets its own record.

## Consequences

Squads ship what the catalogue covers without waiting, opinions built in; errors
surface at compile time or on the PR, not at deploy.

The catalogue is the bottleneck: no module, no route to live, no exemption.
Platform review becomes the queue, so two days is a promise to keep, and modules
are built before anyone asks. Sandboxes cost subscriptions and cleanup.

The gate is our own code: a source check, not a parser, wrong both ways, needing
tests and releases. Nothing stops portal Owner rights and anyone with write
access can copy a tag, so layer 3 catches drift, not a determined bypass. In a
one-person organisation required CODEOWNERS review cannot be met, so CI and the
gate enforce until a second maintainer exists. We give up unit tests.
Renovate is ours to run: a workflow, a token, and an alias map kept in step
with `bicepconfig.json` by hand. Its PRs carry no release notes.

We track time to first deploy for a new service, time from missing-module
request to published version, and how often `advanced` keys are requested.
Revisit if new services need hand-written Bicep, if module requests routinely
wait over a sprint, if `advanced` requests keep rising (modules too tight), if
gate false positives cost more than the drift, if the OIDC binding fails, or if
modules are mere pass-throughs.

## Alternatives considered

- **ADR-0002's escape hatch, or AVM with no platform layer.** Rejected: the
  opinions are the product. Revisit if squads are blocked more than served.
- **Per-resource-type modules only.** Rejected: every squad re-wires a service.
  Revisit if service-shaped modules grow `advanced` keys faster than callers.
- **Convention only.** Rejected: an unchecked rule is a claim, and a team of one
  has no reviewer. Revisit if gate upkeep exceeds the drift caught.
- **Azure Policy as the primary control.** Rejected: fails after merge and sees
  resources, not provenance. Revisit if the gate proves unmaintainable.
- **Pulumi with C#.** Rejected: user-defined types give the type safety; state
  is a permanent cost. Revisit if multi-cloud, or logic outgrows PSRule.
- **Terraform.** Rejected: the same state cost. Revisit if multi-cloud.
- **Raw ARM.** Rejected: no ergonomics or types. Revisit if Bicep stalls.

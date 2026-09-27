---
id: 6
title: Infrastructure as code — squads self-serve through governed Bicep modules only
status: draft
date: 2026-09-27
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["infra-platform", "aeroflow-workflows", "svc-*", "template-dotnet-service"]
design-doc: null
---

## Context

This record is intended to supersede ADR-0002. The supersession link is set
when it is accepted (see `docs/decisions/README.md`); until then ADR-0002
stands.

AeroFlow runs entirely on Azure and has no multi-cloud ambition. ADR-0002 chose
Bicep, thin platform modules over Azure Verified Modules (AVM), typed contracts
and a state-free lifecycle, and rejected Pulumi and Terraform largely because a
state file is an operational asset paid for continuously by a platform team of
one. That reasoning still holds and is carried forward here.

What changes is the design test. ADR-0002 said "a squad must be able to delete
the platform module and call the AVM module directly". The failure that test
invites is the one this platform exists to prevent: every squad that finds the
platform module inconvenient writes its own key vault module, with its own
naming, tagging, identity and diagnostics, and the estate drifts one
reasonable-looking exception at a time. Squads should self-serve their
infrastructure, but through governed modules, not around them.

Nothing has been built yet — there are no `.bicep` files in the organisation —
so reversing the test now costs a record, not a migration.

## Decision

Infrastructure is authored in **Bicep**. **Squads write and deploy their own
workload infrastructure, composed only from governed platform modules.**

- **Squads own `infra/` in their service repository** and deploy it
  themselves. Workload code may reference modules only from the platform
  registry (`br/platform:*`). No `resource` declarations, and no modules from
  any other source — not `br/public` AVM, not another registry, not template
  specs, not relative-path local modules.
- **One governed module per resource type**, owned by the platform in
  `infra-platform`. Modules are thin: they accept a narrow typed input, apply
  AeroFlow's opinions (naming, tags, managed identity, diagnostic settings), and
  delegate to AVM, pinned to an exact version, for the resource itself. Each may
  expose a small **sealed** `advanced` parameter listing settings deliberately
  left to squads. That is the pressure valve; there is no other.
- **Typed contracts.** Module inputs are user-defined types exported from a
  separately versioned `types` module (`br/platform:types:<semver>`), so the
  interface between platform and squad is a compile-time contract rather than a
  documented convention.
- **Distribution and versioning.** Modules are published to Azure Container
  Registry as OCI artifacts and consumed by exact pinned version
  (`br/platform:key-vault:1.4.0`); no floating tags. A published version is
  never overwritten. Patch: no contract change. Minor: additive — a new optional
  parameter, a new `advanced` key, a widened allowed value. Major: anything that
  breaks an existing caller or replaces a resource — a new required parameter, a
  removed or renamed parameter or output, a narrowed allowed value. Squads
  upgrade in their own PR, at their own pace, with what-if showing the diff. A
  previous major stays published until no service pins it. Each module keeps a
  changelog.
- **Missing capability.** A squad opens an issue or a PR against
  `infra-platform`: a new module, a new `advanced` key, or a new allowed value.
  No RFC, no reviewer pool. The platform owns the module once merged.
- **Enforcement, in three layers.**
  1. **Deploy gate.** The reusable deploy workflow in `aeroflow-workflows` runs
     a source check over `infra/` before anything else and fails on a
     `resource` declaration or any module or import source other than the
     platform registry, naming the governed module to use from a catalogue
     index published by `infra-platform`. It resolves `br/platform` against its
     own configuration, not the squad's `bicepconfig.json`. Bicep has no
     built-in registry allow-list and PSRule sees expanded resources, not module
     sources, so this check is our own code.
  2. **Only the governed workflow can deploy.** Each squad has a deploy identity
     whose rights are limited to that squad's resource groups, trusted through
     GitHub OIDC federated credentials. The organisation customises the OIDC
     subject to include `job_workflow_ref`, so tokens are accepted only from
     jobs running the deploy workflow. Squad members hold Reader on their
     resource groups; write access belongs to the deploy identity. **To be
     confirmed during implementation:** standard Entra federated credentials
     match the subject exactly, and a subject containing `job_workflow_ref`
     embeds the workflow's ref (for example `@refs/tags/v1.2.0`), so each
     workflow release needs new credentials per repository and environment,
     against a limit of 20 per identity. Flexible federated identity credentials
     can match `job_workflow_ref` with a wildcard, but are in preview, must
     also match `sub` and `repository_id` or `repository_owner_id`, and are
     configurable only through the REST APIs, not Azure CLI, PowerShell or
     Terraform. Which option we use is settled with a real token and recorded
     in `infra-platform`.
  3. **Azure Policy backstop.** Governed modules stamp an `aeroflow-module` tag
     carrying module name and version, set by the publish pipeline. A policy on
     squad resource groups audits resources without it — which also catches
     anything created in the portal — and moves to deny once the audit is quiet.
- **Validation and deployment.** Templates are validated in CI by **PSRule for
  Azure** against a pinned baseline, alongside custom rules encoding AeroFlow's
  own conventions, in `infra-platform` for modules and in the deploy workflow
  for squad compositions. Every pull request that changes a service's `infra/`
  runs what-if. Deployments use **deployment stacks**, one per service and
  environment, so resource lifecycle, including removal, is managed without a
  state file.
- **Scope.** Shared platform resources — the hosting environment, Log
  Analytics, the container registry, squad resource groups, deploy identities,
  federated credentials and policy assignments — are platform-owned in
  `infra-platform` and never squad-deployed. The hosting target is not decided
  here; it gets its own record.

## Consequences

Squads ship infrastructure without waiting on the platform for anything the
catalogue already covers, and every resource they create carries AeroFlow's
naming, tags, identity and diagnostics. A malformed workload definition fails
at compile time with IntelliSense, not at deploy time with an ARM error.
Resource-level maintenance is inherited from Microsoft rather than owned.

The catalogue becomes the bottleneck. Nothing is deployable until a module
exists, and there is no per-squad exemption; a squad that needs something new
waits for a module or a new `advanced` key. This is a promise the platform has
to keep: requests are prioritised as delivery work, and a minimal first module
version beats a complete late one.

The gate is code we maintain. It is a source check, not a parser, so it can be
wrong in both directions, and it needs tests and a release like any other
workflow. It proves what the Bicep references; layer 2 proves the Bicep was
deployed through the gate. Neither stops someone with Owner rights in the
portal, which is why layer 3 exists, and a tag is a claim anyone with write
access can copy — layer 3 catches accidents and drift, not a determined bypass.

In a one-person organisation, required CODEOWNERS review on `infra-platform`
cannot be satisfied by its author. Review is not required, as for
`docs/decisions/`; CI and the gate carry enforcement until a second maintainer
exists.

What is given up is unit-testable infrastructure. Bicep offers linting,
`what-if`, and policy assertion via PSRule, which is not the same as testing
logic in isolation. We accept this because the platform layer deliberately
contains little logic to test; if it grows enough logic to need tests, that is
a signal the layer is doing too much. Pinning a PSRule baseline means new rules
do not appear in CI unannounced.

Revisit if module requests routinely wait longer than a sprint; if the gate's
false positives cost more than the drift it prevents; if the OIDC workflow
binding cannot be made to work, in which case layer 2 falls back to
repository-and-environment-scoped credentials and the gate carries more
weight; or if platform modules turn out to be pass-throughs that add nothing
but indirection.

## Alternatives considered

**ADR-0002's escape hatch: squads may delete the platform module and call AVM
directly.** Rejected. It protects squads from a poor catalogue by letting every
squad leave it, and the cost lands on consistency: naming, tags, identity and
diagnostics get rediscovered per squad. The sealed `advanced` parameter and a
fast contribution route are the pressure valve instead. Revisit if the
catalogue cannot keep pace and squads are blocked more than they are served.

**Convention and documentation only.** Rejected. A handbook rule with no check
is a claim rather than a fact, and review cannot enforce it in an organisation
of one. Revisit if the gate's maintenance cost exceeds the drift it catches
over a sustained period.

**Azure Policy as the primary control.** Rejected. It fails at deploy time,
after merge, and sees resources, not whether they came from a governed module.
It stays as the backstop. Revisit if the gate proves unmaintainable and tag
policy alone is enough.

**AVM consumed directly by squads, with no platform layer.** Rejected: the
opinions are the product. Without a platform module, every squad rediscovers
tagging, diagnostics and identity wiring independently. Revisit if the
platform modules turn out to be pass-throughs that add nothing but indirection.

**Pulumi with C#.** Rejected. The type safety it offers is available in Bicep
through user-defined types, and its distinguishing advantage — real unit testing
of infrastructure code — addresses a problem this estate does not have, while
introducing state management as a permanent operational cost. Revisit if
AeroFlow becomes multi-cloud, or if the platform layer acquires enough
conditional logic that policy assertion is genuinely insufficient.

**Terraform.** Rejected. Strong module ecosystem and the same state cost as
Pulumi, with no compensating advantage on an Azure-only estate. Revisit under
the same trigger as Pulumi — a real multi-cloud need, where one tool across
providers outweighs giving up deployment stacks' state-free lifecycle.

**Raw ARM templates.** Rejected. No authoring ergonomics, no type system, and
no reason to choose it now that Bicep compiles to the same thing. Revisit only
if Bicep itself stalls or its tooling regresses badly enough that hand-written
ARM becomes the more reliable option — unlikely given it's Microsoft's own
stated direction for the language.

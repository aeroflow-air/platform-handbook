---
id: 9
title: Workload manifest as the paved road, with a guarded side door in infra/
status: draft
date: 2026-09-28
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "template-*", "aeroflow-workflows", "infra-platform"]
design-doc: null
---

## Context

ADR-0008 lets agents request infrastructure only through a `workload.yaml`
manifest, and left to this record what it holds and who turns it into
`br/platform:*` modules. Banning all IaC in service repos would make every
uncovered need wait on Platform, so ADR-0006's route stays open, guarded.

Nothing here exists yet. No repo has a `workload.yaml` or a `CODEOWNERS` for
`infra/`, and no `infra-boundary` label exists. `aeroflow-workflows` (tagged
`v0.1.0`) holds `dotnet-ci.yml`, `validate-decisions.yml` and a self-test,
but no deploy workflow. There is no `infra-platform` repo, so no module
exists. Both `svc-*` repos and `template-dotnet-service` have an `infra/`
holding only a README, and require no pull request reviews today.

## Decision

**The manifest is the paved road. ADR-0006's hand-composed `infra/` is a
guarded side door. Raw resources and AVM stay off the route to live.**

```yaml
workload: flight-status
repo: svc-flight-status
dataClass: internal
capabilities: [http, identity]
modules:
  hosting: br/platform:container-app-service:x.y.z
```

- **Paved road.** Every `svc-*` and `template-*` repo carries a
  `workload.yaml`. The shared deploy workflow generates the composition from
  it; the output is not committed. Most changes, and every agent
  infrastructure change (ADR-0008), go this way.
- **Schema.** `workload`, `repo`, `dataClass` (`public`, `internal` or
  `confidential`), `capabilities` (an enum starting at `http`, `identity`,
  `store`, `queue`) and `modules` (exact pins in Bicep's colon form). It lives
  in `aeroflow-workflows`, versioned with its tags. ADR-0013, planned, is to
  key human approval on `confidential`. A new capability needs a module and
  an ADR (ADR-0008).
- **Side door.** ADR-0006 stands unchanged: a squad may hand-compose governed
  `br/platform:*` modules in `infra/`, so nobody waits on Platform for a
  one-off.
- **Guard.** Any change under `infra/` is labelled `infra-boundary`
  automatically and needs approval from a human in the owning squad
  (`CODEOWNERS` on `infra/`, required code-owner review). It is by path, not
  author. ADR-0008 still says agents do not write Bicep; an `infra/` change
  an agent proposes anyway cannot merge alone.
- **Feedback loop.** Side-door use is discovery. The label makes those PRs
  searchable across the org. When the same composition recurs in about three
  services, it becomes a capability with a module.
- **Modules.** ADR-0006's contribute-first route stands: a squad may
  contribute a module to `infra-platform`, which Platform then owns. The
  hosting module is `container-app-service`.
- **Sandboxes.** Agents may work there. Sandbox work reaches a service repo
  only as a manifest change, or for humans through the side door.

This narrows ADR-0006 and ADR-0008 and supersedes neither.

## Consequences

The guarantee is weaker than a ban: not "no IaC in service repos" but "IaC
in a service repo is only governed modules, reviewed by a squad human".

The done test still holds: a new service can be built without writing a
`resource` block. Identity and network changes still get a human, through
ADR-0013 on the manifest or the guard in `infra/`.

The generator is our code: a bug in it reaches every service, so it needs
tests and releases like ADR-0006's gate. The Renovate rule in
`docs/infrastructure/module-upgrades.md`, tested on Bicep only, must handle
pins in both YAML and Bicep.

The guard needs a second human. ADR-0006 notes that required code-owner
review cannot be met in a one-person organisation, and today each team has
one member.

Open, not decided here:

- The capability-to-module mapping, until the first module is published.
- Who reads the `infra-boundary` search, and how often.
- Whether `infra/` changes touching identity or network also need Platform,
  as ADR-0013 will require for the manifest.

Revisit if the generator becomes the queue.

## Alternatives considered

- **No IaC in service repos at all** (the previous draft). Rejected: every
  uncovered need waits on Platform. Revisit if the side door is used for most
  changes.
- **Hand-written Bicep checked against the manifest as the only route.**
  Rejected: two sources of truth for every service. Revisit if generation
  cannot express real services.
- **Commit the generated Bicep to the service repo.** Rejected: it drifts from
  the generator and blurs the side door. Revisit if reviewers need the
  generated output in the PR.
- **Free-form capabilities.** Rejected: a request nobody can check. Revisit if
  the enum needs an ADR for every service.

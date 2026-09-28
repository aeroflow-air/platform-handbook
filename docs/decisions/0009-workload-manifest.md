---
id: 9
title: Workload manifest schema, with the module composition generated in CI
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
manifest, and left to this record what it holds and who turns it into a
composition of `br/platform:*` modules. While squads may hand-write that Bicep
under ADR-0006, CI cannot tell an agent's composition from a human's.

Nothing here exists yet. No repo has a `workload.yaml`. `aeroflow-workflows`
holds `dotnet-ci.yml`, `validate-decisions.yml` and a self-test, but no deploy
workflow. There is no `infra-platform` repo, so no module exists, not even
`container-app-service`. In both `svc-*` repos and `template-dotnet-service`,
`infra/` holds only a README saying governed Bicep will land there.

## Decision

**Every `svc-*` and `template-*` repo carries a `workload.yaml`. The shared
deploy workflow generates the `br/platform:*` module composition from it.
These repos contain no infrastructure-as-code files at all.**

```yaml
workload: flight-status
repo: svc-flight-status
dataClass: internal
capabilities: [http, identity]
modules:
  hosting: br/platform:container-app-service:x.y.z
```

- **Fields.** `workload` (name), `repo`, `dataClass`, `capabilities`, and
  `modules`: exact pins keyed by role, in ADR-0006's form. Nothing else.
- **Capabilities** are an enum, starting at `http`, `identity`, `store` and
  `queue`. A new value needs a module and an ADR (ADR-0008). A capability is
  usable only once a module serves it; none does yet.
- **Generated, not written.** The deploy workflow in `aeroflow-workflows`
  generates the composition from the manifest on each run. Generated Bicep is
  not committed to the service repo.
- **No IaC in service repos.** No Bicep, ARM JSON or deploy scripts in any
  `svc-*` or `template-*` repo, whoever the author. This is what ADR-0008's
  "raw resource definition" means, and it makes the gate a file check.
- **The template carries a manifest**, so a new service starts with one,
  in place of the wired `infra/` ADR-0006 described.
- **Sandboxes.** Agents may work in ADR-0006's sandboxes. Sandbox work reaches
  a service repo only as a manifest change.
- **Hosting module:** `container-app-service`, the name ADR-0006 gave it.
- **Platform writes new modules** when a requested capability has none. An
  agent does not.

This keeps ADR-0006's governed catalogue, exact pins, sandboxes, deploy
identity and policy backstop, but moves the composition out of each service's
squad-written `infra/`, a route ADR-0008 left open to humans. Both records are
accepted and unchanged; whether this needs one superseding ADR-0006 is open.

## Consequences

The gate gets simpler: it looks for IaC files rather than checking module
sources. Bicep and ARM JSON are recognisable by extension and schema; a deploy
script is not, so the gate needs a rule for what counts as one.

The generator becomes our code: a bug in it reaches every service, so it needs
tests and releases like ADR-0006's gate. Squads lose hand-composition;
anything the capabilities cannot express waits for Platform.

The Renovate rule in `docs/infrastructure/module-upgrades.md` was tested on
Bicep; pins now live in YAML, so it needs rework. The three `infra/README.md`
files and `CLAUDE.md`'s IaC line describe the old route and need updating
once this is accepted.

Open, not decided here:

- The allowed `dataClass` values; only `internal` appears so far.
- Which module serves each capability, and whether `container-app-service`
  covers `http` and `identity` on its own.
- Whether ADR-0006's contribute-first route, where a squad writes a module and
  Platform then owns it, still stands beside "Platform writes new modules".
- Where the schema lives and how it is versioned.

Revisit if services often need what the enum can't express, or the generator
becomes the queue.

## Alternatives considered

- **Hand-written Bicep checked against the manifest.** Rejected: two sources of
  truth, and the gate must parse Bicep to compare them. Revisit if generation
  cannot express real services without an escape hatch.
- **Commit the generated Bicep to the service repo.** Rejected: IaC returns to
  the repo and drifts from the generator. Revisit if reviewers need the
  generated output in the PR.
- **Manifests for agents, ADR-0006's `infra/` route for humans.** Rejected: CI
  cannot tell authors apart (ADR-0008). Revisit if provenance (ADR-0011) proves
  reliable.
- **Free-form capabilities.** Rejected: a request nobody can check. Revisit if
  the enum needs an ADR for every service.

# How platform module upgrades reach squads

Squads deploy their infrastructure from governed Bicep modules published by the
platform as `br/platform:*`, pinned to exact versions (see ADR-0006).
This page describes how a new module version gets from the platform
into every service that uses the module, without the platform chasing anyone.

**Status.** Designed and proven locally, not yet running in the organisation.
The Renovate rule was tested with Renovate 44.115.12 against Microsoft's public
registry (`mcr.microsoft.com`), with a local test Git server standing in for
GitHub. It found every module reference, including `import … from`, and opened
one PR per outdated module, each changing only that version; `bicep build`
still passed on every branch. Our private ACR, GitHub itself and what-if on a
Renovate PR are not tested yet.

## The loop

1. **Platform publishes.** A new version of a module goes to the registry with
   a changelog entry. Published versions are never overwritten.
2. **Renovate opens PRs.** In every repo pinned to an older version, Renovate
   opens a PR that changes only that version. By default a new major gets its
   own PR, so a squad can take the latest 1.x without being pushed onto 2.0.
3. **The squad's PR checks run.** The PR workflow described in ADR-0006 runs
   `bicep build`, lint, PSRule and what-if, and posts the what-if diff on the
   PR.
4. **The squad merges when it suits them.** They read the changelog and the
   diff, and merge, wait or close. Nothing is forced.
5. **Old majors are retired** once nothing pins them any more.

## Why it helps the platform team

- **Upgrades become a pull, not a chase.** Nobody files tickets asking squads
  to upgrade. The PR is already there, with the checks already run.
- **Adoption is visible.** The open Renovate PRs show which services are behind
  on which module. Renovate also keeps a Dependency Dashboard issue in each
  repo (on by default in its recommended preset), listing its open PRs and every
  detected module with its current version, including those already up to date.
  Each dashboard is per repo, so an estate-wide view means reading across them,
  but that is enough to know when a major can be retired and how fast a fix is
  spreading.
- **Fixes roll out quickly.** A security or patch release reaches every
  affected repo as a ready-made PR on Renovate's next run, and the dashboards
  show which squads have not merged it, so follow-up is targeted.
- **Unmerged PRs are product feedback.** A PR squads will not merge usually
  means the change hurt them or was badly explained. That is worth a
  conversation, and a better module or changelog, not a mandate.
- **Squads keep control.** They choose when to upgrade, and old majors stay
  available while anything pins them.

## What the platform must do for it to work

- **Write a real changelog.** Renovate cannot read release notes from a Bicep
  module in a registry, so its PRs arrive with no notes and no source link.
  Renovate's `prBodyNotes` setting adds templated text to every PR body; its
  documentation and source show it can carry a link to the module's changelog
  (not yet tried in the test run).
- **Keep patch, minor and major honest.** Squads, and any Renovate rules we
  write, trust the version number. Renovate jumps straight to the newest
  version in a line, and because it has no release dates it cannot reliably
  hold back a version for a few days (`minimumReleaseAge`). Publish only what
  is ready.
- **Keep auto-merge off.** A clean `bicep build` proves the template compiles,
  not that it behaves the same. A person reads the what-if diff.
- **Limit the noise.** Use Renovate's `schedule` and grouping so a busy release
  week does not bury squads in PRs.
- **Keep the alias mapping in sync.** The org preset repeats by hand what
  `bicepconfig.json` says about where `br/platform` lives. Change both in the
  same PR. A repo whose alias points elsewhere gets no PRs, silently.

## How it runs

Renovate runs self-hosted as a scheduled GitHub Action owned by the platform.
Its configuration, including the custom rule, lives in an org preset (for
example `aeroflow-air/renovate-config`) that each service repo's
`renovate.json` extends. The rule is three regex patterns, one each for the
full `br:` form, the `br/public` alias and the `platform` alias, looked up as
OCI tags with semver versioning.

The Action needs a GitHub App token or a personal access token: PRs opened with
the workflow's own `GITHUB_TOKEN` do not trigger other workflows, so the
squad's checks would never run. Sign-in to our private ACR is intended to use
OIDC (`azure/login`, then `az acr login --expose-token`, passed to Renovate as
a host rule) and is still to be confirmed.

The decision this supports is ADR-0006,
[`docs/decisions/0006-governed-bicep-modules-only.md`](../decisions/0006-governed-bicep-modules-only.md).

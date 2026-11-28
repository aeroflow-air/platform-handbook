---
id: 24
title: A minimal Backstage service catalogue fed by catalog-info.yaml in every repo
status: draft
date: 2026-11-28
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos", "platform-handbook", "backstage"]
design-doc: null
---

## Context

`CLAUDE.md` says base permission is read because "discoverability is the
point of a catalogue", and ADR-0001 rejected having no naming convention
because "the org list is the catalogue until the portal exists". There is
no portal. On 28 Nov 2026 `aeroflow-air` has 12 repositories and no
`catalog-info.yaml` in any of them. Today the answers to "what is this
repo, who owns it, what does it publish, what reads it?" are scattered:

- **Ownership** is two GitHub teams (`platform`, `squad-checkin`), each with
  one member. ADR-0009 records `squad-checkin` as owning the `svc-*` repos
  and `template-dotnet-service`; everything else is Platform's. CODEOWNERS
  covers only agent context and `docs/decisions/`.
- **Event wiring** lives in the airport overview, each `docs/service.md`,
  `workload.yaml` `events:` blocks (ADR-0019) and producer-owned
  `contracts/<topic>/` examples. Nothing joins them.
- **APIs** are documented at runtime only (`/openapi/v1.json` in
  Development, ADR-0015); no OpenAPI file is checked in.

The squad-of-six test applies, and it bites: one person can hold 12 repos
in their head, and the org profile README plus the airport overview
already answer most questions. A portal on its own would be theatre. The
part that is not theatre is the data: a small, versioned, reviewable
description of each repo, kept next to the code it describes, that any
tool (Backstage, a script, an agent) can read.

## Decision

Every repository carries a root `catalog-info.yaml`, and a minimal
Backstage instance reads them.

- **Instance.** It lives in its own platform-operation repo,
  `aeroflow-air/backstage`. Tony has approved the repo and it is being
  created alongside this record; the instance arrives as a PR there.
  Upstream Backstage scaffold (1.57 line) and upstream configuration
  patterns only: no custom plugins, no software templates, no branding work.
- **Discovery.** The GitHub entity provider scans `/catalog-info.yaml` on
  `main` of every repo in the org named by `GITHUB_ORG` (`aeroflow-air`).
  The `githubOrg` provider imports org members and teams as User and Group
  entities, so `group:platform` and `group:squad-checkin` are the real
  GitHub teams and Groups are not hand-written.
- **Org-level entities** (Domains, Systems, shared Resources) live in this
  repo under `catalog/`, reached from a `Location` in the handbook's own
  `catalog-info.yaml`.
- **TechDocs** use the local builder, from `docs/` where a repo has it
  (`backstage.io/techdocs-ref: dir:.`).
- **Storage** is SQLite by default (in memory for local runs); Postgres
  in a container is optional and never required.
- **Token.** A read-only GitHub token (contents, metadata, `read:org`)
  comes from an environment variable. Nothing secret is committed.

### Hosting and cost

Zero extra cost. The instance runs locally, in a Codespace on the
personal free allowance, or as a container on a laptop. No paid hosting,
no paid plugins, no hosted Backstage. Backstage is Apache-2.0 open source.
Hosting it in Azure (for example on Container Apps through `workload.yaml`)
is a later decision for Tony, and would cost only what the published Azure
pricing says at that time; nothing here commits to it.

### Modelling conventions

| Kind | Used for | Lives in |
| --- | --- | --- |
| Domain | `airport-operations`, `platform-engineering` | `catalog/domains.yaml` |
| System | `airport`, `developer-platform`, `public-site` | `catalog/systems.yaml` |
| Resource | shared infrastructure squads depend on (today: `event-bus`, the Service Bus emulator of ADR-0013) | `catalog/resources.yaml` |
| Group, User | imported from GitHub teams and members | `githubOrg` provider |
| Component | one per repo, or per deployable when a repo holds several (aeroflow-local) | the repo's `catalog-info.yaml` |
| API | only where a contract file exists: today the `<domain>-events` examples under `contracts/` (ADR-0019), `type: event-contract` | the producer's `catalog-info.yaml` |

- **Component types:** `service`, `website`, `library`, `template`,
  `documentation`, `infrastructure`, and `tool` for local-only developer
  tooling.
- **Lifecycle is honest:** `experimental` unless something serves real
  readers. Only the public site (`site-customer` on GitHub Pages) and the
  org profile (`.github`) are `production`. Nothing is deployed to Azure,
  so no service is `production`.
- **Owners** are `group:<github-team-slug>`. A repo whose owner is not
  written down anywhere is owned by `group:platform` until it is.
- **Annotations:** always `github.com/project-slug`; `backstage.io/techdocs-ref`
  only where `docs/` exists.
- **Relations** only where the code shows them: `providesApis` for a topic
  the component owns, `consumesApis` for a subscription it reads, `dependsOn`
  for a package or resource it really uses. No invented HTTP APIs: an
  OpenAPI API entity appears when a service checks in its spec.
- **Names** match the repo name, so a squad can find the entity from the
  clone URL. A repo created from `template-dotnet-service` renames the
  entity in the same PR (a follow-up adds that step to the new-service
  checklist skill).

## Consequences

Easier: one place to answer "who owns this, what does it publish, who
reads it"; `affects:` on decision records gets the portal ADR-0001
anticipated; agents can read `catalog-info.yaml` without the portal.

Harder: one more file per repo that can drift. The airport overview and
`docs/service.md` still own the prose; `catalog-info.yaml` holds only
relations and must change in the same PR as a new topic, subscription or
owner, as the service-docs standard already asks for those documents.

Costs: no money; a Node toolchain and a yarn lockfile to keep current in
the `backstage` repo, and an upgrade every few Backstage releases. If the
instance is not run for a month, delete it and keep the YAML: the files
stand on their own.

The repo name `backstage` names a tool, which ADR-0001's "capability, not
technology" rule discourages. It is accepted because the repo is the
Backstage app itself: if the tool changes, the repo is replaced, not
renamed.

## Alternatives considered

**A hand-maintained catalogue in one YAML or Markdown file here.**
Rejected: it drifts from the repos it describes and needs a handbook PR for
every service change. Revisit if Backstage is dropped; the per-repo files
can be concatenated into one.

**Port, Cortex, OpsLevel or hosted Backstage (Roadie).** Rejected: commercial
hosted products, against the zero-extra-cost rule, and catalogue data would
live outside the org. Revisit if AeroFlow had a platform budget and more
than one team needing scorecards.

**Adding AeroFlow to another organisation's Backstage instance.** Rejected:
AeroFlow stays fully separate from other organisations, with its own
instance, repo and data. Not revisited.

**Backstage with custom plugins, software templates and Postgres from day
one.** Rejected as scaffolding with an empty catalogue. Revisit templates
when services are created from the template often enough that the manual
checklist hurts; Postgres when the instance is hosted.

**No portal: the org profile README and the airport overview.** Not
rejected outright; it is the fallback. Revisit (and delete the instance)
if nobody opens the portal in a month or `catalog-info.yaml` drifts from
the code.

---
id: 23
title: Central, versioned agent skills and a short AGENTS.md per repo
status: draft
date: 2026-11-21
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos", "template-dotnet-service", "aeroflow-workflows"]
design-doc: "docs/design/agent-context-audit.md"
---

## Context

AI coding agents (Claude Code, the Claude review workflow, Copilot cloud agent
and code review) already write and review AeroFlow code. What they know about
our standards comes from a handful of hand-copied files. An audit of all 11
`aeroflow-air` repos on 21 Nov 2026 found:

| Repo | Agent context | Covers | Issues |
|------|---------------|--------|--------|
| platform-handbook | `CLAUDE.md` (131 lines) | Org purpose, naming, settings, stack, ADR rules | Stack row promises separate libraries for config binding, ProblemDetails and error middleware; reality is one `AeroFlow.ServiceDefaults` package and per-service code. "React frontends", "database per service" and the release manifest are stated as fact but do not exist. No mention of ADR-0022 or ServiceDefaults. |
| svc-gate-allocation, svc-flight-status, svc-baggage-reclaim | `CLAUDE.md` (40–43 lines each) | ADR-0004 rules, layout, topics, outbox, tests | Same 12-line conventions block copied into each one (and into the template) from `coding-standards.md`. "Local package feed in `lib/packages`" goes stale with the feed switch. The linked `docs/service-defaults.md` and `lib/README.md` still say no `lib-*` repo or feed exists. |
| template-dotnet-service | `CLAUDE.md` (38 lines) | Same block, plus "rename this file" | Does not mention the in-repo copy of `AeroFlow.ServiceDefaults`, which is now a second source that has already drifted from lib-service-defaults (csproj, README). The README still says to use a project reference until a feed exists. |
| lib-service-defaults | `CLAUDE.md` (14 lines) | Event id ranges, analysers, release by tag | Accurate. |
| aeroflow-workflows | No file. The `ai-code-review.yml` prompt acts as context | Review priorities | Asks for "minimal API conventions", but every service uses controllers. Points at "the repo's CLAUDE.md", which four repos do not have. Knows nothing about ServiceDefaults, event ids or CA1848. |
| aeroflow-local, infra-platform, site-customer, .github | None | — | aeroflow-local (AppHost, simulator, ops dashboard) is the most intricate repo and has no agent context. |

No repo has `AGENTS.md`, `.github/copilot-instructions.md`,
`.github/instructions/`, `.claude/`, `.github/skills/`, `.agents/`,
`.cursor/rules`, `.cursorrules`, `GEMINI.md` or `.windsurfrules`. Tools that
read only `AGENTS.md` see nothing. Copilot does read `CLAUDE.md`, so today it
sees the same copies Claude does.

**Standards not captured in any agent file** (verified against code):

- **ProblemDetails mapping.** It is described as a rule but no recipe exists.
  The 400/404/409 + `code` mapping is copied in `Controllers/ProblemResults.cs`
  in gate-allocation and baggage-reclaim, and written inline in
  flight-status's `FlightsController`.
- **Config binding and validation.** Every service uses
  `Configure<T>(GetSection(...))` with no `ValidateOnStart` or validation. The
  handbook stack table promises a config-binding library that does not exist.
- **Health checks.** `/health` (readiness) and `/alive` (liveness) appear only
  in the template README and ADR-0022. No service registers a dependency
  check, so readiness is not yet "including configured dependencies".
- **Observability contract** beyond event ids: resource attributes, the
  `Observability:Squad` setting, custom spans through an `ActivitySource`
  named after the service, and `ObservabilityContractTests` with
  `LogCollector`.
- **Writing a decision record.** The rules are in the handbook `CLAUDE.md` and
  `docs/decisions/README.md`, but the four service repos are not told when a
  decision is service-local (`docs/decisions/` in the repo) or org-wide.
- **Test approach.** It says "unit tests, no mocks in domain" but not that we
  use xUnit, `WebApplicationFactory` API tests, contract tests against copied
  schemas (ADR-0019) or observability contract tests.
- **`workload.yaml`** (ADR-0009), **Entra auth at the edge** (ADR-0018),
  **OpenAPI/Scalar** (ADR-0015) and **pinning `aeroflow-workflows` tags**,
  where `v0.6.0` needs `packages: read`.

Per-file detail is in [docs/design/agent-context-audit.md](../design/agent-context-audit.md).

## Decision

**Agent guidance moves into one versioned repo, `aeroflow-air/agent-skills`.
It holds one small skill per task. Each repo gets a short `AGENTS.md` with
the non-negotiables, and a pinned copy of the skills is synced into the repo,
where agents actually look.**

- **Skills are small and task-shaped.** Each skill is
  `skills/aeroflow-<task>/SKILL.md` with `name` and `description` frontmatter
  (Agent Skills format). The body has three parts: *When to use*, *Steps*
  (at most about 10), and *Example*, which links to real code. Each SKILL.md
  stays under about 60 lines. Skills link to the handbook and ADRs and do not
  restate them.
- **Starter set:**

  | Skill | When | Steps (outline) | Real example |
  |-------|------|-----------------|--------------|
  | `aeroflow-add-endpoint` | New HTTP route | Request/response records in `Models/`; call pure domain, `Match` the `Result`; errors to ProblemDetails via `ProblemResults`; `[ProducesResponseType]`; auth policy if it writes (ADR-0018); API test with `WebApplicationFactory`; update `docs/service.md` | [AllocationsController](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/src/AeroFlow.GateAllocation/Controllers/AllocationsController.cs), [ProblemResults](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/src/AeroFlow.GateAllocation/Controllers/ProblemResults.cs), [GateAllocationApiTests](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/tests/AeroFlow.GateAllocation.Tests/Api/GateAllocationApiTests.cs) |
  | `aeroflow-add-queue-consumer` | Subscribe to another squad's topic | Copy the contract schema (ADR-0019); processor → handler → pure planner; idempotency by event id in the same atomic store update; `Ignored`/`Rejected` with a reason, never throw; publish only through the outbox with deterministic ids (ADR-0017); duplicate-delivery and contract tests | [FlightEventsProcessor](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/src/AeroFlow.GateAllocation/Messaging/FlightEventsProcessor.cs), [GateEventHandler](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/src/AeroFlow.GateAllocation/Messaging/GateEventHandler.cs), [GateEventHandlerTests](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/tests/AeroFlow.GateAllocation.Tests/Messaging/GateEventHandlerTests.cs) |
  | `aeroflow-add-otel-tracing` | Adding observability to a service, a business event or a custom span | Reference `AeroFlow.ServiceDefaults` from the feed; `AddServiceDefaults()` + `MapDefaultEndpoints()`; set `Observability:Squad`; business events with `[LoggerMessage]` from 10,000; custom spans from an `ActivitySource` named after the service; no PII; add an observability contract test | [Extensions.cs](https://github.com/aeroflow-air/lib-service-defaults/blob/main/src/AeroFlow.ServiceDefaults/Extensions.cs), [service-defaults.md](https://github.com/aeroflow-air/lib-service-defaults/blob/main/docs/service-defaults.md), [OutboxDispatcher logs](https://github.com/aeroflow-air/svc-baggage-reclaim/blob/main/src/AeroFlow.BaggageReclaim/Messaging/OutboxDispatcher.cs), [ObservabilityContractTests](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/tests/AeroFlow.GateAllocation.Tests/ObservabilityContractTests.cs) |
  | `aeroflow-write-decision-record` | A choice another squad, or future you, needs to know | Org-wide or service-local test; copy `_template.md`; next free id; status `draft`; rejected alternatives each name a revisit trigger; one step per merged PR; run the validator | [README](https://github.com/aeroflow-air/platform-handbook/blob/main/docs/decisions/README.md), [_template.md](https://github.com/aeroflow-air/platform-handbook/blob/main/docs/decisions/_template.md), [ADR-0022](https://github.com/aeroflow-air/platform-handbook/blob/main/docs/decisions/0022-observability-on-the-golden-path.md) |
  | `aeroflow-new-service-checklist` | Creating a `svc-*` from the template | Name by capability (ADR-0001); Use this template; rename the project; `workload.yaml` `workload`/`repo` (ADR-0009); pin `aeroflow-workflows` and grant `packages: read`; replace the demo with a `Domain/` core; own topic `<capability>-events`; `docs/service.md` from the template; fill in `AGENTS.md`; add it to the airport overview if it joins the event flow | [template README](https://github.com/aeroflow-air/template-dotnet-service/blob/main/README.md), [workload.yaml](https://github.com/aeroflow-air/svc-gate-allocation/blob/main/workload.yaml), [service-doc template](https://github.com/aeroflow-air/platform-handbook/blob/main/templates/service-doc.md) |

  Likely next skills, added only when someone has asked for them twice:
  `aeroflow-add-config-options` and `aeroflow-add-health-check`.
- **Versioned like our libraries.** Use SemVer with `vMAJOR.MINOR.PATCH` tags
  and a GitHub Release with a changelog, the same habit as
  `aeroflow-workflows` and `lib-service-defaults`. A new skill or new steps
  is a minor bump. Renaming or removing a skill, or changing a rule a skill
  enforces, is a major bump. Fixing a typo or a link is a patch. CI in
  `agent-skills` lints the frontmatter (`gh skill publish --dry-run`) and
  checks that every example link resolves.
- **Discovery by synced folder, not by URL.** Agents load skills only from the
  checked-out repo. They do not fetch a URL from another repo. Each consuming
  repo therefore holds a pinned copy under `.claude/skills/`. That one folder
  is read by Claude Code and by Copilot (cloud agent, code review, CLI and
  VS Code). A pin file at the repo root controls it:

  ```yaml
  # .agent-skills.yaml
  source: aeroflow-air/agent-skills
  version: v1.0.0          # tag, like a workflow pin
  skills: default          # or an explicit list
  exclude: []              # e.g. [aeroflow-add-queue-consumer] for an API-only service
  ```

  A reusable `sync-agent-skills.yml` in `aeroflow-workflows` copies
  `skills/aeroflow-*` at that tag into `.claude/skills/` and fails the PR on
  drift. On a schedule it opens a bump PR, the same way module upgrades reach
  squads. Locally, `gh skill install aeroflow-air/agent-skills <skill> --pin
  <tag>` does the same job by hand, but `gh skill` is still in preview, so it
  is not the mechanism CI relies on.
- **The template carries the default set.** `template-dotnet-service` includes
  `.agent-skills.yaml` (`skills: default`), the synced `.claude/skills/` and
  `AGENTS.md`. A new service starts pinned and receives bump PRs like any
  other repo.
- **Overrides are local and visible.** The sync owns only `aeroflow-*`
  folders. A squad's own skill uses any other name and is never touched. To
  replace a platform skill, the squad lists it under `exclude` and adds a
  differently named skill, for example `baggage-add-endpoint`. Overrides stay
  greppable in one file and show up in review.
- **Short `AGENTS.md` everywhere, `CLAUDE.md` as a pointer.** Each repo gets
  an `AGENTS.md` of no more than about 40 lines. It holds what the repo is,
  the non-negotiables, the build and test commands, and links to skills and
  standards. `CLAUDE.md` shrinks to `@AGENTS.md` plus anything specific to
  Claude. Domain facts specific to the repo (topics, layout) stay in
  `AGENTS.md`. The copied conventions block goes. The AI review prompt points
  at `AGENTS.md` and drops "minimal API".

  ```markdown
  # <repo>
  <One line: what this service does.> Owner: <squad>.

  ## Non-negotiables (CI enforces those marked *)
  - Domain is pure: no I/O, logging, clock or `throw` for business rules; `Result<T>` / `Option<T>` (ADR-0004).
  - * `[LoggerMessage]` only, no `Console`; business event ids ≥ 10,000 (ADR-0022).
  - * `AddServiceDefaults()` + `MapDefaultEndpoints()`; `/health` readiness, `/alive` liveness.
  - Errors leave the HTTP edge as ProblemDetails 400/404/409 with `code`.
  - Publish only to `<topic>`, via the outbox, deterministic ids; handlers idempotent (ADR-0013/0017).
  - * Options validated at startup; no secrets in config, code or logs.
  - * Workflows pin `aeroflow-workflows` tags and declare `permissions`.
  - Update `docs/service.md` in the same PR as behaviour changes.

  ## Build and test
  `dotnet build -warnaserror && dotnet test`

  ## Skills
  `.claude/skills/` (pinned in `.agent-skills.yaml`). Standards: platform-handbook `docs/standards/`.
  ```

## Enforcement

A rule an agent can skip is a suggestion. Each non-negotiable either has a
check or is marked as review-only:

| Rule | Enforced today | Could be enforced by |
|------|----------------|----------------------|
| No `Console` / `Debug.WriteLine` | Yes: BannedApiAnalyzers (RS0030) from ServiceDefaults | — |
| `[LoggerMessage]`, constant templates | Yes: CA1848, CA2254 as errors | — |
| Warnings fail the build, nullable on | Yes: `Directory.Build.props` | — |
| Business event ids ≥ 10,000 | No (contract tests cover platform logs only) | A Roslyn analyser in ServiceDefaults |
| No logging, I/O, clock or `ILogger` in `Domain/` | No | An architecture test (NetArchTest) in the template; banned-namespace check scoped to `Domain/` |
| No `throw` for business rules; `Option` not `null` in domain | No | Architecture test for nullable return types in `Domain/`; review for the rest |
| ProblemDetails for every error response | No | API test asserting `application/problem+json` for 4xx; ServiceDefaults could ship `ProblemResults` |
| Options validated at startup | No | `ValidateOnStart` in the template plus a startup test that runs with missing config |
| `/health` and `/alive` mapped | Yes: `HealthEndpointTests` | — |
| Outbox only, deterministic ids, idempotent handlers | Partly: handler tests | Arch test: handlers do not depend on the publisher |
| Contracts additive (ADR-0019) | Partly: contract tests | Schema diff check in CI |
| Pinned workflow tags, explicit `permissions` | Partly: actionlint in aeroflow-workflows | A check in `dotnet-ci.yml` for `@main` and missing `permissions` |
| ADR shape and lifecycle | Yes: `validate-decisions.py` | — |
| `docs/service.md` kept current | AI review only | Path rule: `src/` changes in Models, Messaging or settings need a `docs/service.md` change or a label |
| Skills match the pin | No | `sync-agent-skills.yml` drift check |

## Consequences

Agents in every repo get the same rules from one place. A rule changes in one
PR plus a version bump, not by editing five copies. Skills are loaded only
when relevant, which keeps `AGENTS.md` short. The audit's stale statements
get fixed as part of the rollout, not as one-off clean-ups.

What it costs: one more repo to version, a sync workflow, and a bump PR per
repo per release. Example links can rot when code moves, so CI link checks
are mandatory, not optional. The vendored `.claude/skills/` copy is
duplication by design. It is accepted because agents cannot read across
repos, and the drift check keeps it honest.

This record does not create `agent-skills`, change any repo or alter the
review workflow. Those follow once it is accepted.

## Alternatives considered

**Keep per-repo `CLAUDE.md` files and fix the drift.** Rejected: the drift
found here comes from copying. Revisit if the org shrinks to one or two
service repos.

**Org-level instructions only (Copilot organisation instructions, `.github`
repo).** Rejected: they reach Copilot alone, are not versioned or pinnable,
and do not reach Claude Code or the review workflow. Revisit if all agents
read one org-level source.

**Git submodule of `agent-skills`.** Rejected: `dotnet-ci.yml` does not
fetch submodules, and agents and squads handle submodules badly. Revisit if
the shared checkout adopts submodules.

**Publish skills as a NuGet or npm package.** Rejected: agents read files in
the repo, not package caches. Revisit if agent hosts read skills from
packages.

**`.agents/skills/` or `.github/skills/` instead of `.claude/skills/`.**
Rejected for now: `.claude/skills/` is the one folder both Claude Code and
Copilot read. Revisit when Claude Code reads `.agents/skills/`, and move
there to be tool-neutral.

**One big standards skill.** Rejected: large always-loaded context gets
skimmed, and task skills load only when needed. Revisit if skill selection
proves unreliable in practice.

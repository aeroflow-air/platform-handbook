---
id: 11
title: Platform productivity metrics — teams, not individuals
status: draft
date: 2026-10-05
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos"]
design-doc: null
---

## Context

AeroFlow is a portfolio platform for a squad of about six. Employers and
collaborators will ask how we know the platform helps people ship. The industry
default — lines of code, story points, individual commit counts, or AI “usage”
dashboards — measures theatre and is trivially gamed.

What we need is evidence that the **platform serves teams**: shorter safe
delivery loops, fewer failed changes, faster recovery, and a developer
experience that squads would choose again. Individual output metrics fail
because people optimise the score (batch commits, avoid hard work, inflate AI
annotations) while the system stays slow or brittle. Once a number is used to
rank people, it stops describing reality.

This hangs off the golden path (`template-dotnet-service`, reusable workflows in
`aeroflow-workflows`, Container Apps hosting per ADR-0007, workload manifests
per ADR-0009). Metrics should fall out of how a service is scaffolded and
shipped — not become a second product every squad wires by hand. Quality
accountability already lives in the squad (ADR-0005); these measures tell us
whether **platform interfaces and CI** help that squad, not whether a named
engineer is “productive.”

## Decision

**Measure how well the platform serves teams. Never publish or reward
individual productivity scores.**

We run three complementary views, all aggregated at **service / squad /
org** grain:

### 1. Delivery flow — four DORA measures

Derived automatically from GitHub Actions and deployment telemetry that the
golden path already produces. No manual entry.

| Measure | Precise definition | Primary data source |
|---------|--------------------|---------------------|
| **Deployment frequency** | Count of **successful production deployments** per service per calendar week. A deployment is a workflow run that applies a release to the production environment (not build-only, not plan/what-if). | GitHub Actions: production deploy workflow runs with `conclusion=success` and environment `production` (or the org’s agreed prod environment name). |
| **Lead time for changes** | Median time from **first commit on the merged PR** to **that commit’s first successful production deployment**. PRs without a prod deploy are excluded from the median until deployed. | GitHub: PR merge commit + associated commits; join to the deploy workflow that references the same git SHA (or release tag that points at it). |
| **Change failure rate** | Share of production deployments that are followed by a **hotfix, rollback, or incident-tagged revert** within 24 hours, or that fail health checks post-deploy such that the pipeline records a failed release. | Deploy workflow outcomes + follow-up PRs labelled `hotfix` / `rollback` (or linked incident) within 24h of the deploy SHA. Start with labels; tighten when incident tooling exists. |
| **Time to restore** | Median time from **failure signal** (failed prod deploy health, or `incident`/`rollback` label opened) to **next successful production deployment** that resolves it for that service. | Same deploy + label/incident events; clock starts at the failure event timestamp. |

Services not yet on the golden path are marked **uninstrumented** rather than
estimated. Missing data is a platform backlog item, not a squad performance
story.

### 2. Developer experience — quarterly survey

Once per quarter, a short anonymous survey aligned to the DX Core 4
dimensions: **speed**, **effectiveness**, **quality**, and **impact**. Five to
eight Likert items plus one free-text “what should platform fix next?”

Results are reviewed by platform (and published in aggregate to the org). Themes
directly feed the platform backlog priority order for the next quarter — survey
without backlog coupling is vanity. We do **not** break results down by named
individual. Squad-level cuts are allowed only when the squad has enough
respondents to preserve anonymity (rule of thumb: n ≥ 5).

### 3. AI-assisted authoring — join to outcomes, not adoption vanity

Track **share of merged PRs marked AI-assisted** alongside **median review
time** and **change failure rate** for the same cohort window.

- **Marking:** authors (or a bot) apply the org label `ai-assisted` when a
  substantial share of the change was AI-generated or AI-edited. Honest
  self-marking is enough at this scale; we do not scrape IDE telemetry.
- **Read-out:** for each service over a rolling 4-week window, show
  `% AI-assisted merges`, `median time PR open → approved`, and CFR for
  AI-assisted vs not. The question is whether AI **shortens safe delivery** or
  **moves effort into review and failures**.
- **Non-goal:** ranking engineers by AI usage, or a target % AI adoption.

### First dashboard sketch

One org page (GitHub Projects dashboard, or a static page fed by Actions
artefacts — pick the cheaper path in implementation):

1. **Flow** — four DORA tiles per service, 90-day sparkline, org median.
2. **Experience** — latest quarterly Core 4 scores + top free-text themes.
3. **AI join** — `% AI-assisted`, review-time delta, CFR delta (AI vs not).
4. **Coverage** — list of services missing prod environment hooks or labels.

No individual leaderboard. No story-point burndown as a productivity proxy.

### Anti-patterns (explicitly rejected)

- Individual commit, PR, or “lines changed” leaderboards.
- Using story points or ticket count as productivity.
- Deployment frequency targets without pairing CFR and restore time.
- AI adoption % as a goal divorced from review time and CFR.
- Manual spreadsheet entry of DORA numbers.
- Ranking squads against each other for reward (comparison for learning is
  fine; competition destroys honesty).

### Phased rollout

1. **Instrument the golden path** — ensure production deploy workflows emit
   consistent environment names and SHA metadata; document the `hotfix` /
   `rollback` / `ai-assisted` labels in the handbook.
2. **Publish DORA for golden-path services** — weekly Actions job writing an
   artefact or gist consumed by the dashboard sketch.
3. **First DX survey** — after at least two services have been through the
   path, so answers refer to a real platform rather than a template.
4. **AI join panel** — once label hygiene is good enough for a 4-week window.
5. **Only then** consider richer tooling (dedicated DX platform, incident
   system). Until then, GitHub-native signals beat another product.

## Consequences

Platform priorities become evidence-based: slow lead time or weak survey themes
are backlog input. Portfolio reviewers can see a coherent story — DORA from the
path, experience from humans, AI judged by outcomes.

Costs: label hygiene and consistent deploy workflow contracts. Early CFR will
be noisy until incident/hotfix conventions stick. Survey fatigue if we ask more
than quarterly or ignore the answers.

What becomes harder: impressing anyone who wants individual productivity
theatre. We refuse that ask in writing here.

## Alternatives considered

**Individual productivity dashboards (commits, PRs, AI keystrokes).** Rejected.
They measure gaming once used for evaluation. Revisit only if a regulator
legally requires named-person telemetry — record the constraint separately.

**DORA only, no survey.** Rejected. Flow metrics miss friction the platform
causes (docs, permissions, local loop). Revisit if response rates stay near
zero after two quarters — then fix the survey, don’t abandon the signal.

**Buy a full DX / analytics platform immediately.** Rejected at squad-of-six
scale; another product before the golden path emits clean events is scaffolding
with an empty catalogue. Revisit when three or more services need shared
history beyond what Actions artefacts can hold.

**Mandate AI usage quotas.** Rejected. Adoption targets without quality joins
reward annotation theatre. Revisit only if AI tooling is a paid seat we must
justify with outcome evidence — still join to CFR and review time, never raw
usage.
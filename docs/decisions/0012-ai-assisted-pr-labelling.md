---
id: 12
title: Labelling AI-assisted pull requests
status: draft
date: 2026-10-05
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos"]
design-doc: null
---

## Context

ADR-0011 treats **share of AI-assisted merges** as a platform signal, joined to
median review time and change failure rate. It named a single `ai-assisted`
label as a starting point but left the marking convention undefined. Without a
clear, auditable way to tag PRs, that panel is either empty or invents numbers.

We need one convention a squad of six will actually use: cheap to apply, easy
to query from GitHub, honest enough for portfolio metrics, and not a second
product (no IDE telemetry scrapers). Options on the table are a GitHub label, a
commit trailer, a PR template checkbox, or a combination.

Two different activities get conflated if we use one bit: **AI that wrote or
edited the change**, and **AI that only helped review**. ADR-0011’s join to
review time and CFR is about authoring, not review tooling — so the labels must
distinguish them.

A later impulse was to auto-apply labels from vendor usage APIs (Cursor AI Code
Tracking, Copilot usage metrics, Claude Code analytics, and similar). Those
paths either need **paid Enterprise seats**, return **aggregate / per-user
data that cannot join to a PR**, or both. **No additional cost is allowed for
this portfolio**, so paid and Enterprise-only APIs are out of scope. The only
new automated signal that stays zero-cost and GitHub-native is detecting when
**Copilot’s cloud agent authored the pull request**.

## Decision

**Source of truth for metrics: GitHub PR labels, applied before merge.** Authors
are prompted by a PR template checkbox. Automation may apply labels from
**zero-cost signals only**. Commit trailers remain a detection input, not the
metric store.

### Labels (org-standard)

| Label | Means | Counts for ADR-0011 AI share |
|-------|--------|------------------------------|
| `ai-authored` | A **substantial** share of the diff was AI-generated or AI-edited. “Substantial” is author judgement: more than trivial autocomplete. | **Yes** — this is the cohort |
| `ai-reviewed` | AI was used in **review** only. | **No** — tracked separately later if useful |
| `ai-declaration:none` | Author explicitly asserts neither. | Counts as not AI-authored |
| `ai-label:auto` | At least one content label was applied by automation. | Meta only — ignored by metrics |
| `ai-label:manual` | Human lock; automation must not overwrite content labels. | Meta only |

Do **not** use a vague `ai-assisted` umbrella once this record is accepted.

### How authors mark (human path)

1. **PR template** checklist: `ai-authored` / `ai-reviewed` / Neither.
2. **Author** applies matching label(s), or ticks Neither
   (`ai-declaration:none` when synced).
3. **Optional trailer** `Ai-Assisted: authored|reviewed|none` — fallback input
   for automation, not the dashboard query.

### Zero-cost automation (Copilot cloud agent only)

**New automated source:** if the pull request’s GitHub **author** (and, where
exposed on the event, the **actor** that opened it) matches a small allow-list
of Copilot cloud-agent identities — for example `Copilot`,
`copilot-swe-agent[bot]`, `github-copilot[bot]` — treat the PR as
`ai-authored`, set `ai-label:auto`, and sticky-comment the reason.

**What this free signal can detect**

- PRs **opened by** Copilot cloud agent (agent-created branches / agent PRs).

**What it cannot detect**

- Human-authored PRs where Copilot, Cursor, Claude Code, or chat only helped
  in the IDE.
- Copilot code review on a human PR (`ai-reviewed` still needs a human mark or
  a future free signal — none exists today without paid APIs).
- “Substantial” AI edits inside a human’s commits.

So coverage is **narrow**: agent-opened PRs only. Most AI-assisted day-to-day
work still depends on template, trailers, or honest self-labelling.

**Nightly collector:** **not needed.** Author/actor is available on
`pull_request` (and related) events. An event-time check in a label workflow is
enough. No secrets, no vendor poll, no cache job.

**Paid / Enterprise APIs:** do **not** integrate Cursor AI Code Tracking,
Copilot Usage Metrics API, Claude Code Analytics, Windsurf Analytics, or any
other paid usage export for labelling. Draft implementation that assumed
`CURSOR_API_KEY` is abandoned.

### Detection precedence (highest first)

Stop at the first decisive band:

1. **Manual lock / slash override** — `ai-label:manual` or `/ai-label …`.
2. **PR body markers** — template checkboxes or
   `<!-- ai-label: authored|reviewed|none -->` (human declaration; not auto).
3. **Copilot cloud-agent author/actor** — zero-cost GitHub-native →
   `ai-authored` + `ai-label:auto`.
4. **Commit trailers** — `Ai-Assisted: …` (fallback).
5. **Co-Authored-By allow-list** — known AI agents only; not Dependabot
   (fallback).
6. **No signal** — Phase B may remind when ready-for-review and undeclared;
   still non-blocking.

### Aggregate-only vendor sources

Copilot Usage Metrics, Claude Code Analytics, and Windsurf Analytics cannot
tie usage to a PR id or commit SHA. Treat them as:

- **Out of labelling** entirely.
- **Out of ADR-0011 delivery metrics** unless already free under a licence we
  already pay for **and** consumed only as **org/team aggregates** (never
  per-person charts). Today AeroFlow should **leave them out** rather than
  add seats or admin keys for dashboards.

### Worth building? (honest assessment)

**Marginal yes for a tiny change; no for a platform product.**

Extending automation with Copilot-agent author detection is a small,
zero-secret branch on the event-time label workflow already sketched for
trailers and body markers. It correctly tags a real, growing class of PRs and
keeps ADR-0011’s AI share from under-counting agent work.

It does **not** solve IDE-assisted human PRs. Building collectors, Enterprise
keys, or multi-vendor joins for that gap is **not worth it** under the
no-extra-cost rule — coverage would still be incomplete without human honesty.

**Recommendation:** when (and only when) the Phase B label workflow is built,
add Copilot-agent author/actor as band 3 alongside trailers and co-authors.
Do **not** build a nightly job, Cursor integration, or aggregate-API pipelines
for labelling. Rely on the PR template for everything the free signal misses.

### Auditability and enforcement

Unchanged in spirit: GitHub timeline for label changes; `/ai-label` overrides
are auditable; metrics snapshot labels **at merge time**. Phased enforcement
A (docs) → B (warn) → C (optional ruleset) still applies — do not start at C.

Permissions for any future workflow stay least-privilege: `contents: read`,
`pull-requests: write`. No vendor secrets.

### Feed into ADR-0011

Unchanged: `% ai-authored` on merged PRs; join to review time and CFR;
ignore meta labels; under-count if undeclared rather than invent usage.

## Consequences

Labelling stays affordable and GitHub-native. Agent-authored PRs can be
auto-tagged without new spend. Most AI-assisted human work remains a trust-
and-template problem — which matches a squad of six better than Enterprise
telemetry theatre.

Costs: maintaining a short Copilot-agent login allow-list; accepting narrow
auto-coverage. What we give up: automated detection of IDE AI on human PRs
without paid APIs.

## Alternatives considered

**Cursor AI Code Tracking / other paid Enterprise usage APIs for labelling.**
Rejected. Additional cost and/or Enterprise lock-in. Revisit only if the org
already has the seat for other reasons **and** the API joins to commit SHA or
PR id without per-person surveillance dashboards.

**Copilot Usage Metrics / Claude Code / Windsurf for labelling.** Rejected.
Aggregate or per-user/day only — cannot attribute to a PR. Revisit never for
labels; optional org-only ADR-0011 context only if already free.

**Nightly collector for agent authorship.** Rejected. Event-time author/actor
is sufficient. Revisit only if GitHub stops exposing author on PR events
(unlikely).

**Single `ai-assisted` label.** Rejected. Collapses authoring and review.

**Commit trailer as sole source of truth.** Rejected. Squash-merge and query
pain; kept as fallback band 4.

**Required ruleset from day one.** Rejected. Performative `none` ticks.
Revisit as Phase C after Phase B evidence.

**Build nothing automated at all.** Acceptable interim. The template and
manual labels already satisfy ADR-0011 if people use them. Automating only
Copilot-agent authorship is a small optional improvement, not a prerequisite.

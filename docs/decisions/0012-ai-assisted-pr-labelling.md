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

## Decision

**Source of truth for metrics: GitHub PR labels, applied before merge.** Authors
are prompted by a PR template checkbox; automation may sync or remind; commit
trailers are optional and never the metric source.

### Labels (org-standard)

| Label | Means | Counts for ADR-0011 AI share |
|-------|--------|------------------------------|
| `ai-authored` | A **substantial** share of the diff was AI-generated or AI-edited (Copilot, ChatGPT, Cursor, agents, etc.). “Substantial” is author judgement: more than trivial autocomplete. | **Yes** — this is the cohort |
| `ai-reviewed` | AI was used in **review** (summary, suggested comments, risk scan) but did not author the change. | **No** — tracked separately later if useful |
| *(neither)* | No meaningful AI involvement, or author declines to claim it. | Counts as not AI-authored |

Do **not** use a vague `ai-assisted` umbrella once this record is accepted — it
collapses the two meanings ADR-0011 needs to keep apart. Prefer exactly one of
`ai-authored` or `ai-reviewed` when only one applies; both may appear if AI both
wrote and reviewed.

### How authors and bots mark

1. **PR template** (golden path + handbook): a short checklist:
   - [ ] `ai-authored` — substantial AI-generated or AI-edited code
   - [ ] `ai-reviewed` — AI used only in review
   - [ ] Neither
2. **Author** (or the opening bot) applies the matching label(s) when opening or
   before ready-for-review. Self-marking is enough at this scale.
3. **Optional automation** (later, in `aeroflow-workflows`):
   - Reminder comment if the PR is `ready for review` and has none of the three
     declarations (no label and checklist unchecked).
   - Sync: if the template checkbox is ticked and the label is missing, apply
     the label (and vice versa for untick → remove, only while open).
4. **Commit trailer** `Ai-Assisted: authored|reviewed` is **optional** for
   people who prefer git-native notes. CI may *suggest* a label from trailers
   on the PR’s commits; it must **not** be the only signal (squash merges drop
   or rewrite trailers; metrics query PRs, not commit graphs).

### What counts

- **AI-authored:** model-produced or heavily model-edited code, config, tests,
  or docs that land in the merge. Human-written code with light autocomplete
  does not need the label.
- **AI-reviewed:** review assistance only. Does not move a PR into the
  ADR-0011 AI-authored cohort.
- **Not in scope:** scraping IDE telemetry, vendor “AI usage” dashboards, or
  estimating % of lines by tool.

### Auditability

- **Who can set/change:** anyone with write on the repo (the squad). Labels are
  not restricted to admins — friction kills honesty.
- **History:** GitHub’s PR timeline records label add/remove with actor and
  timestamp. That is the audit log; we do not duplicate it.
- **Metric snapshot:** ADR-0011 jobs read labels **at merge time** (or on the
  merged PR object). Post-merge label edits do not rewrite published weekly
  artefacts; a later correction is a note, not a silent rewrite.
- **Enforcement (phased, light):**
  - Phase A: documentation + template only.
  - Phase B: non-blocking workflow check — warn when ready-for-review and
    undeclared.
  - Phase C (optional): repository ruleset or required check that blocks merge
    until one declaration exists. Adopt only if honesty holds and reminders
    are ignored; do not start here — a hard gate teaches people to tick
    “Neither” blindly.

Org labels are created once (description matching the table) and reused across
repos so queries stay uniform.

### Feed into ADR-0011

For each service, rolling 4-week window on **merged** PRs:

- `% ai-authored` = merges with label `ai-authored` / all merges
- Join that cohort to median time PR open → approved and to change failure rate
  (AI-authored vs not), exactly as ADR-0011 specifies
- `ai-reviewed` may appear on a future panel; it does not affect the AI share
  numerator

Unlabelled merges count as **not** AI-authored. That biases the share down if
people forget — preferable to inventing AI usage, and Phase B reminders address
it.

## Consequences

ADR-0011’s AI panel becomes implementable with GitHub-native data. Authors get
a one-line habit; platform gets a stable query. Distinct labels keep “AI wrote
this” separate from “AI helped me review.”

Costs: creating org labels, adding a few lines to the PR template on the golden
path, and accepting imperfect self-reporting. A hard merge gate too early will
produce junk data.

## Alternatives considered

**Single `ai-assisted` label only.** Rejected. Collapses authoring and review;
breaks the ADR-0011 join. Revisit only if after two quarters nobody uses
`ai-reviewed` and the extra label is pure noise.

**Commit trailer as sole source of truth.** Rejected. Awkward under squash
merge; hard to query at PR grain; easy to omit on fixup commits. Revisit if the
estate standardises on merge commits and trailers are enforced in CI — still
pair with a PR label for dashboards.

**PR template checkbox without labels.** Rejected. Checkboxes in markdown are
weak to query and easy to edit without timeline clarity. Revisit never as the
metric source; keep them only as the prompt that drives labels.

**IDE / vendor telemetry.** Rejected at squad-of-six scale: another product,
privacy theatre, and weak join to merge outcomes. Revisit if a paid seat must
be justified with vendor stats — still keep GitHub labels for the delivery join.

**Required ruleset from day one.** Rejected. Forces performative “Neither”
ticks. Revisit after Phase B if undeclared ready-for-review PRs stay common.
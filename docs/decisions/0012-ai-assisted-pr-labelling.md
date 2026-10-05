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

Manual checkboxes alone will under-report. This record therefore also defines
**how automation applies labels**, how humans override it, and how that maps to
the staged enforcement path — without jumping straight to a hard merge gate.

## Decision

**Source of truth for metrics: GitHub PR labels, applied before merge.** Authors
are prompted by a PR template checkbox; automation detects high-confidence
signals and applies labels; commit trailers remain a detection input, not the
metric store.

### Labels (org-standard)

| Label | Means | Counts for ADR-0011 AI share |
|-------|--------|------------------------------|
| `ai-authored` | A **substantial** share of the diff was AI-generated or AI-edited (Copilot, ChatGPT, Cursor, agents, etc.). “Substantial” is author judgement: more than trivial autocomplete. | **Yes** — this is the cohort |
| `ai-reviewed` | AI was used in **review** (summary, suggested comments, risk scan) but did not author the change. | **No** — tracked separately later if useful |
| `ai-declaration:none` | Author explicitly asserts neither authored nor reviewed assistance. | Counts as not AI-authored |
| `ai-label:auto` | At least one of `ai-authored` / `ai-reviewed` was applied by automation, not by a human. Removable when a human confirms or corrects. | Meta only — ignored by metrics |

Do **not** use a vague `ai-assisted` umbrella once this record is accepted — it
collapses the two meanings ADR-0011 needs to keep apart. Prefer exactly one of
`ai-authored` or `ai-reviewed` when only one applies; both may appear if AI both
wrote and reviewed. `ai-declaration:none` is mutually exclusive with the other
two content labels for metric purposes (if both somehow appear, content labels
win and automation should remove `none`).

### How authors mark (human path)

1. **PR template** (golden path + handbook): checklist —
   - [ ] `ai-authored` — substantial AI-generated or AI-edited code
   - [ ] `ai-reviewed` — AI used only in review
   - [ ] Neither
2. **Author** applies matching label(s), or ticks Neither (automation will add
   `ai-declaration:none` when syncing from the template).
3. **Optional trailer** on commits: `Ai-Assisted: authored|reviewed|none` —
   detection input for the bot, not the dashboard query.

### Automation design

Ship a reusable workflow in `aeroflow-workflows` (for example
`label-ai-assistance.yml`) called from golden-path repos. Trigger on
`pull_request` types: `opened`, `edited`, `synchronize`, `ready_for_review`,
`reopened`, and on `issue_comment` (for override commands).

#### Detection signals (precedence, highest first)

When deciding what to apply, evaluate in this order and **stop at the first
decisive band**. Implementation: reusable workflow
`aeroflow-workflows/.github/workflows/label-ai-assistance.yml` and
`scripts/label_ai_assistance.py`.

1. **Manual override / human lock (highest)**  
   - Label `ai-label:manual`, **or**  
   - slash command `/ai-label …` on the PR.  
   Automation **must not** change content labels while locked.

2. **Explicit PR body markers**  
   - Template checkboxes, or `<!-- ai-label: authored|reviewed|none -->`.  
   - Human declaration; not marked `ai-label:auto`.

3. **Joinable tool telemetry (preferred over trailers)**  
   - **Copilot cloud agent:** PR author login is a known Copilot agent
     identity (`Copilot`, `copilot-swe-agent[bot]`, …). GitHub-native; no
     metrics API. → `ai-authored` + `ai-label:auto`.  
   - **Cursor AI Code Tracking** (Enterprise, alpha): per-commit SHA metrics
     joined to PR commits
     ([docs](https://cursor.com/docs/account/teams/ai-code-tracking-api)).
     Uses line shares only — **user identity fields are stripped** before
     storage (ADR-0011). Optional secret `CURSOR_API_KEY`; if unset, this
     sub-band is skipped. → `ai-authored` + `ai-label:auto` when thresholds
     match.

4. **Commit trailers (fallback)**  
   - `Ai-Assisted: authored|reviewed|none` on commits reachable from the PR
     head. Used when band 3 has no data.

5. **Known AI co-author trailers (fallback)**  
   - `Co-Authored-By` matching the AI agent allow-list. Not Dependabot.

6. **No signal**  
   - Phase B+: non-blocking reminder when `ready_for_review` and undeclared.

**Explicitly not used for labelling** (aggregate / per-user only — cannot
tie to a PR id or commit SHA):

- GitHub Copilot Usage Metrics API
  ([reference](https://docs.github.com/en/copilot/reference/copilot-usage-metrics/copilot-usage-metrics))
- Claude Code Analytics API
  ([docs](https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api))
- Windsurf Enterprise Analytics

Those feeds may still inform **org-level** ADR-0011 dashboards; they must not
drive `ai-authored` on an individual pull request.

#### What the bot does when it auto-applies

1. Add/remove the content label(s) per precedence.
2. Add `ai-label:auto` if it applied `ai-authored` or `ai-reviewed`.
3. Post (or update) a single sticky comment naming **which signal won**, for
   example: “Applied `ai-authored` from commit trailer `Ai-Assisted: authored`
   on `abc1234`. This is auto-labelled (`ai-label:auto`).”
4. Never invent labels from weak or ambiguous evidence — skip and remind.

#### Manual override (auditable)

Any author or reviewer with write access can:

| Action | Effect | Audit |
|--------|--------|--------|
| Change labels in the UI | Sets **manual lock**; bot stops overwriting content labels | GitHub timeline (actor ≠ bot) |
| Comment `/ai-label authored` | Apply `ai-authored`, clear `none`, set manual lock, remove `ai-label:auto` | Comment + bot acknowledgement + timeline |
| `/ai-label reviewed` | Same for `ai-reviewed` | Same |
| `/ai-label both` | Both content labels | Same |
| `/ai-label none` | `ai-declaration:none` only | Same |
| `/ai-label clear` | Remove content + `none` + `auto`; leave undeclared | Same |
| `/ai-label unlock` | Clear manual lock; bot may re-evaluate on next event | Same |

Disputing an auto-label is the same path: correct with `/ai-label …` or the UI.
False positives should be easy to undo; the sticky comment must say how.

#### False positives and false negatives

- **False positive (auto-labelled wrongly):** human overrides via UI or
  `/ai-label`; `ai-label:auto` comes off on successful override; weekly metrics
  use **merge-time** labels, so fix before merge.
- **False negative (missed AI use):** Phase B reminder on undeclared
  ready-for-review PRs; authors still responsible for honesty. We bias missing
  toward under-count (ADR-0011), not fabrication.
- **Squash merges:** trailers may disappear from `main`; that is why labels on
  the **PR at merge** remain the metric source.

#### Permissions (least privilege)

Reusable workflow job permissions — no broader:

```yaml
permissions:
  contents: read
  pull-requests: write   # labels + PR comments
```

Use `GITHUB_TOKEN` (or a fine-scoped GitHub App later if org rules block
`pull-requests: write` on the default token). **No** `contents: write`, no
`actions: write`, no org-admin token. The workflow must not push commits or
alter branch protection.

#### Mapping onto staged enforcement

| Phase | Human convention | Automation | Gate |
|-------|------------------|------------|------|
| **A — docs** | Template + label meanings published | Workflow not required | None |
| **B — warn** | Same | Workflow on; auto-apply from bands 2–4; sticky reason; remind if undeclared at ready-for-review | Non-blocking check (warn annotation / comment only) |
| **C — optional ruleset** | Same | Same + required status check “AI assistance declared” (any of `ai-authored`, `ai-reviewed`, `ai-declaration:none`) | Blocking only after Phase B shows reminders work and junk “none” ticks are rare |

Do **not** start at Phase C. A hard gate teaches performative `none` ticks and
poisons ADR-0011.

### Feed into ADR-0011

For each service, rolling 4-week window on **merged** PRs:

- `% ai-authored` = merges with `ai-authored` / all merges
- Join that cohort to median time PR open → approved and to CFR (AI-authored vs
  not)
- Ignore `ai-label:auto` and `ai-declaration:none` in the numerator
- Snapshot labels **at merge time**; post-merge edits do not rewrite published
  weekly artefacts

## Consequences

ADR-0011’s AI panel becomes implementable with GitHub-native data. Automation
raises recall without making trailers or vendor APIs the system of record.
Overrides stay visible on the PR timeline and in bot acknowledgements.

Costs: implementing and owning one reusable workflow; maintaining a small
co-author allow-list; accepting imperfect self-reporting for cases with no
trailer or checkbox. A Phase C gate too early will produce junk declarations.

## Alternatives considered

**Single `ai-assisted` label only.** Rejected. Collapses authoring and review;
breaks the ADR-0011 join. Revisit only if after two quarters nobody uses
`ai-reviewed` and the extra label is pure noise.

**Commit trailer as sole source of truth.** Rejected. Awkward under squash
merge; hard to query at PR grain; easy to omit on fixup commits. Kept only as
detection band 3. Revisit if the estate standardises on merge commits and
trailers are enforced in CI — still pair with a PR label for dashboards.

**PR template checkbox without labels.** Rejected. Checkboxes in markdown are
weak to query and easy to edit without timeline clarity. Kept as the author
prompt and as detection band 2.

**IDE / vendor telemetry without PR or commit join.** Rejected for labelling.
Copilot Usage Metrics, Claude Code Analytics, and Windsurf Analytics stay
dashboard-only. Cursor AI Code Tracking (commit SHA) and Copilot cloud-agent
authorship are the documented exceptions under band 3. Revisit other vendors
only with merge-correlated identifiers and a false-positive path.

**Required ruleset from day one.** Rejected. Forces performative `none` ticks.
Revisit as Phase C after Phase B evidence.

**Bot always overwrites human labels.** Rejected. Destroys trust and audit.
Manual lock (band 1) is mandatory once a human has set intent.
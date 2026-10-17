---
id: 20
title: Advisory AI code review with a shared Claude workflow
status: draft
date: 2026-10-17
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["aeroflow-workflows", "svc-*", "template-dotnet-service"]
design-doc: null
---

## Context

Issue #82 asks for a policy decision on the advisory Claude PR reviews
piloted from aeroflow-workflows#8: advisory only or ever a required check,
which repos opt in and with what cost guards, who owns spend on the org
`ANTHROPIC_API_KEY`, what code is sent to Anthropic, how fork PRs behave,
and how this relates to ADR-0012's AI-assistance labels. The pilot has run
since mid-October 2026, long enough to have evidence (below). The approach
is also written up publicly in the site-customer engineering blog,
"Claude code reviews" (14 Oct 2026).

What is actually in place (verified 2026-10-17):

- **One reusable workflow**, `ai-code-review.yml` in aeroflow-workflows,
  latest release **v0.3.1**, wrapping `anthropics/claude-code-action@v1`.
  The review prompt lives in that workflow — priority order: event
  contracts and idempotency, docs currency, tests, security, .NET practice,
  ADR-0004 domain conventions (the same checklist as
  `docs/standards/coding-standards.md`) — and a caller can append its own
  `extra-instructions`. No caller currently does.
- **Four thin callers**, all pinning `@v0.3.1` with identical shape:
  svc-gate-allocation, svc-flight-status, svc-baggage-reclaim and
  template-dotnet-service. Each passes `ANTHROPIC_API_KEY` explicitly (no
  `secrets: inherit`) and declares `contents: read`,
  `pull-requests: write`, `id-token: write`. aeroflow-local,
  infra-platform, site-customer and this handbook do **not** have the
  caller — the rollout is incomplete, and handbook PRs (including every
  recent ADR) get no AI review.
- **Cost and behaviour guards are the workflow defaults everywhere**:
  `max-turns` 25, skip when additions + deletions exceed 1,500 lines,
  skip drafts, skip fork PRs, skip PRs labelled `skip-ai-review`,
  15-minute timeout, one review at a time per PR (concurrency group,
  cancel-in-progress). The Claude step is `continue-on-error: true`; if it
  fails — including the known "finished over max-turns after already
  posting" case — a follow-up step posts a `::warning::` and the job stays
  green. The reviewer may comment (inline and one sticky summary) and read
  the diff; its allowed tools are restricted to commenting, `gh pr diff` /
  `gh pr view`, Read, Glob and Grep. It never approves, never requests
  changes formally, and never pushes code.
- **Evidence the reviews earn their keep**: across the ADR-0017/#84 PRs,
  21 findings — 14 fixed, 4 deferred into issues, 3 rejected with a reply
  and reasoning. That reject path matters: findings are advice a human
  disposes of, not verdicts. The public write-up is at
  site-customer, `src/content/blog/claude-code-reviews.md`
  (https://aeroflow-air.github.io/site-customer/engineering/claude-code-reviews/).
- **The known failure mode has already happened**: when Anthropic credits
  ran out (during the #69 work), reviews failed with a warning only and
  merges proceeded. The owner called that acceptable. That is the designed
  behaviour, not an accident — a required check would have blocked merges
  on a billing event.

Related, not the same thing: ADR-0012 labels AI **authorship**
(`ai-authored`) for ADR-0011 metrics and keeps AI **review** as the
separate `ai-reviewed` label, expressly not counted as AI-authored.

## Decision

**AI code review stays advisory, shared, and opt-in per repo. It is never
a required status check and never a merge gate.**

1. **One shared workflow, thin callers.** Reviews run only through
   `aeroflow-air/aeroflow-workflows/.github/workflows/ai-code-review.yml`,
   pinned by release tag (today v0.3.1, never `@main`) from a caller's
   `.github/workflows/ai-review.yml`. The shared prompt is the single
   review standard; a repo may append `extra-instructions` but not fork
   the prompt. Prompt or guard changes ship as a new aeroflow-workflows
   release and roll out by bumping the caller pin, so the org can see
   exactly which review version ran on a PR.
2. **Advisory means advisory.** The Claude step stays
   `continue-on-error: true`; failures surface as a warning annotation,
   never a red check, and the workflow must not be added to branch
   protection or rulesets as required. Claude comments, humans decide:
   every finding is fixed, deferred into an issue, or rejected with a
   reply — that three-way disposition, not acceptance rate, is the record
   of value. A PR with no AI review (skipped, failed, credits exhausted)
   is exactly as mergeable as one with it.
3. **Cost guards are platform defaults, not per-repo taste.** `max-turns`
   25, `max-changed-lines` 1,500, 15-minute timeout, `skip-ai-review`
   label honoured, drafts and synchronise storms contained by the
   per-PR concurrency group. A repo may tighten its own caller inputs;
   loosening them beyond these defaults is a platform decision in the
   shared workflow, not a local edit.
4. **Opt-in rollout.** A repo gets reviews by adding the thin caller —
   new `svc-*` repos inherit it from template-dotnet-service. The repos
   without it today (aeroflow-local, infra-platform, site-customer,
   platform-handbook) are a backlog item, not a silent exemption; until
   they opt in, they get human review only and nobody should claim
   otherwise. Fork PRs never get reviews: the job requires the head repo
   to be this repository, and fork PRs receive no secrets in any case.
5. **Spend and key ownership.** The org secret `ANTHROPIC_API_KEY`
   (name only; nobody reads its value) is the single key for all callers.
   Its owner is the platform owner: they hold the Anthropic account,
   watch credit balance, and rotate the key by replacing the org secret —
   rotation needs no repo change. There is no per-repo key and no budget
   split at this scale; unusual spend shows up as review volume per PR,
   which the guards in (3) already cap.
6. **Data handling.** What leaves GitHub is the PR diff, plus files
   Claude opens for context with its read-only tools, sent to the
   Anthropic API under that account's terms. All repos in this org are
   public, the reviewer gets no secret values (its tools cannot read
   repo secrets, and reviewers must keep it that way), and the workflow
   token swap (`id-token: write`) exists only so the action can mint a
   short-lived Claude app token. Nobody pastes anything into the review
   path that is not already in the PR.
7. **Relation to ADR-0012.** An AI review makes a PR `ai-reviewed` at
   most; it never makes it `ai-authored`, and it does not count in the
   ADR-0011 AI share. This workflow does not apply labels — authorship
   labelling remains the author-declared convention ADR-0012 describes.

## Consequences

- Reviews keep catching contract, docs and test gaps (14 of 21 pilot
  findings were worth fixing) at the price of per-PR Anthropic spend
  capped by turn/line/time guards. Noise is handled socially: reject
  with a reason, and the sticky comment keeps that visible.
- **Accepted outage mode**: when credits or the Anthropic API are
  unavailable, reviews degrade to a warning and development continues
  unreviewed-by-AI. That already happened once and was fine; the risk
  accepted is a quiet gap in review coverage, never a blocked merge.
  If the gap matters retrospectively, the fix is a human re-review, not
  a gate.
- One prompt to maintain, four (eventually more) pins to bump per
  release: rollout of a prompt change is deliberately a visible,
  per-repo PR, which is also its audit trail.
- Handbook and local-platform PRs currently get no AI review, so ADR
  quality rests on human review alone until the backlog closes — this
  record declines to pretend the pilot covers the org.
- The org depends on one vendor's action and model behaviour; a bad
  prompt or model change can raise noise across every repo at once.
  The pin-then-bump rollout is the brake.

## Alternatives considered

**Make the AI review a required status check.** Rejected: it would hand
merge control to a probabilistic reviewer and to Anthropic billing —
the credits outage would have blocked the #69 merges, which the owner
explicitly accepted as warning-only. It would also invite gaming the
reviewer instead of answering it. Revisit if the reviewer ever becomes
deterministic enough to state a narrow, checkable rule — at which point
that rule belongs in ordinary CI, not in an LLM check.

**Standalone per-repo workflows (copy the reusable workflow into each
repo).** Rejected: the pilot's value is one prompt evolving once; four
copies would drift the way the event contracts did before ADR-0019.
Revisit if a repo needs a fundamentally different review (for example a
non-.NET estate) that `extra-instructions` cannot express.

**A different or additional reviewer (Copilot review, or a second
model).** Rejected for now: no evidence the current reviewer misses a
class of problem a second one would catch, and two advisory voices
double noise and spend. ADR-0012's zero-cost rule for vendor metrics
applies in spirit. Revisit if a reviewer changes pricing/terms, or on
a measured miss — a merged bug the review saw and passed.

**No AI review (human only).** Rejected on the pilot evidence:
14 fixes and 4 filed issues from 21 findings is a yield human-only
review was not producing on the same PRs. Revisit if the fix rate
collapses — measure by dispositions for a month; if most findings are
rejected as noise, retire the workflow rather than letting it become
wallpaper.

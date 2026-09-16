# AeroFlow — platform handbook

## What this is

AeroFlow Air is a fictional company. This organisation is a portfolio piece: a
complete platform engineering department — service catalogue, golden paths,
governance, and the platform itself — built as evidence of platform design
capability. Nothing here serves real traffic.

Two consequences that matter when working in this repo:

- **The reasoning is the product.** A working thing with no record of why it is
  shaped that way is worth less here than a smaller thing with the rejected
  alternatives written down. Credibility comes from decision records that show
  what was turned down and why, not from breadth of catalogue.
- **Realistic scale, not enterprise scale.** Solve the problem a squad of six
  actually has. Anything that only makes sense at two hundred engineers is
  theatre and should be rejected in an ADR rather than built.

`platform-handbook` is the governance and documentation repo. Services,
libraries and infrastructure live in their own repositories.

## Organisation conventions

Repositories are prefixed by category — `svc-`, `lib-`, `infra-`, `template-`.
Repos that are part of the platform's own operation keep a bare descriptive
name (`platform-handbook`, `.github`, `aeroflow-workflows`). Names are
lowercase, hyphen-separated, and describe the business capability rather than
the technology: `svc-booking`, not `svc-booking-api-dotnet`. See ADR-0001.

Settled organisation settings, so they are not re-litigated:

- Default branch is `main`.
- Base member permission is **read** — everyone can see everything, teams grant
  write on what they own. Discoverability is the point of a catalogue.
- Default `GITHUB_TOKEN` permission is **read-only** org-wide. Every workflow
  declares the permissions it needs explicitly, at job level where possible.
  This is as much about legibility as security: a reader can see what each job
  is trusted with.
- Repositories are **public**. On the free plan, branch protection, rulesets and
  CODEOWNERS enforcement only apply to public repos — private repos fail
  silently, which would make the governance flow a claim rather than a fact.
- Repo-per-service. No monorepo.

## Stack decisions

| Area | Choice |
|------|--------|
| IaC | **Bicep**, with typed module contracts published as versioned OCI artifacts. Not Pulumi — see ADR-0002. |
| CI | GitHub Actions, with reusable workflows in `aeroflow-workflows`, referenced by tag |
| Runtime | Containerised. **No Kubernetes** — too much overhead for demonstrating platform interface concepts, and its failure modes leak through the abstraction to squads |
| Services | APIs, async/queues, database per service, a couple of React frontends |
| Service scaffolding | A template repo plus **small, independently versioned libraries** (health checks, OTel at startup, config binding, error middleware, ProblemDetails, structured logging) |

Deliberately excluded: Kubernetes, Dagger. Do not reintroduce them without an
ADR that supersedes the one rejecting them.

**Design test for anything shared:** can a squad delete the library and still
ship? If no, it is a framework, not a foundation — the same failure mode as an
over-abstracted pipeline. Prefer composition a squad can opt out of.

## Releases

Release from semantically versioned artefacts referenced by a release manifest.
Not release branches of pipelines. The manifest makes it unambiguous exactly
what versions are in a release.

## Design docs vs decision records

These are different artefacts and should not be merged:

- **Design docs** are forward-looking, squad-owned proposals. They argue. They
  can be long and they can change.
- **Decision records** are the terse residue: what was chosen, what was
  rejected, what it costs. One page, hard. Immutable once accepted.

## Decision record rules

Records live in `docs/decisions/`, named `<id>-<slug>.md` with a zero-padded
four-digit id. `_template.md` is the starting point.

Lifecycle: `draft → in-review → accepted | rejected`, and `accepted →
superseded`.

Once a record is accepted, rejected or superseded, **only `status` and
`superseded-by` may ever change**. Changed your mind? Write a new record with
`supersedes:` pointing at the old one; the old one stays exactly as written.
Every rejected alternative names the trigger that would make it worth
revisiting.

`scripts/validate-decisions.py` enforces all of this in CI — frontmatter shape,
unique ids matching filenames, legal status transitions, reciprocal supersession
links, and body immutability after a decision. It is intentionally
dependency-free stdlib Python: a repo-local lint with no runtime, not part of
any service, so it does not need to match the C#/Go estate. When changing the
rules, change the validator in the same PR.

## Project management

Work is tracked in a single **org-level GitHub Project**, not per-repo — most
meaningful work crosses repos. Few custom fields (Squad, Type, Status), status
transitions driven by built-in workflows on PR open and merge rather than by
hand. The choice of GitHub Projects over a dedicated tool is itself a recorded
decision: one system of record for the work item, the design doc, the decision
record, the PR and the deployment, with no integration tax.

## Working preferences

- Concrete and specific over abstract. First-step plans, not strategy decks.
- Name the trade-off. A recommendation with no stated cost is not finished.
- Push back on ideas that are more fun than useful — the failure mode for this
  project is elaborate scaffolding with an empty catalogue.
- Do not re-propose things already rejected in `docs/decisions/`. Read them.

## Open questions, not yet decided

- Does a new service need approval at all, or does governance belong at the
  deployment gate instead? This needs an ADR either way.
- Whether the audience is Head of Platform interviews (polish, narrative arc)
  or a sandbox for practices to bring back to day-job work. The two pull
  scope in different directions.
- A customer-facing site explaining the fictional company, with an engineering
  blog documenting each phase and its decisions — built on the platform's own
  architecture, so it doubles as a golden-path proof.

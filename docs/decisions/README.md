# Decision records — how the process works

This describes the whole flow: what a decision record is, how one gets written
and approved, and what CI enforces. It lives in the repo because the process is
part of the platform, not a wiki page beside it.

## What a decision record is

A decision record is the terse residue of a decision: what was chosen, what was
rejected, and what it costs. One page, hard.

It is not a design document. Design documents are forward-looking, squad-owned
proposals — they argue a case, they can be long, they change as the thinking
changes. A decision record is what survives the argument, and it stops changing
the moment it is accepted.

Both can exist for the same piece of work. The design doc links from the
record's `design-doc` field.

## Where records live

- **Organisation-wide decisions** — naming, permissions, the release model, the
  decision process itself — live in `platform-handbook/docs/decisions/`.
- **Service-local decisions** — anything that only constrains one service —
  live in that service's own `docs/decisions/`, same format, same lifecycle,
  reviewed by the squad that owns the code.

The test: would another squad have to read this to do their job? If yes, it
belongs in the handbook.

## File shape

Filename is `<id>-<slug>.md`, id zero-padded to four digits. `_template.md` is
the starting point and is ignored by the validator, as is anything else
prefixed with an underscore.

```yaml
---
id: 2                     # integer, must match the filename
title: Short noun phrase
status: accepted          # see lifecycle below
date: 2026-09-12          # ISO-8601, the date of the decision
deciders: ["@aeroflow-air/platform"]
supersedes: null          # id of the record this replaces
superseded-by: null       # id of the record that replaced this one
affects: ["all-repos"]
design-doc: null          # link, if there was one
---
```

Body sections, in order: **Context**, **Decision**, **Consequences**,
**Alternatives considered**. Every rejected alternative names the trigger that
would make it worth revisiting — that is what turns a dead end into a live
constraint rather than a closed door.

## Lifecycle

```
draft ──► in-review ──► accepted ──► superseded
  ▲           │              │
  └───────────┘              │
              └──► rejected ◄┘
```

Legal transitions, and nothing else:

| From        | To                            |
|-------------|-------------------------------|
| `draft`     | `in-review`, `rejected`       |
| `in-review` | `draft`, `accepted`, `rejected` |
| `accepted`  | `superseded`                  |
| `rejected`  | — terminal                    |
| `superseded`| — terminal                    |

`in-review → draft` exists so a reviewer can send something back. Everything
else moves forward only.

## The immutability rule

Once a record is `accepted`, `rejected` or `superseded`, **only `status` and
`superseded-by` may ever change**. Not the body, not the title, not the date,
not the deciders. Typos included.

Changed your mind? Write a new record with `supersedes: <old id>`, and set the
old record's `superseded-by` to the new id and its status to `superseded`. Both
sides of that link must agree. The old record stays exactly as written — the
value of the log is that it shows what you believed at the time.

## The flow, end to end

1. Copy `_template.md` to `docs/decisions/<next-id>-<slug>.md`, status `draft`.
2. Open a PR. Draft records can be pushed freely — CI checks the shape, not the
   content.
3. Move to `in-review` when it is ready to be argued with. CODEOWNERS review is
   required on `docs/decisions/`, so the owning team is pulled in automatically.
4. On agreement, flip to `accepted` in the same PR and merge.
5. To supersede later: a new PR containing both the new record and the two-field
   change to the old one. The validator rejects a one-sided link, so they cannot
   drift apart.

## What CI enforces

`scripts/validate-decisions.py`, run by `.github/workflows/validate-decisions.yml`
on pull requests touching `docs/decisions/`, and on push to `main`.

Static checks, always:

- frontmatter parses, and required keys are present and non-empty
- `id` is an integer, matches the filename, and is unique across the directory
- `status` is a known lifecycle value
- `date` is ISO-8601
- `supersedes` / `superseded-by` are reciprocal, both records exist, and a
  record with `superseded-by` set has status `superseded`

Diff checks, on pull requests only — these compare against the base branch, so
the workflow checks out with `fetch-depth: 0` and passes
`--base origin/${{ github.base_ref }}`:

- status transitions follow the table above
- a record that was `accepted`, `rejected` or `superseded` in the base branch
  has an unchanged body and unchanged frontmatter apart from the two mutable
  fields
- a new record is not created with status `superseded`

Run it locally the same way:

```bash
python3 scripts/validate-decisions.py                 # static checks only
python3 scripts/validate-decisions.py --base main     # plus diff checks
```

It is dependency-free stdlib Python and parses a deliberately small YAML subset
— scalars, quoted strings, inline lists, `null`. Anything outside that is
rejected rather than guessed at. This is a repo-local lint with no runtime, not
part of any service, which is why it does not match the C# estate.

## What CI deliberately does not enforce

Length, prose quality, whether the alternatives are real, whether the decision
is any good. Those are review's job. The validator protects the properties that
make the log trustworthy — identity, lifecycle, immutability — and nothing else.
Adding content linting here would be the same mistake as an over-abstracted
pipeline: automating the part that needs judgement.

## Wiring it up in a new repo

The validator is published as a reusable workflow in `aeroflow-workflows`, so a
service repo calls it rather than copying the script:

```yaml
jobs:
  decisions:
    uses: aeroflow-air/aeroflow-workflows/.github/workflows/validate-decisions.yml@v1
```

For it to actually gate anything, the check must be listed as required in the
repository ruleset, alongside required CODEOWNERS review. Without that it
reports and the merge proceeds regardless.

**Not built yet.** `aeroflow-workflows` is currently just a README — no
`validate-decisions.yml`, reusable or otherwise. `platform-handbook` runs
`scripts/validate-decisions.py` directly against its own `docs/decisions/`
(see above), which needs nothing from `aeroflow-workflows`. This reusable
wrapper only matters once a service repo actually has service-local
decisions to validate; build it then, against a real consumer, rather than
speculatively. The likely shape: a thin workflow that checks out
`platform-handbook` for the current script and runs it against the calling
repo's own `docs/decisions/`, so the script keeps one home and the "change
the validator in the same PR as this document" rule above still holds.

## When changing the rules

Change the validator in the same PR as this document. If the two disagree, the
validator is what is true, and that is the failure mode this whole flow exists
to prevent.

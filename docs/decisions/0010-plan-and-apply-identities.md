---
id: 10
title: Plan and apply are separate identities, and apply only happens in Actions
status: draft
date: 2026-09-28
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["aeroflow-workflows", "svc-*", "template-*"]
design-doc: null
---

## Context

ADR-0006 says only the shared deploy workflow deploys. Each squad's deploy
identity writes only to its resource groups, trusted by GitHub OIDC with
`job_workflow_ref` in the subject, and that binding is still "to confirm with
a real token". ADR-0009 runs the generated composition through that workflow.
Neither record splits planning a change from applying it.

Checked on 29 September 2026, none of this exists. `aeroflow-workflows` (tag
`v0.1.0`) holds `dotnet-ci.yml`, `validate-decisions.yml` and a self-test, and
no deploy workflow. No repo records an Azure identity or a federated
credential. The org has no custom OIDC subject template. `svc-flight-status`,
`svc-gate-allocation`, `template-dotnet-service` and `aeroflow-workflows` all
use the default immutable subject (`use_default` and `use_immutable_subject`
both true).

## Decision

**Plan and apply use different identities. On the route to live, apply
happens only in GitHub Actions, through the shared deploy workflow.**

- **Plan identity.** Read-only, and the only identity a pull-request workflow
  may assume, for what-if. It cannot create or change resources.
- **Apply identity.** Separate. Its federated credential trusts only the
  shared deploy workflow in `aeroflow-workflows`, at that workflow's `main`,
  which is the `job_workflow_ref` binding ADR-0006 already chose. A person or
  a laptop cannot apply on the route to live.
- **What that binding can and cannot say**, from GitHub's and Microsoft's
  docs, not from a token we have issued:
  - The default `sub` does not name a workflow file. It is the repository plus
    one of an environment, `pull_request`, or a ref. `job_workflow_ref` is a
    separate claim, set when a job calls a reusable workflow, of the form
    `org/repo/.github/workflows/file.yml@ref`.
  - A standard federated credential matches `sub`, issuer and audience
    exactly. It can require `job_workflow_ref` only if the subject template
    is customised to include that claim. This org has not customised it.
  - Flexible federated credentials, still in preview, can match
    `job_workflow_ref` with `eq` or `matches`, and for GitHub must also match
    `sub` and `repository_id` or `repository_owner_id` with `eq`. `subject`
    and `claimsMatchingExpression` cannot both be set. Azure CLI, PowerShell
    and Terraform do not support them; the portal, Microsoft Graph and ARM
    REST do. ADR-0006 already says this, and the docs still do.
  - Pinning `job_workflow_ref` to the workflow's `main` does not by itself
    stop a pull request from calling it: the caller's branch is the `ref`
    claim, not that one. Which of the two mechanisms to use, and how the
    caller's ref is bound, stays where ADR-0006 left it.
- **Bootstrap, once.** A human runs, and records, the registry (ACR), the
  OIDC identities, the AcrPull identities and the budget alert. After that
  the route to live has no local apply.
- **Sandboxes** stay as ADR-0006. They are not the route to live, so this
  apply rule does not cover them.

This adds to ADR-0006 and ADR-0009 and supersedes neither.

## Consequences

A pull request can be shown a plan and cannot ship it, once the identities
exist. They do not. The subject binding is still untested.

"Read-only" is the intent, not the built-in Reader role. Microsoft's what-if
docs say the operation has the same permission needs as a deployment, unless
validation is relaxed, and Reader does not include
`Microsoft.Resources/deployments/whatIf/action`. The exact role is open.

The bootstrap is a standing exception. If it is run again, the carve-out has
failed and this record needs revisiting.

Revisit if a real token cannot carry `job_workflow_ref` as ADR-0006 expects.

## Alternatives considered

- **One identity for plan and apply.** Rejected: a pull-request workflow could
  apply. Revisit if the two checks cannot be separated.
- **Humans apply locally on the route to live.** Rejected: it skips the
  workflow pin. Revisit if Actions cannot do a change the bootstrap does not
  cover.
- **Trust the caller's `workflow_ref` instead of `job_workflow_ref`.**
  Rejected: that file lives in the service repo, and a squad can edit it.
  Revisit if a reusable workflow in this org cannot request the token.

---
id: 0003
title: Infrastructure as code — Bicep platform modules with deployment stack lifecycle management
status: accepted
date: 2026-09-18
deciders: ["@aeroflow-air/platform"]
supersedes: 0002
superseded-by: null
affects: ["all-repos"]
design-doc: null
---

## Context

ADR-0002 established Bicep as the standard Infrastructure as Code language,
introduced typed module contracts, Azure Verified Modules (AVM), OCI-based
module distribution, PSRule validation, and deployment stacks.

Since adoption, the platform team has observed that typed contracts achieved
their goal of creating a clear interface between squads and platform
capabilities. Most infrastructure consumers interact with a small number of
approved platform modules and rarely need direct access to underlying resource
definitions.

However, the decision bundles several independent concerns into a single ADR:

- Choice of IaC language.
- Module distribution strategy.
- Contract definition approach.
- Validation and governance tooling.
- Resource lifecycle management.

As platform capabilities grow, lifecycle management has emerged as the most
important architectural concern because it directly affects the safe creation,
update and removal of infrastructure. The original ADR treats deployment stacks
as an implementation detail despite them being a key part of the operating
model.

This decision supersedes ADR-0002 to make deployment stack ownership and
lifecycle governance a first-class platform concern while preserving the
existing investment in Bicep, AVM and typed contracts.

## Decision

Infrastructure continues to be authored in **Bicep**.

Platform modules continue to be published as versioned OCI artifacts and remain
the preferred consumption interface for application teams.

The primary platform abstraction is now defined as:

> A versioned Bicep module deployed and governed through an Azure Deployment
> Stack.

Every production deployment must be associated with a deployment stack owned by
a clearly identified platform service, product or workload.

Deployment stacks are responsible for managing resource lifecycle, including:

- Resource creation.
- Resource updates.
- Resource deletion.
- Drift remediation.
- Controlled decommissioning.

Platform modules must define ownership metadata and standard tags to allow
resources to be traced back to a deployment stack and owning service.

Typed contracts, Azure Verified Modules and PSRule validation remain mandatory
implementation requirements.

## Consequences

The platform operating model becomes clearer.

Infrastructure is no longer viewed simply as templates that happen to deploy
resources. Instead, infrastructure is treated as a managed product with a known
owner and lifecycle.

Resource cleanup becomes more predictable because deletion behaviour is
explicitly governed by deployment stack ownership rather than relying on manual
processes.

Operational responsibility becomes easier to understand. Engineers can identify
which deployment stack owns a resource and determine the correct route for
change, investigation or decommissioning.

Some additional governance overhead is introduced. Teams must understand
deployment stack ownership and ensure ownership metadata remains accurate.

This decision does not materially change how squads consume infrastructure.
Existing platform modules remain valid.

## Alternatives considered

### Retain ADR-0002 unchanged

Rejected.

The original decision remains technically sound but combines multiple unrelated
architectural decisions into a single record. Lifecycle management deserves its
own explicit architectural focus.

### Adopt deployment stacks without platform module ownership requirements

Rejected.

Deployment stacks provide lifecycle control but not accountability. Ownership
metadata is required to support operational management at scale.

### Remove deployment stacks and rely on standard ARM deployments

Rejected.

This reintroduces manual lifecycle management and weakens the platform team's
ability to safely remove infrastructure.

### Revisit Pulumi or Terraform

Rejected.

Nothing has changed in the estate to justify reintroducing tools that require
state management. The Azure-only context remains unchanged and deployment
stacks continue to provide a simpler operational model.

---
id: 7
title: Service hosting on Azure Container Apps
status: in-review
date: 2026-09-28
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["infra-platform", "aeroflow-workflows", "svc-*", "template-dotnet-service"]
design-doc: null
---

## Context

ADR-0006 settles how squads deploy infrastructure and leaves hosting to its own
record. This is that record; the first service module, `container-app-service`,
is built on it.

Two .NET 8 HTTP APIs exist, `svc-flight-status` and `svc-gate-allocation`, both
from `template-dotnet-service`: one image each, port 8080, a `/health` endpoint.
Neither is deployed, nothing runs in Azure and no `.bicep` exists. A showcase on
one pay-as-you-go subscription sits idle most of the time, so idle cost matters
more than peak. The question is also real: much of the .NET estate this mirrors
runs on App Service, with a move to Container Apps likely.

## Decision

AeroFlow services are hosted on **Azure Container Apps**.

- **One environment to start.** A workload profiles environment (the default
  type) using only its built-in Consumption profile, in one subscription.
  Separate test and live environments come later, with their own record.
- **Scale to zero by default.** The default HTTP scale rule, `minReplicas: 0`.
  A service that can't take a cold start sets `minReplicas: 1` and pays for it.
- **Built-in ingress.** External HTTP ingress to the template's port, no load
  balancer or public IP of our own; internal ingress for internal-only services.
- **Revisions.** Single revision mode by default: a new revision takes traffic
  once ready; a failed one leaves traffic where it was. Multiple revision mode
  with traffic splitting is an opt-in module parameter.
- **Images pulled by managed identity.** A user-assigned identity with `AcrPull`
  on the platform registry. No admin user, no registry password.
- **Not adopted now:** Dapr, KEDA custom scale rules, Dedicated or Flexible
  profiles, our own virtual network. Each becomes a module option when needed.
- Names (organisation, prefix, registry) are parameters, never hard-coded.

## Consequences

Idle services cost little: no usage charges while scaled to zero, a monthly
free grant per subscription (180,000 vCPU-seconds, 360,000 GiB-seconds, 2
million requests), and no management fee without a Dedicated profile. The
registry has a daily rate per tier; Log Analytics bills separately.

The price is the cold start: after scaling to zero, the next request waits for
image pull, provisioning and app start. Learn asks for ASP.NET Core data
protection on .NET apps here; the template lacks it, so that changes first.

Pull identities and their `AcrPull` grants are made at bootstrap, since a
squad's deploy identity writes only to its own resource groups (ADR-0006); the
registry must allow ARM-audience tokens. Azure deletes an environment idle for
over 90 days; Learn doesn't say whether scaled-to-zero apps count as active, so
the runtime pipeline must be able to recreate it.

Deployment runs in four layers, only the first manual: a one-off bootstrap
(resource group, registry, GitHub OIDC identities, role assignments, budget
alert); modules published on tag, a release not a deployment; the environment
and Log Analytics from the planned `infra-platform` pipeline, probably as a
deployment stack; services from the shared workflow, using it as `existing`.

No Kubernetes API means no Helm charts or operators, which is the point. A
Consumption replica tops out at 4 vCPU and 8 GiB. Revisions are not App Service
slots, and that mapping is what the migration question needs. Revisit if cold
starts hurt more than `minReplicas: 1` costs, a service outgrows a Consumption
replica, or the idle-deletion policy bites.

## Alternatives considered

- **App Service.** Familiar, code or containers, deployment slots. Rejected:
  dedicated tiers bill every VM instance busy or not, so no scale to zero, and
  Free and Shared can't scale out; it would also dodge the migration question.
  Revisit if Container Apps friction outweighs that, or the estate it mirrors
  stays on App Service.
- **AKS.** Rejected: full Kubernetes, and on AKS Standard its operation is ours.
  AKS Automatic takes more on, but squads still meet Kubernetes, which the
  handbook excludes. Revisit if a workload needs the Kubernetes API.
- **Azure Functions.** Rejected for these services: a different programming
  model for template-built ASP.NET Core APIs. Right for event handlers, which
  can join the same environment. Revisit when the first handler arrives.
- **Container Apps on Dedicated profiles.** Rejected: a management fee and
  per-instance billing suit steady load we don't have. Revisit if steady load
  makes it cheaper, or a service needs more than a Consumption replica.

## References

- https://learn.microsoft.com/en-us/azure/container-apps/environment
- https://learn.microsoft.com/en-us/azure/container-apps/workload-profiles-overview
- https://learn.microsoft.com/en-us/azure/container-apps/scale-app
- https://learn.microsoft.com/en-us/azure/container-apps/cold-start
- https://learn.microsoft.com/en-us/azure/container-apps/revisions
- https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview
- https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull
- https://learn.microsoft.com/en-us/azure/container-apps/billing
- https://learn.microsoft.com/en-us/azure/container-apps/compare-options
- https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans
- https://learn.microsoft.com/en-us/azure/container-registry/container-registry-skus

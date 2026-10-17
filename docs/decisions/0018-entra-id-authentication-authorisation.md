---
id: 18
title: Authentication and authorisation with Entra ID app roles
status: draft
date: 2026-10-17
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "template-dotnet-service", "platform-handbook"]
design-doc: null
---

## Context

Every AeroFlow HTTP API is anonymous today. That was fine while they were
read-only, but the first write endpoint — `POST
/flights/{flightId}/reclaim/complete` in svc-baggage-reclaim, left out of #69
for exactly this reason — cannot ship unauthenticated. Issue #51 asks for one
shared identity model so each service does not roll its own.

Constraints that shape the choice:

- **No Azure deployment yet.** The owner is deliberately keeping the platform
  local-only (Aspire, ADR-0014) to avoid Azure cost, so auth must work at home,
  offline, in tests, with no tenant and no deployed resources.
- **Realistic scale** (see CLAUDE.md): one developer, a handful of services.
  Anything that only makes sense at two hundred engineers is theatre.
- Services already return RFC 7807 ProblemDetails with a stable `code`
  (ADR-0004), and event publishing is reliable via the store outbox
  (ADR-0017). Auth should slot into those edges, not change the domain:
  authorisation is an HTTP-edge concern, domain commands stay pure and
  caller-agnostic.
- Service docs still mention Keycloak as a placeholder ("waits for Keycloak",
  an unused `identity` reference in the AppHost). Nothing implements it; it was
  never decided, just named. This record replaces that placeholder.

## Decision

**Microsoft Entra ID is the identity provider. Each service is an app
registration, exposes app roles, and validates JWT bearer tokens itself on
every request.**

- **App roles, not scopes, for service APIs.** Each registration defines roles
  for the actions its service owns — first example: `Ops.Reclaim.Write` on
  svc-baggage-reclaim, required by `POST /flights/{flightId}/reclaim/complete`.
  Roles are assigned to users/groups (and later to client apps) in Entra;
  services check the `roles` claim through a named ASP.NET Core authorisation
  policy, never by parsing tokens by hand.
- **Per-service JWT validation.** ASP.NET Core JWT bearer via
  `Microsoft.Identity.Web`: issuer, audience, signing key, lifetime and role
  claims are checked in the service on every request. There is no gateway in
  front making this decision for it (see APIM below). Failures use the standard
  401 (no/invalid token) and 403 (valid token, missing role) responses; domain
  failures keep the existing ProblemDetails shape with `code`.
- **People sign in through Entra; services use managed identities.** Human
  callers (ops users, the Blazor dashboard acting for a user) get tokens from
  Entra. When services later call each other or Azure resources (Service Bus,
  Storage, Key Vault) in Azure, they use managed identities and Entra tokens —
  no client secrets in configuration.
- **Local dev and tests use a fake auth handler.** A development-only
  authentication handler (registered only when `Auth:UseFake` is set, which
  Development and tests set) accepts a simple test token/header and mints the
  same claims, including roles. The Aspire home setup and the test suite run
  fully offline; tests cover authorised, unauthenticated (401) and wrong-role
  (403) callers. Fake auth is never registered outside Development/tests, and
  the real Entra path needs only configuration (`AzureAd` tenant/client ids)
  when a tenant exists.
- **Read endpoints stay anonymous for now.** `GET` endpoints and `/health`
  keep working unauthenticated locally, as today. Requiring roles for reads is
  a later, separate decision per service; this record only gates writes.

## Consequences

- The reclaim-complete endpoint can ship now, locally, with real authorisation
  semantics and tests, at **zero cost**: Entra ID app registrations and token
  issuance are free at this scale, and none of this needs anything deployed to
  Azure. A free Entra tenant on a personal Microsoft account is enough when
  the real token path is exercised.
- Every service repeats a small, identical auth setup. Per the ADR-0004
  extraction rule, that setup moves into `template-dotnet-service` (the #51
  follow-up) once the pattern is proven in svc-baggage-reclaim, rather than
  being abstracted up front or copied a third time.
- Defence in depth stays possible later: internal traffic remains private
  inside the Container Apps environment (ADR-0007) and only the dashboard is
  exposed, but no service relies on network position for authorisation.
- Two auth modes (fake locally, Entra in Azure) must stay behaviourally
  identical from the policies' point of view — same claim types, same role
  names — or local tests stop proving anything. The fake handler therefore
  mints claims, not shortcuts around policies.
- The Keycloak placeholder in service docs and the AppHost `identity`
  reference are now stale; docs are updated as each service adopts this, and
  aeroflow-local should drop or repoint the reference when it next changes.

## Alternatives considered

**Azure API Management (APIM) as the auth front door.** Rejected for now:
APIM can validate tokens, but its real value is rate limiting, versioning,
one public URL and API products for external consumers — none of which a
local-only, single-developer platform needs yet, and it adds cost and a
second policy surface to learn. Per-service validation is the zero-trust
baseline and stays necessary even with a gateway. Revisit when an API is
exposed publicly to consumers outside the platform, at which point APIM (or
Front Door) becomes a platform capability in front of — not instead of —
per-service checks.

**Keycloak (self-hosted).** Rejected: it was only ever a placeholder name.
Running an identity provider is operational work Entra makes unnecessary,
and it would teach less-transferable skills than the Microsoft stack this
portfolio targets. Revisit if a future non-Azure host (for example the
deferred local-Kubernetes rebuild) needs a provider Entra cannot serve.

**Shared-secret / API-key headers.** Rejected: no identity, no roles, secrets
to distribute and rotate by hand — it would have to be replaced before any
real deployment, so it proves nothing. Revisit never for write endpoints.

**Defer the write endpoint until Azure deployment.** Rejected: it couples a
code decision to a spending decision. The endpoint, its policy and its tests
are all buildable and reviewable locally today; only token issuance waits
for a tenant. Revisit if the fake-handler tests drift from real Entra
behaviour in a way that hides a bug.

---
id: 15
title: API documentation with OpenAPI and Scalar
status: draft
date: 2026-10-10
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["svc-*", "template-dotnet-service", "aeroflow-workflows", "aeroflow-local"]
design-doc: null
---

## Context

Each HTTP service exposes its own API, but nothing says how it's documented.
Until now, Swashbuckle (spec plus Swagger UI) was what you got by default.
Microsoft dropped it from the .NET 9+ templates in favour of the built-in
`Microsoft.AspNetCore.OpenApi` generator, which has no UI of its own. Our
service estate is .NET 8 today (no built-in generator) and will move to .NET 9+
later. `aeroflow-local`, including the flight simulator, targets net10.0
(aeroflow-local#20, open) and is the first project on the net9+ path.
Without a shared rule, each squad will pick a different generator, URL and UI.
Consumers of `svc-*` APIs, the ops dashboard and the planned flight simulator
need consistent, browsable docs. Local runs through Aspire (ADR-0014) should
make every service's docs one click away.

## Decision

**Every HTTP service publishes an OpenAPI 3 document at `/openapi/v1.json`
and a Scalar UI at `/scalar`, gated by the `ApiDocs:Enabled` setting.**

- **Spec generation.** On net8 the spec comes from Swashbuckle
  (`Swashbuckle.AspNetCore.SwaggerGen` + `Swashbuckle.AspNetCore.Swagger`
  only, with no Swagger UI package), with the route template set to
  `openapi/{documentName}.json`. On net9+ it comes from the built-in
  `Microsoft.AspNetCore.OpenApi` (`AddOpenApi` / `MapOpenApi`), which serves
  the same URL by default. Moving up a framework version changes the generator,
  not the contract.
- **Build-time export (net9+ only).** A project on the built-in generator also
  sets `OpenApiGenerateDocuments` and `OpenApiDocumentsDirectory` so that
  `Microsoft.Extensions.ApiDescription.Server` writes the document to the
  repo-root `openapi/<name>.json` on every build. The export runs the app's
  startup, including hosted services, so anything needing an external service
  (a message bus client and its worker, for example) is skipped when the
  entry assembly is `GetDocument.Insider`. A test compares the file with the
  live `/openapi/v1.json`, ignoring the request-derived `servers` entry. The
  built-in generator is registered unconditionally and only its endpoints
  and Scalar are gated by `ApiDocs:Enabled`, which lets the export work with
  docs off. ADR-0024 reads these files for the Backstage catalogue.
- **UI.** `Scalar.AspNetCore` (`MapScalarApiReference`) at `/scalar`, reading
  `/openapi/v1.json`.
- **Content is required.** Projects set `GenerateDocumentationFile`. Controller
  actions (or minimal-API endpoints) and request/response models carry XML doc
  comments, including `<param>` and `<response>`. Every action declares its
  responses with `ProducesResponseType`, ProblemDetails included. The document
  sets a title, a version (`v1`) and a description. CS1591 may be suppressed so
  undocumented internal or domain types don't break warnings-as-errors builds,
  but public API surface is documented.
- **Exposure.** `ApiDocs:Enabled` is `true` in `appsettings.Development.json`
  and `false` (or absent) in `appsettings.json`. So docs are on locally and
  under Aspire, and off in Production by default. Turning them on in another
  environment is an explicit config change (`ApiDocs__Enabled=true`), not a
  code change.
- **Tests.** Each service has a test that `GET /openapi/v1.json` returns 200
  and lists its expected paths.

Reference implementations on net8 (Swashbuckle, spec served at runtime only):
[svc-flight-status#7](https://github.com/aeroflow-air/svc-flight-status/pull/7)
and
[svc-gate-allocation#5](https://github.com/aeroflow-air/svc-gate-allocation/pull/5).
On net10 (built-in generator, build-time export, Scalar, no Swashbuckle): the
flight simulator in
[aeroflow-local#20](https://github.com/aeroflow-air/aeroflow-local/pull/20).
The three `svc-*` services stay on net8 with Swashbuckle until they move.

## Consequences

Zero cost: every package is free and open source (MIT), and nothing is hosted.
Every service's docs live at the same two URLs, so tooling (Aspire links, a
future portal, client generation) can rely on them. Requiring XML comments and
`ProducesResponseType` adds a little friction per endpoint, but it also keeps
the response contract honest. Production exposes no docs surface unless someone
opts in.

Costs: on net8, one extra dependency (Swashbuckle) that has to be swapped out
when each service moves to net9+. On net9+ the build runs the app's startup
once per build to write the file, and the startup must tolerate that. Scalar releases often, so versions need
Dependabot or regular bumps.

Follow-ups:
- add the setup to `template-dotnet-service`, so new services start compliant
- add a CI step in `aeroflow-workflows` that builds the app and checks that the
  spec generates (and later, diffs it for breaking changes)
- possibly publish specs centrally later (see the portal alternative below)

## Alternatives considered

**Swagger UI (Swashbuckle's UI).** Rejected: it's dated and slower to browse,
and it ties the UI to Swashbuckle, which we only keep for net8 spec
generation. Revisit if Scalar stops being maintained or changes its licence.

**ReDoc.** Rejected: good for reading, but it has no built-in "try it" request
console, which squads want during local development. Revisit if we publish
read-only public API docs, where ReDoc's layout is a good fit.

**No docs (README endpoint lists only).** Rejected: the lists go stale, can't
be machine-read, and give consumers no schemas. Revisit never while services
expose HTTP APIs to other squads.

**Central docs portal (aggregate every spec in one site).** Deferred rather than
rejected: it needs hosting, auth and a publishing pipeline, which isn't worth
it for the number of services we have now. Per-service `/openapi/v1.json` is
the input such a portal would use anyway. Revisit when more than a handful of
services exist, or external consumers need docs without running anything.

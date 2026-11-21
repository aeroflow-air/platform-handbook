# Agent context audit (21 Nov 2026)

Appendix to [ADR-0023](../decisions/0023-central-agent-skills.md). This is a snapshot of `main` in all 11
`aeroflow-air` repos. It searched for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`,
`.github/instructions/`, `.github/skills/`, `.claude/`, `.agents/`, `.cursor/rules`, `.cursorrules`
and `.windsurfrules`. Only `CLAUDE.md` exists, in 6 repos.

## Findings by file

**[platform-handbook/CLAUDE.md](../../CLAUDE.md)**
- Accurate: naming (ADR-0001), org settings, Bicep/ADR-0006, ADR lifecycle and immutability (this matches
  `docs/decisions/README.md` and the validator).
- Outdated: the "Service scaffolding" row lists separate libraries for health checks, OTel, config binding,
  error middleware, ProblemDetails and structured logging. In reality there is one package,
  `AeroFlow.ServiceDefaults` (OTel, health, logging, analysers). ProblemDetails mapping and options binding are
  hand-written in each service.
- Not true yet: "a couple of React frontends" (the site is Astro, the dashboard is Blazor Server per
  ADR-0016), "database per service" (every store is in-memory), and "release manifest" (none exists).
- Missing: ADR-0022 / ServiceDefaults, ADR-0013/0017/0019 event rules, `aeroflow-workflows` pinning.
- "One page, hard": ADRs 0012, 0013, 0019, 0020 and 0022 run to 170–194 lines.

**svc-gate-allocation, svc-flight-status, svc-baggage-reclaim `CLAUDE.md`**
- Accurate against the code: the `Domain/` layout, `Result`/`Option`, outbox + `EventIds` (gate, baggage),
  idempotency through stored event ids, the auth policy at the edge (baggage), and `[LoggerMessage]` ids from 10,000.
- Duplicated: the 12-line "Conventions" block is near-identical in all three and the template, and restates
  [coding-standards.md](../standards/coding-standards.md).
- Soon stale: "local package feed in `lib/packages/`". `nuget.config` says to "swap ... when an org feed
  exists", and the feed now exists (lib-service-defaults `v0.1.0`).
- Stale linked docs: `docs/service-defaults.md` (byte-identical in all three and the template) says "There is no
  `lib-*` repo and no NuGet feed" and "Existing `svc-*` services are a later follow-up". `lib/README.md`
  says the same about the feed.
- flight-status: there is no `ProblemResults.cs`. Mapping is inline in `FlightsController`, a third variant.

**[template-dotnet-service/CLAUDE.md](https://github.com/aeroflow-air/template-dotnet-service/blob/main/CLAUDE.md)**
- It describes the `Domain/`, `Errors.cs` and `Result`/`Option` shape, but the template has none of these (only the
  `BookingsController` demo). It does point at svc-gate-allocation, which is the right call.
- Silent on `src/AeroFlow.ServiceDefaults*`, a full in-repo copy of the library. Its csproj and README already
  differ from lib-service-defaults, and the README still says to use a project reference until a feed exists.

**[lib-service-defaults/CLAUDE.md](https://github.com/aeroflow-air/lib-service-defaults/blob/main/CLAUDE.md)**
- Accurate: event id ranges, CA1848/CA2254/RS0030 via `build/` props, `BannedSymbols.txt` (Console and
  `Debug.WriteLine`), release by tag. This is the model for "short".

**[aeroflow-workflows ai-code-review.yml](https://github.com/aeroflow-air/aeroflow-workflows/blob/main/.github/workflows/ai-code-review.yml) prompt**
- It asks for "minimal API conventions", but no service maps minimal APIs (all use controllers).
- It points to "the repo's CLAUDE.md", which aeroflow-local, aeroflow-workflows, infra-platform and site-customer lack.
- It knows nothing about ServiceDefaults, event ids, readiness/liveness or options validation.

**Other docs agents follow**
- [docs/decisions/README.md](../decisions/README.md) shows `validate-decisions.yml@v1` and says it is
  "not tagged yet". aeroflow-workflows tags run `v0.1.0`…`v0.6.0` and there is no `v1`.

## Standards in code but not in agent context

| Standard | Where it lives today |
|----------|----------------------|
| ProblemDetails 400/404/409 + `code` | `Controllers/ProblemResults.cs` (gate, baggage), inline (flight-status); `AddProblemDetails` + `UseExceptionHandler` in every `Program.cs` |
| Options binding | `Configure<T>(GetSection(...))` with no validation in all three services and aeroflow-local |
| Health | `/health` + `/alive` from ServiceDefaults with only a `self` check; `HealthEndpointTests` in each service |
| Tests | xUnit, `Microsoft.AspNetCore.Mvc.Testing`, contract tests under `tests/*/Contracts`, `ObservabilityContractTests` |
| Toolchain | `net8.0`, `Nullable`, `TreatWarningsAsErrors`, `AnalysisLevel latest` in every `Directory.Build.props` |
| Pins | Services and template pin `aeroflow-workflows@v0.5.0`. `v0.6.0` is out and needs `packages: read` |

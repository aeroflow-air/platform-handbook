---
id: 21
title: C# file-based app as a second workload generator
status: draft
date: 2026-10-31
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["aeroflow-workflows"]
design-doc: null
---

## Context

ADR-0009 made a service's root `workload.yaml` the paved-road contract
for infrastructure. A generator in `aeroflow-workflows` turns that
manifest into Bicep that calls infra-platform's `container-app-service`
module. The generated file is a build artifact, not committed to the
service repo.

The first generator, `generator/generate.py`, is a Python script. It
reuses the same pinned `jsonschema` and PyYAML stack as the schema lint,
and Python is already on GitHub-hosted runners, so there is no extra
SDK or build step. The people who change AeroFlow services, and who
would change the generator, write C#. A Python-only generator is harder
for that team to read and patch with confidence.

On 31 October 2026 the generator was ported to a .NET 10 file-based
app, `generator/generate.cs`: one file, no `.csproj`, packages declared
with `#:package` directives (YamlDotNet 18.1.0 and JsonSchema.Net
9.6.0). It keeps the same CLI, the same schema file, the same rules and
rule-error messages, and the same output template. Pull request
[aeroflow-workflows#12](https://github.com/aeroflow-air/aeroflow-workflows/pull/12)
merged that port to `main` on 12 November 2026. The deploy workflow was
not switched: `workload-deploy.yml` still defaults to Python, and
callers may opt in with `generator: csharp`. The .NET 10 SDK is
installed only when that input is set. Both implementations must pass
the shared golden files byte for byte (`tests/generator/run_csharp_golden.sh`
runs in the self-test). Python remains the source used to refresh those
files.

This record does not change ADR-0009. It records how the generator is
implemented, not what a service declares.

## Decision

**The workload generator has two implementations: Python
(`generate.py`), which remains the default, and C# (`generate.cs`), a
.NET 10 file-based app. Both must produce byte-identical Bicep against
the shared golden files.**

- **Default.** `workload-deploy.yml` keeps `generator: python` as the
  default, so existing callers do not change. A caller opts into C# with
  `generator: csharp`.
- **Shape.** The C# port is a single file-based app, run with
  `dotnet run generator/generate.cs`. It needs the .NET 10 SDK, not
  only the runtime. If it outgrows one file,
  `dotnet project convert generator/generate.cs` turns it into a
  normal project.
- **Parity.** The self-test runs the Python unit and golden-file tests
  and the C# parity script. A change that makes the two outputs differ
  fails CI. Schema-error wording may differ because it comes from
  JsonSchema.Net rather than Python's `jsonschema`; failing paths and
  exit code 1 stay the same.
- **Later choice.** After the C# path has been watched green in CI, a
  separate decision will pick one default and retire the other, so
  there is one schema stack again. That switch is not made here.

## Consequences

C# developers can read and change the generator in the language they
already use, without a project file to maintain.

There are two implementations and two schema stacks to keep in step.
Golden files are still refreshed from Python. The first `dotnet run`
restores and builds (a few seconds); later runs reuse the SDK build
cache. Python has no build step. Runners that choose C# need the
.NET 10 SDK.

The port is on `aeroflow-workflows` `main` as of #12. It is not in a
tagged release yet (latest tag is `v0.4.0`, 18 October 2026). Callers
pin tags, so they do not see the new input until a later tag is cut
and they move their pin.

## Alternatives considered

**Python only.** Rejected: the team that has to change the generator
writes C#, and a second language in this path slows them down. Revisit
if the C# port drifts from Python or the SDK cost on runners is too
high.

**Switch the deploy default to C# in the same change.** Rejected: the
port needed to land and stay green first, and existing callers should
not change until we choose a default on purpose. Revisit once the C#
path has been watched green in CI.

**A multi-file `.csproj` console app from the start.** Rejected: a
file-based app keeps the single-script shape of `generate.py` and
avoids a project file for a small generator. Revisit if the file
grows past a comfortable size (the convert command above is the
escape hatch).

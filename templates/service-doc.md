<!--
Service doc template (platform-handbook docs/standards/service-docs.md).
Copy to docs/service.md in the service repo. Keep every heading; write "None"
rather than deleting a section, so a reader can tell "nothing" from "forgot".
Describe what the code does today, not what is planned. Link the code.
-->

# <service-name>

> One sentence: what this service is responsible for, in business terms.

| | |
| --- | --- |
| Repo | `aeroflow-air/<repo>` |
| Owner | <squad> |
| Status | <prototype / local-only / deployed> |
| Runs in | <aeroflow-local AppHost resource name, hosting target> |
| Last reviewed | <YYYY-MM-DD> |

## Purpose

What problem it solves, what it owns (its data and its topic), and what it
deliberately does **not** do.

## Design decisions

Service-level choices and the reason for each. Link platform ADRs this service
follows; record anything service-specific here (or in an ADR if it binds other
services).

| Decision | Why | Link |
| --- | --- | --- |
| | | |

## Architecture

Main components (domain, messaging, storage, API) and how a request or event
flows through them. A small Mermaid diagram is welcome.

## Inputs

### HTTP API

| Method | Route | Purpose | Responses |
| --- | --- | --- | --- |
| | | | |

Where the OpenAPI document and Scalar UI live, and how errors are shaped.

### Events consumed

| Topic | Subscription | Event types handled | Effect | Ignored |
| --- | --- | --- | --- | --- |
| | | | | |

Contract source (shared package or local copy, and which upstream type).

### Configuration

| Setting | Default | Meaning |
| --- | --- | --- |
| | | |

## Outputs

### Events published

| Topic | Event type | When | Payload fields |
| --- | --- | --- | --- |
| | | | |

Message conventions (`MessageId`, `Subject`, `CorrelationId`, content type).
Write "None" if the service publishes nothing.

### Other side effects

State it owns, files, calls to other services.

## Dependencies

| Dependency | Needed for | Behaviour when absent |
| --- | --- | --- |
| | | |

## Failure modes

How the service fails and how you would notice. One row per failure.

| Failure | How it shows up | Impact | What to do |
| --- | --- | --- | --- |
| | | | |

Delivery semantics: at-least-once? idempotent? what is dead-lettered and why?

## Running and testing

- Standalone: `dotnet run ...`, which endpoints to hit.
- With the airport: aeroflow-local AppHost steps.
- Tests: `dotnet test`, and what the suites cover.
- What to look for in logs to know it is working.

## Known gaps

Things that are knowingly missing or wrong, each with an issue link.

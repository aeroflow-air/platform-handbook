# Catalogue: org-level entities

Backstage entities that belong to the organisation rather than to one repo
([ADR-0024](../docs/decisions/0024-backstage-service-catalogue.md)):

| File | Entities |
| --- | --- |
| `domains.yaml` | Domains `airport-operations`, `platform-engineering` |
| `systems.yaml` | Systems `airport`, `developer-platform`, `public-site` |
| `resources.yaml` | Resource `event-bus` (ADR-0013, local emulator only) |

The handbook's root `catalog-info.yaml` holds a `Location` that points here, so
the instance's GitHub discovery finds these files without extra configuration.

Groups and Users are **not** defined here. The `githubOrg` provider imports the
real GitHub teams (`platform`, `squad-checkin`) and members, and a hand-written
Group with the same name would clash with them.

Each repo describes itself in its own root `catalog-info.yaml`. Add a Domain,
System or shared Resource here only when a repo needs to point at it.

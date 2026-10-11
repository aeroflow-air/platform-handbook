# LinkedIn: Services declare, the platform builds

| | |
|---|---|
| **Title** | Services declare, the platform builds |
| **Date** | 11 Oct 2026 |
| **Status** | draft, not yet published |
| **Related** | [Design: workload manifest platform](../design/workload-manifest-platform.md), [ADR-0009](../decisions/0009-workload-manifest.md), [ADR-0006](../decisions/0006-governed-bicep-modules-only.md), [blog post PR (site-customer #21)](https://github.com/aeroflow-air/site-customer/pull/21) |

**LinkedIn post:** [Published 11 Oct 2026](https://lnkd.in/p/efgTZbbU)

---

At scale, standards and consistency are key. So on AeroFlow, a service no longer writes its own infrastructure.

It declares what it needs in a five-line workload.yaml: "I'm an internal HTTP service". A generator in CI turns that into Bicep built only from governed modules, so naming, tags, identity and logging are applied once, in the platform, not remembered in every repo. The service's infra folder is just a README.

Services pin a tagged release of the generator, so a change rolls out one service at a time, in each service's own PR.

The honest trade-offs: the generator is a shared dependency, squads only get the capabilities on offer, and reviewers see YAML rather than resources until what-if runs on PRs.

Why not Kratix, Score or Radius? AeroFlow is Azure Container Apps only, with no Kubernetes, so a CI generator costs nothing and needs nothing always on. Azure bill so far: £0.

Where do you draw the line between a paved road and a side door?

The full write-up: https://aeroflow-air.github.io/site-customer/engineering/services-declare-the-platform-builds/

#PlatformEngineering #Azure #Bicep

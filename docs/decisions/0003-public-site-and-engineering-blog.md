---
id: 0003
title: Public site and engineering blog on GitHub Pages
status: draft
date: 2026-09-20
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["www"]
design-doc: null
---

## Context

AeroFlow Air is a fictional company whose real product is the platform
engineering story: decision records, golden paths, reusable CI, and Azure-native
IaC. That story currently lives in GitHub repositories that a hiring manager or
curious engineer will not casually browse end-to-end.

An open question in the handbook is whether the audience is Head of Platform
interviews (narrative arc, polish) or a sandbox for practices to bring back to
day-job work. A public site can serve both: a short customer-facing face for the
airport domain, and an engineering blog that documents each platform phase with
links back to the decision records that justified it.

The site must stay cheap to host and honest about what it is. It should not
become a second handbook, and v1 should not require Kubernetes or a custom
Azure hosting path before the platform's own golden path is ready to prove it.

## Decision

We publish a **public product website and engineering blog** for AeroFlow Air.

- **Repository:** `www` (bare descriptive name; organisation-owned, public).
- **Hosting:** **GitHub Pages**, deployed by GitHub Actions from `main`.
- **Stack:** **Astro** with content collections for blog posts (Markdown/MDX).
  Static output only for v1.
- **Information architecture:** a small customer-facing home (fictional product),
  an Engineering section for the blog, and a Platform page that **links into**
  `platform-handbook` rather than copying ADRs. Blog posts may summarise a phase
  and must cite the relevant decision record by link; the handbook remains the
  source of truth for decisions.
- **Dogfooding later:** promoting the site onto the platform's own container /
  Bicep golden path is allowed only via a later ADR. v1 deliberately stays on
  Pages so the portfolio ships narrative without waiting on infra modules.

## Consequences

The portfolio gains a single URL that explains the fictional company and walks
a reader through platform work chronologically. Interviewers and peers can read
the blog without cloning repos.

What this costs: another repository to maintain, a content cadence expectation
once posts exist, and discipline to avoid duplicating the handbook. Astro and
Pages are another toolchain for a platform team of one — accepted because the
site is static and the deploy surface is one Actions workflow.

What becomes harder: treating the blog as a design doc dump. Posts that argue
unsettled design belong in design docs or draft ADRs first; the blog narrates
accepted (or deliberately experimental) work.

## Alternatives considered

**Docusaurus.** Rejected for v1. Strong for a docs portal; weaker fit for a
short product face plus narrative blog. Revisit if the site becomes primarily a
documentation hub and marketing pages shrink to near zero.

**Hugo.** Rejected. Excellent static performance and Markdown workflow, but
Astro's component model and content collections are a better default for a
small product+blog site with occasional custom UI. Revisit if the site stays
almost entirely Markdown with no component needs and build speed becomes a
pain.

**Azure Static Web Apps / Container Apps from day one.** Rejected. Valuable as
later dogfooding of the Azure-native path, but it couples the portfolio's first
public face to infra modules that are not yet the golden path. Revisit when
Bicep/AVM modules and a service template can host a static or SSR site without
theatre — then supersede hosting with a new ADR if Pages is left behind.

**Notion, GitBook, or an external CMS.** Rejected. Splits the system of record
away from GitHub (where ADRs, PRs, and Actions already live) and adds an
integration tax. Revisit only if non-engineer authors must publish without PRs
and that need outweighs a single GitHub workflow.

**No public site — handbook and READMEs only.** Rejected. Fine for internal
operators; weak for the interview and narrative goals already named in the
handbook. Revisit if the portfolio audience collapses to "operators reading
repos" only.

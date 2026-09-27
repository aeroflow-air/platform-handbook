---
id: 0003
title: Public site and engineering blog on GitHub Pages
status: accepted
date: 2026-09-20
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["site-customer"]
design-doc: null
---

## Context

AeroFlow Air is a fictional company whose real product is the platform
engineering story: decision records, golden paths, reusable CI, and Azure-native
IaC. That story currently lives in GitHub repositories that a hiring manager or
curious engineer will not casually browse end-to-end.

An open question in the handbook is whether the audience is Head of Platform
interviews (narrative arc, polish) or a sandbox for practices to bring back to
day-job work. A public site can serve both: a short public face that introduces
the fictional company and its airport domain, and an engineering blog that
documents each platform phase with links back to the decision records that
justified it.

The site must stay cheap to host and honest about what it is. It should not
become a second handbook, and v1 should not require Kubernetes or a custom
Azure hosting path before the platform's own golden path is ready to prove it.

## Decision

We publish a **public website and engineering blog** for AeroFlow Air.

- **Repository:** `site-customer` (organisation-owned, public). Any further
  public sites follow the same `site-<purpose>` pattern. ADR-0001's category
  prefixes do not cover websites, so this record adds `site-` for them. Decided
  on 2026-09-21; the first draft of this record said `www`.
- **Hosting:** **GitHub Pages**, deployed by GitHub Actions from `main`. The
  site is a project site at `https://aeroflow-air.github.io/site-customer/`, so
  it builds with the base path `/site-customer/`.
- **Build check:** every pull request runs `pr-build` (`npm install` and
  `npm run build`), and `main` requires it to pass before merge.
- **Stack:** **Astro** with content collections for blog posts (Markdown/MDX).
  Static output only for v1.
- **Information architecture:** a home page that introduces the platform, links
  to what is actually built, and presents the fictional airport as the problem
  space rather than as shipped product; an Engineering section for the blog
  under `/engineering/`; and a Platform page that **links into**
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

---
id: 0001
title: Repository naming convention
status: accepted        # draft | in-review | accepted | rejected | superseded
date: 2026-09-11        # date of the decision, not of the draft
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos"]  # services or domains, for portal filtering
design-doc: null        # link, if this came out of a proposal
---

## Context

The org has crossed the point where repository names alone no longer
convey what a repository is or who owns it. New repositories are
created weekly, discovery still runs through the GitHub org list, and
a mixed bag of ad hoc names makes that list unscannable. We need a
convention now, before the count grows further and renaming becomes
disruptive.

## Decision

We will prefix repositories by category: `svc-`, `lib-`, `infra-`,
`template-`. Present tense, active voice, one paragraph.

## Consequences

The org list becomes scannable and sortable by category without
tooling, and new repositories get an unambiguous home for their name
from day one. The cost is migration: existing repositories keep their
current names until they are next touched, so the convention will be
inconsistently applied for a transition period, and renaming a
repository breaks existing clone URLs, CI references, and bookmarks
for anyone who doesn't update them.

## Alternatives considered

**GitHub custom properties.** Rejected because ruleset targeting on
properties is plan-gated and a property is invisible in a clone URL.
Revisit if the taxonomy exceeds four categories.

**No convention.** Rejected because the org list is the catalogue
until the portal exists.

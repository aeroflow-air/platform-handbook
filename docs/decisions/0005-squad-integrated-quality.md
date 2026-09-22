---
id: 5
title: Quality skill lives in the squad, not a QA department
status: draft
date: 2026-09-22
deciders: ["@aeroflow-air/platform"]
supersedes: null
superseded-by: null
affects: ["all-repos"]
design-doc: null
---

## Context

A common failure mode in product organisations is a separate QA department:
people titled testers report to different managers, sit apart from the squad,
take lunch together, and run their own meetings. Even when labelled "embedded,"
they remain a tribe with its own loyalty, career path, and definition of success.

That structure produces handovers — "Ready for QA," a queue, a late sign-off —
and an us-versus-them dynamic. The squad optimises for shipping; QA optimises
for findings and gatekeeping. Quality becomes something done *to* the work after
"dev done," not something owned with the outcome.

AeroFlow is sized as a squad of about six. A second department for testing is
enterprise theatre at that scale, and it teaches the wrong lesson about how
platform and product teams should work. How we *test* (pyramid, automation,
exploratory practice) is a separate decision; this record is only about where
quality accountability lives.

## Decision

**Quality skill and accountability live inside the product squad.** There is no
separate QA department, no separate QA management line, and no mandatory
handover state before release.

Concretely:

- Testers (or engineers with deep quality craft) **sit with the squad**, share
  its rituals (standup, planning, retros), and share the same outcome measures.
- Reporting and career progress for those people align with the **squad’s
  delivery line**, not a parallel QA hierarchy.
- Definition of done is **shared**. There is no "dev complete → wait for QA"
  queue as the default path to production.
- A **community of practice** for testing craft is allowed and encouraged, but
  it is secondary to the squad bond. The CoP must not recreate a department
  (separate backlog, separate managers, stronger loyalty than the squad).

How tests are designed, automated, and explored is **out of scope** here and
belongs in a later decision on test approach.

## Consequences

The squad owns confidence to ship. Handovers shrink because the people who
change the system and the people who challenge it share one backlog and one
set of bosses. Platform work (templates, CI gates) supports the squad rather
than feeding a QA org.

What this costs: managers must hire and coach for mixed skill, not "devs plus
a QA pool." Specialist testers need a real home in the squad, or the craft
atrophies. Under delivery pressure, teams may try to recreate a mini-waterfall;
leadership has to refuse that shortcut.

What becomes harder: using a central QA headcount as a flexible buffer across
squads. Capacity planning is squad-shaped, not department-shaped.

## Alternatives considered

**Separate QA department with "embedded" testers.** Rejected. Embedding without
shared management, seating, and rituals still produces tribal loyalty and
handovers. Revisit only if regulated release sign-off legally requires an
independent test org — and even then, record the constraint explicitly rather
than pretending the squad owns quality.

**QA as a shared service / centre of excellence that squads book.** Rejected.
Creates a queue and externalises accountability. A craft CoP is fine; a booking
desk is a department. Revisit if AeroFlow somehow runs dozens of squads and a
thin enablement function is proven not to become a gate — unlikely at portfolio
scale.

**No dedicated quality craft — developers only.** Rejected as the sole model.
Developers own quality, but deep exploratory and risk-based testing skill is
real craft; excluding it rebrands under-investment as culture. Revisit for
tiny throwaway spikes only, not for lasting services.

**Test approach (pyramid, tools, environments) in this ADR.** Rejected. Mixing
org design with technique muddies the log. Revisit immediately as a follow-on
ADR once this record is accepted.

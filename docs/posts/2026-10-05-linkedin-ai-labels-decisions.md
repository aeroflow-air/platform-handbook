# LinkedIn: AI labelling and productivity decisions (zero-cost)

| | |
|---|---|
| **Title** | AI labelling and productivity decisions (zero-cost) |
| **Date** | 5 Oct 2026 |
| **Status** | draft, not yet published |
| **Related** | [ADR-0011](../decisions/0011-platform-developer-productivity-metrics.md), [ADR-0012](../decisions/0012-ai-assisted-pr-labelling.md), [PR #41](https://github.com/aeroflow-air/platform-handbook/pull/41) |

**LinkedIn post:** <!-- TODO: replace with the LinkedIn post URL once published -->

---

I want to know whether AI coding tools are actually helping teams, without turning it into a league table of individuals.

On AeroFlow, my Azure-native reference platform built in public, that's now settled, including where I decided not to spend money.

ADR-0011: productivity metrics measure teams, not people. DORA measures come from pipeline and deploy data, there's a quarterly survey in the style of DX Core 4, and the share of AI-assisted PRs is tracked against review time and change failure rate.

ADR-0012: two labels. ai-authored counts in the metrics; ai-reviewed is tracked separately. A PR template checkbox prompts authors, labels are recorded at merge time, and enforcement is phased in. The automation checks signals in a fixed order (a hand-set label, then PR description markers, then commit trailers, then known AI co-authors), tags its label ai-label:auto with a comment saying why, and anyone can override it with an auditable /ai-label command.

Then I looked at pulling usage data straight from the AI coding tools. Only two sources can tie AI use to a specific PR: Cursor's paid Enterprise per-commit tracking, and GitHub's own record that a Copilot agent authored the PR. Copilot usage metrics, Claude Code and Windsurf only give aggregates.

So the decision was no extra cost: no paid APIs, no Cursor tracking and no nightly job. The one new source is GitHub's free Copilot-agent signal, checked when the PR event fires and slotted in after description markers. Aggregates stay out of labelling.

My honest verdict is a marginal yes. A small event-time check is worth having; paying for vendor telemetry isn't. Coverage is narrow, and AI help inside the editor still relies on the template and on people being honest.

How are you handling this: paying for telemetry, or trusting a checkbox?

The decision and the change: https://github.com/aeroflow-air/platform-handbook/pull/41

#PlatformEngineering #DevEx #DORA

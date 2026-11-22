# LinkedIn: Agent skills, making the right way the easy way for AI too

| | |
|---|---|
| **Title** | Agent skills: making the right way the easy way for AI too |
| **Date** | 22 Nov 2026 |
| **Status** | draft, not yet published |
| **Related** | [ADR-0023](../decisions/0023-central-agent-skills.md), [agent-skills](https://github.com/aeroflow-air/agent-skills), [blog post PR (site-customer #25)](https://github.com/aeroflow-air/site-customer/pull/25) |

**LinkedIn post:** <!-- TODO: replace with the LinkedIn post URL once published -->

---

AI agents now write and review a lot of our code at AeroFlow Air. Each one is only as good as what it is told about how we build things.

I audited what they were being told. There was one kind of file, CLAUDE.md, in 6 of 11 repos. The same conventions block had been copied four times, some of it was out of date, and some of our rules weren't written down anywhere.

So I treated agent guidance the way a platform team treats pipelines: make the right way the easy way.

- The platform team owns a small, versioned set of skills. Each one is a plain Markdown file with when to use it, the steps, and links to real code. Any agent can read them, whether that's Claude Code, Copilot or Grok.
- Squads pin a version, exclude what they don't need, and add their own skills. The sync never touches those.
- A check fails a PR if the copies drift, and a weekly bump PR moves them to the latest release, like any dependency.

The rules that matter are enforced by analysers and pipeline checks, not by prompts. Some of ours aren't enforced yet, and the decision record lists them openly.

We also switched on secret scanning and push protection across the organisation.

What's not done: the rollout starts with the service template, and bump PRs need a GitHub App before CI will run on them.

The full write-up:
https://aeroflow-air.github.io/site-customer/engineering/agent-skills-the-right-way-the-easy-way/

#PlatformEngineering #AI #DeveloperExperience #GitHubActions

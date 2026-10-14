# LinkedIn: Claude reviews every pull request

| | |
|---|---|
| **Title** | Claude reviews every pull request |
| **Date** | 14 Oct 2026 |
| **Status** | Ready to publish manually (not yet posted) |
| **Related** | [Blog post: How AeroFlow Air uses Claude to review our code](https://aeroflow-air.github.io/site-customer/engineering/claude-code-reviews/), [blog post PR (site-customer #22)](https://github.com/aeroflow-air/site-customer/pull/22) |

**LinkedIn post:** <!-- TODO: replace with the LinkedIn post URL once published -->

---

🛫 Every pull request at AeroFlow Air now gets a first review from Claude.

It doesn't replace our engineers. It runs the routine checks the same way every time, so people can focus on design.

Before we trusted it, we tried to catch it out with deliberately bad code. It caught 9 of 9 planted issues, and 13 of 14 problems in C# that broke our functional style.

The biggest lesson: an AI reviewer is only as good as the standards you write down.

The blog post covers the full setup, with diagrams: the shared versioned workflow, the CLAUDE.md files, and what we're doing next 👇
https://aeroflow-air.github.io/site-customer/engineering/claude-code-reviews/

#PlatformEngineering #DevOps #AI #CodeReview #dotnet #GitHubActions

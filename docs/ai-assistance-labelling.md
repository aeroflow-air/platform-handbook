# AI assistance labelling — operations

Implements [ADR-0012](./decisions/0012-ai-assisted-pr-labelling.md). Metrics
consumer: [ADR-0011](./decisions/0011-platform-developer-productivity-metrics.md).

## What runs

Reusable workflow:
`aeroflow-air/aeroflow-workflows/.github/workflows/label-ai-assistance.yml`

Caller repos (golden path) add a thin workflow that `uses:` it and may pass
`CURSOR_API_KEY`.

## Secrets and permissions

| Name | Where | Required | Value |
|------|--------|----------|-------|
| `CURSOR_API_KEY` | Org or repo Actions secret | No | Cursor Enterprise API key with access to AI Code Tracking. Placeholder until issued: `REPLACE_WITH_CURSOR_ENTERPRISE_API_KEY`. |

Job permissions (least privilege):

```yaml
permissions:
  contents: read
  pull-requests: write
```

No `contents: write`. Do not store Copilot or Claude admin tokens for labelling —
those APIs cannot attribute usage to a PR.

## Supported tool signals

| Tool | Used for labels? | Data | Docs |
|------|------------------|------|------|
| Cursor AI Code Tracking | Yes (commit SHA join) | Per-commit TAB/Composer line counts; user fields redacted | https://cursor.com/docs/account/teams/ai-code-tracking-api |
| Copilot cloud agent | Yes (PR author) | GitHub PR `user.login` | https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent |
| Copilot Usage Metrics API | No | Org/user/day and repo-day **counts** only | https://docs.github.com/en/copilot/reference/copilot-usage-metrics/copilot-usage-metrics |
| Claude Code Analytics | No | Per-user/day **counts** only | https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api |
| Trailers / co-authors / template | Fallback | On the PR itself | ADR-0012 |

## Privacy (ADR-0011)

- Labelling must not create per-engineer leaderboards.
- Cursor fetch strips `userId` / `userEmail` before the decision step.
- Prefer org/service aggregates for any future dashboard that consumes vendor
  usage APIs.

## Overrides

| Command | Effect |
|---------|--------|
| `/ai-label authored` | Force `ai-authored`, set `ai-label:manual` |
| `/ai-label reviewed` | Force `ai-reviewed`, manual lock |
| `/ai-label both` | Both content labels, manual lock |
| `/ai-label none` | `ai-declaration:none`, manual lock |
| `/ai-label clear` | Remove content + auto labels, manual lock |
| `/ai-label unlock` | Clear manual lock |

## Org labels to create

`ai-authored`, `ai-reviewed`, `ai-declaration:none`, `ai-label:auto`,
`ai-label:manual` — create once at org level with descriptions matching ADR-0012.

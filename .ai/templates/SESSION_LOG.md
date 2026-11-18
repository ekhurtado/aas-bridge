# templates/SESSION_LOG.md — Session Entry Template

> Append one entry per closed session. Never rewrite prior entries.

```md
## [SES-XXX] <short title> — YYYY-MM-DD
- **Mode:** analysis | bootstrap | implementation | review | close
- **Participants:** <human + agent(s)>
- **Summary:** <what was done, one paragraph>
- **Decisions:** <ADR/TD IDs or none>
- **Artifacts:** <files created or changed>
- **Checks:** <commands/results or N/A>
- **Next:** <next session or task>
```

## Checklist

- [ ] The session has a closed cycle or a concrete milestone.
- [ ] Every changed `.ai/` file is listed.
- [ ] Decisions, issues and outcomes are referenced by ID.
- [ ] The next step is explicit.
- [ ] No secrets, tokens or personal data are recorded.

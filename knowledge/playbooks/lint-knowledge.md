---
type: Playbook
title: Lint knowledge
description: Validate frontmatter and links, then manually scan for contradictions and orphans.
tags: [okf, lint]
timestamp: 2026-07-08T15:34:24Z
---

# Lint knowledge

1. Run:

```bash
python .cursor/skills/okf/scripts/validate_okf.py
python .cursor/skills/okf/scripts/check_links.py
python .cursor/skills/okf/scripts/regen_index.py --check
```

2. Manual pass:
   - Contradictions (roles, mappings, control ownership)
   - Orphan concepts not reachable from indexes or links
   - Terms in prose without concept files
   - Stale timestamps vs content
   - Conflicts with [`CONTEXT.md`](../../CONTEXT.md)
   - Decisions that need a formal ADR
3. Report by severity; apply fixes only when asked.
4. If the user requested a full lint, append a summary to [/log.md](/log.md).

## Related

- [/playbooks/ingest-source.md](/playbooks/ingest-source.md)

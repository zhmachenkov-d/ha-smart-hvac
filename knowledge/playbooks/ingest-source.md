---
type: Playbook
title: Ingest source
description: Copy raw material into knowledge/raw/, extract one concept per idea, cross-link, regen indexes, validate.
tags: [okf, ingest]
timestamp: 2026-07-08T15:45:00Z
---

# Ingest source

1. Place an **immutable** copy under `knowledge/raw/<source-slug>/` (never edit raw after ingest).
2. Read the source end-to-end.
3. Create or update one page per idea in `concepts/`, `decisions/`, or `references/` per [.cursor/skills/okf/CONCEPT-TYPES.md](/.cursor/skills/okf/CONCEPT-TYPES.md).
4. Cross-link 5–15 related pages; prefer bundle paths like `/concepts/foo.md`.
5. Add short glossary lines to [`CONTEXT.md`](../../CONTEXT.md) only when a term needs a canonical one-liner.
6. If a choice is irreversible, file `docs/adr/` **and** a `decisions/` page.
7. Append a dated entry to [/log.md](/log.md).
8. Run:

```bash
python .cursor/skills/okf/scripts/regen_index.py
python .cursor/skills/okf/scripts/validate_okf.py
python .cursor/skills/okf/scripts/check_links.py
```

9. Report created/updated pages and remaining stubs.

## Related

- [/playbooks/lint-knowledge.md](/playbooks/lint-knowledge.md)
- [/references/huang-2018-ladrc-hvac.md](/references/huang-2018-ladrc-hvac.md) (example ingest)
- [/references/wang-2026-madrc-sst.md](/references/wang-2026-madrc-sst.md) (example ingest; CDN PDF when journal HTML is blocked)

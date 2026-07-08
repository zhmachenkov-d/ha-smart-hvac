---
name: okf
description: Manage the OKF knowledge bundle in knowledge/ — ingest raw sources into concepts, query the graph with citations, and lint for contradictions and broken links. Use when the user invokes Ingest, Query, or Lint for the knowledge system, or asks about OKF workflows.
disable-model-invocation: true
---

# OKF Knowledge System

Three explicit workflows for the `knowledge/` bundle. Read [CONCEPT-TYPES.md](CONCEPT-TYPES.md)
for producer conventions.

**Bundle root:** `knowledge/`  
**Coexistence:** glossary in `CONTEXT.md`, formal ADRs in `docs/adr/`, depth here.

## Scripts

```bash
python .cursor/skills/okf/scripts/validate_okf.py
python .cursor/skills/okf/scripts/check_links.py
python .cursor/skills/okf/scripts/regen_index.py
python .cursor/skills/okf/scripts/regen_index.py --check
```

Uses stdlib by default; optional PyYAML if installed.

---

## Workflow: Ingest

**Trigger:** User asks to ingest new material, or drops files in `knowledge/raw/`.

1. Identify new or updated files under `knowledge/raw/` (immutable — never edit in place after ingest)
2. Read source end-to-end
3. Extract **one concept per idea** — not one markdown page per source page
4. Create or update files in `concepts/`, `decisions/`, `references/` per [CONCEPT-TYPES.md](CONCEPT-TYPES.md)
5. Update cross-links across 5–15 related bundle pages
6. Add short glossary entries to `CONTEXT.md` only when a term needs a canonical one-liner
7. Link to `docs/adr/` when a decision becomes formal
8. Append entry to `knowledge/log.md`
9. Run `regen_index.py`, then `validate_okf.py` and `check_links.py`
10. Report what was created/updated and any stubs still needing raw sources

Follow the detailed checklist in [ingest-source playbook](/knowledge/playbooks/ingest-source.md).

---

## Workflow: Query

**Trigger:** User asks a domain question that should be answered from the bundle.

1. Read `knowledge/index.md` for orientation
2. Drill into relevant type indexes (`concepts/`, `decisions/`, `references/`, `playbooks/`)
3. Read linked pages until the question is answerable
4. Synthesize an answer with **bundle-relative citations** (`/concepts/foo.md`)
5. If the synthesis is reusable and missing as a concept, offer to file it (do not auto-create without user consent)

Prefer bundle knowledge over re-deriving from scratch. If raw sources are needed, note
which `raw/` file should be ingested next.

---

## Workflow: Lint

**Trigger:** User asks to lint the knowledge bundle, or after a large ingest.

1. Run all three scripts (validate, check links, regen_index --check)
2. Manual pass per [lint-knowledge playbook](/knowledge/playbooks/lint-knowledge.md):
   - Contradictions (roles, mappings, pin assignments)
   - Orphan concepts not reachable from indexes or links
   - Terms in prose without concept files
   - Stale timestamps vs content
   - CONTEXT.md conflicts
   - Decisions without ADRs when irreversible
3. Report findings grouped by severity
4. Propose fixes; apply only when user asks
5. Append lint summary to `knowledge/log.md` if user requested a full lint pass

---

## Obsidian

Open `knowledge/` as an Obsidian vault for graph view. No custom visualizer in v1.

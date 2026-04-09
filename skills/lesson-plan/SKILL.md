---
name: lesson-plan
description: Create a pedagogically sound, time-bounded lesson plan from corpus and validated sources. Produces lesson-plan.md. Every content item must trace to a source. Never adds objectives not in briefing.
---

You are building the lesson plan from the closed briefing, corpus inventory, and validated sources.

## BEFORE STARTING

1. Read `aulas/<slug>/briefing.md`. If `status` is not `closed`: stop and say "O briefing ainda não foi fechado. Execute `/lesson-intake` primeiro."
2. Read `aulas/<slug>/corpus-inventory.md`
3. Read `aulas/<slug>/sources.md`

If any of these files is missing: stop and state which file is missing and which skill produces it.

## Planning constraints

- Total duration = `briefing.duration_minutes` (default 45)
- Academic level = `briefing.level`
- Teaching style = `briefing.style`
- Must address ALL objectives in `briefing.secondary_objectives`
- Must use ALL materials marked `obrigatório` in corpus-inventory

## Block types and typical durations

| Block type | Typical % of total | Purpose |
|------------|-------------------|---------|
| introdução | 10–15% | Activate prior knowledge, set objectives |
| desenvolvimento | 50–60% | Core content delivery |
| fixação | 15–20% | Practice, activity, verification |
| fechamento | 10–15% | Summary, next steps |

## Conceptual progression

Organize content so that:
1. Each concept builds on previously introduced concepts
2. No concept is introduced without its prerequisites being covered first
3. The most important objective is reached by the midpoint of the lesson

## Every content item must have a source

For each `content_item`, set `source_ref` to:
- A `source_id` from sources.md (e.g., `leslie-lamport-1978`), OR
- A filepath from corpus-inventory.md (e.g., `docs/unidades/01-intro/slides/aula01.pptx`)

If a content item cannot be traced to any source or corpus file: remove it from the plan.

## Time budget check

Sum all `duration_minutes` values. If sum > `total_duration_minutes`:
- First, remove all blocks marked `optional`
- If still over budget: trim the longest development block
- If still over budget: stop and ask the professor to increase duration or reduce scope

Set `time_budget_check: pass` only when sum ≤ total_duration_minutes.

## Show plan before writing

Display the complete plan with time allocations as a table:

| Bloco | Tipo | Duração | Prioridade |
|-------|------|---------|-----------|

Show time total and whether it fits.

Ask: "Este plano está adequado? (sim / ajustar: bloco, operação)"

**STOP and wait. Accept adjustments. Only write after "sim".**

## GUARDRAILS

- NEVER include content not traceable to a source or corpus file
- NEVER exceed the time budget
- NEVER add objectives not in briefing
- NEVER generate slide content (that is lesson-blueprint's job)
- NEVER write lesson-plan.md before explicit "sim"
- If style=interativo or laboratório: plan MUST include at least one fixação block with an activity

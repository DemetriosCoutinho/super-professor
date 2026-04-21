---
name: lesson-notebooklm
description: Create or update a NotebookLM notebook for a lesson using lesson-plan.md, sources.md, and blueprint as sources. Triggers generation of audio overview, study guide, and mind map. Saves outputs to aulas/<slug>/extras/. Run after /lesson-blueprint.
---

You are creating supplementary lesson content via NotebookLM. Use the `notebooklm` skill for all NotebookLM API operations.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da aula?"
2. Verify these files exist:
   - `aulas/<slug>/lesson-plan.md`
   - `aulas/<slug>/sources.md`
   - `aulas/<slug>/slides-blueprint.md`

If any is missing: stop and state which file is needed and which skill generates it.

3. Invoke the `notebooklm` skill to check authentication status before proceeding.

## Step 1: Check for existing notebook

Read `aulas/<slug>/extras/notebooklm-manifest.json` if it exists.
If `notebook_id` is present: ask the teacher "Já existe um notebook para esta aula (`<notebook_id>`). Atualizar fontes e regenerar conteúdo? (sim / não)"

## Step 2: Collect sources

Build the source list for the notebook:
1. `aulas/<slug>/lesson-plan.md` — primary source (full text)
2. `aulas/<slug>/sources.md` — bibliography and external references
3. `aulas/<slug>/slides-blueprint.md` — slide structure and speaker notes
4. Any PDF paths listed in `sources.md` that exist locally

Present the source list to the professor: "Estas são as fontes que serão enviadas ao NotebookLM. Adicionar mais? (sim: <path> / não)"

## Step 3: Create or update notebook

Using the `notebooklm` skill:
- If new notebook: create with title `"[super-professor] <lesson_title> — <slug>"`
- If existing: update sources (add new, flag removed)
- Upload text sources as inline text, PDF sources as file uploads

Capture `notebook_id`.

## Step 4: Request content generation

Ask which outputs to generate:
```
Quais conteúdos gerar? (responda com números, ex: 1,3)
  1. Audio overview (podcast resumo ~5 min)
  2. Study guide (guia de estudos estruturado)
  3. Mind map (mapa mental exportável)
  4. Briefing doc (resumo executivo)
  5. FAQ (perguntas frequentes do conteúdo)
```

For each selected output, trigger generation via the `notebooklm` skill.

## Step 5: Save outputs

Create `aulas/<slug>/extras/` if it doesn't exist.

For each generated output:
- **Audio overview**: save link/transcript to `aulas/<slug>/extras/audio.md`
- **Study guide**: save to `aulas/<slug>/extras/study-guide.md`
- **Mind map**: save to `aulas/<slug>/extras/mind-map.md` (or export link)
- **Briefing doc**: save to `aulas/<slug>/extras/briefing-doc.md`
- **FAQ**: save to `aulas/<slug>/extras/faq.md`

## Step 6: Write manifest

Write `aulas/<slug>/extras/notebooklm-manifest.json`:

```json
{
  "created_at": "<ISO timestamp>",
  "updated_at": "<ISO timestamp>",
  "slug": "<slug>",
  "notebook_id": "<id>",
  "notebook_title": "<title>",
  "sources": [
    {"type": "text|pdf", "path": "<path>", "added_at": "<ISO>"}
  ],
  "outputs": [
    {"type": "audio|study_guide|mind_map|briefing_doc|faq", "file": "<path>", "generated_at": "<ISO>"}
  ]
}
```

Report to teacher:
```
NotebookLM configurado para <slug>:
  Notebook: <notebook_id>
  Fontes: <N>
  Conteúdo gerado:
    ✓ <tipo> → aulas/<slug>/extras/<file>
    ...
```

## GUARDRAILS

- NEVER upload files that contain student data (scores, grades, names)
- NEVER proceed without authentication check (Step BEFORE STARTING item 3)
- NEVER overwrite existing extras files without showing the professor what will be replaced
- If NotebookLM API returns an error: surface verbatim, write partial manifest with `status: error`, stop
- This skill delegates all API calls to the `notebooklm` skill — do NOT attempt direct API calls

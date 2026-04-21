---
name: lesson-classroom-publish
description: Publish lesson materials and activities directly to Google Classroom using the gws CLI. Reads lesson-plan.md, blueprint, and extras. Supports --preview (dry-run) mode. Run after /lesson-blueprint (and optionally /lesson-notebooklm).
---

You are publishing lesson content to Google Classroom via the gws CLI.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da aula? (ex: `2026-04-21-introducao-lamport-clocks`)"
2. Ask: "Modo de execução: `--preview` (mostrar sem publicar) ou publicar agora?"
3. Check gws is available: `gws --version 2>&1`. If fails: stop and say "gws CLI não encontrado."
4. Verify required files exist:
   - `aulas/<slug>/lesson-plan.md` — objectives, duration
   - `aulas/<slug>/slides-blueprint.md` — activities, homework
   - `.super-professor/repo-manifest.md` — must contain `course_id`

If `course_id` is missing from manifest: ask teacher "Qual é o course_id do Google Classroom?"

## Step 1: Read lesson content

From `aulas/<slug>/lesson-plan.md` extract:
- `lesson_title`
- `lesson_date` (if present)
- `objectives` list
- Any homework or activity blocks

From `aulas/<slug>/slides-blueprint.md` extract:
- Slides with `type: fixacao` or `type: atividade` → candidate activities
- Any homework descriptions

Check for extras in `aulas/<slug>/extras/` (created by `/lesson-notebooklm`):
- `audio.md` → link to audio overview
- Any exported study guides or mind maps

## Step 2: Build publish plan

Propose items to publish. For each item, show:

```
Item <n>: <title>
  Tipo: MATERIAL | ASSIGNMENT | SHORT_ANSWER_QUESTION
  Descrição: <first 100 chars>
  Pontos: <N ou null>
  Data de entrega: <YYYY-MM-DD ou null>
  Anexos: <list of files/links>
```

Ask the teacher: "Quais itens publicar? (números separados por vírgula, ou `todos`, ou `nenhum`)"

**In `--preview` mode**: show the publish plan and the exact gws JSON payload for each item, then STOP. Do NOT proceed to Step 3.

## Step 3: Confirm before publishing

Show a summary:

```
Prestes a publicar no Classroom (course_id: <course_id>):
  • <N> itens
  • Títulos: <list>

Confirmar? (sim / não)
```

Only continue if teacher types "sim".

## Step 4: Publish each item

For each confirmed item, run:

```bash
gws classroom courses courseWork create \
  --params '{"courseId": "<course_id>"}' \
  --json '{
    "title": "<title>",
    "description": "<description>",
    "workType": "<ASSIGNMENT|MATERIAL|SHORT_ANSWER_QUESTION>",
    "maxPoints": <N or omit>,
    "dueDate": {"year": YYYY, "month": MM, "day": DD},
    "materials": [
      {"driveFile": {"driveFile": {"id": "<id>", "title": "<name>"}, "shareMode": "VIEW"}}
    ]
  }'
```

For plain link materials (no Drive upload):
```bash
gws classroom courses courseWork create \
  --params '{"courseId": "<course_id>"}' \
  --json '{
    "title": "<title>",
    "workType": "MATERIAL",
    "materials": [{"link": {"url": "<url>", "title": "<title>"}}]
  }'
```

Capture the response. Extract `id` (courseWorkId) and `alternateLink`.

## Step 5: Write publish record

Write `aulas/<slug>/classroom-publish.json`:

```json
{
  "published_at": "<ISO timestamp>",
  "course_id": "<course_id>",
  "slug": "<slug>",
  "items": [
    {
      "title": "<title>",
      "work_type": "<type>",
      "courseWorkId": "<id>",
      "link": "<alternateLink>",
      "status": "published"
    }
  ],
  "skipped": [],
  "errors": []
}
```

Report to teacher:
```
Publicado no Classroom:
  ✓ <N> itens publicados
  ✗ <M> erros (listados abaixo)
Links: <alternateLink para cada item>
```

## GUARDRAILS

- NEVER publish without explicit "sim" confirmation showing all items
- NEVER re-publish an item that already has a `courseWorkId` in `classroom-publish.json` — show the existing link and ask for explicit override confirmation
- NEVER invent courseWorkIds — always capture from gws response
- Surface gws errors verbatim
- In `--preview` mode: NEVER call any write endpoint, NEVER write `classroom-publish.json`

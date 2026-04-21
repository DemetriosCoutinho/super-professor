---
name: lesson-images
description: Author the media plan for a lesson blueprint. For each slide requiring an image, decides the source in priority order: (1) reuse from corpus, (2) generate Mermaid/HTML diagram, (3) generate raster image via Gemini or DALL-E. Outputs media-plan.md. Run after /lesson-blueprint.
---

You are authoring the media plan for a lesson. Every image decision must have a declared pedagogical function.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da aula?"
2. Verify these files exist:
   - `aulas/<slug>/slides-blueprint.md` — source of slides with `media.required: true`
   - `aulas/<slug>/corpus-inventory.md` — index of reference materials (if exists)
   - `.super-professor/repo-manifest.md` — check for `image_provider` field

Read `repo-manifest.md`. If `image_provider` is absent, note it and default to `mermaid_only` (no raster generation).

## Step 1: Extract slides needing media

Read `aulas/<slug>/slides-blueprint.md`. Collect all slides where `media.required: true`.

For each, capture:
- `slide_number`
- `title`
- `media.description` (the ≥20-word description from the blueprint)
- `media.pedagogical_function`
- `media.type` (diagram | photo | animation | infographic | etc.)

## Step 2: Resolve source for each slide

For each slide, try sources in order:

### Source 1: Corpus reuse

Search `aulas/<slug>/corpus-inventory.md` (or `aulas/<slug>/sources.md`) for:
- Figures, diagrams, or images referenced in the materials
- Match by topic keywords from slide title and description

If a match is found: record `source: corpus`, `file: <path>`, `page: <n>`, `extraction_note: <how to extract>`.

### Source 2: Mermaid / HTML diagram

Use when `media.type` is `diagram`, `flowchart`, `sequence`, `timeline`, or `architecture` — or when the description calls for structured relationships.

Generate the Mermaid or HTML+SVG code directly. Embed inline in the media plan.

Mermaid types to prefer:
- `sequenceDiagram` — message passing, protocols
- `flowchart LR/TD` — algorithms, decision trees
- `classDiagram` — data structures, OOP
- `timeline` — historical events, evolution
- `graph` — dependency trees, concept maps

### Source 3: Raster image (Gemini or DALL-E)

Use only when Sources 1 and 2 are unsuitable (e.g., realistic photo, specific illustration).

Read `image_provider` from `repo-manifest.md`:
- `gemini` → use `google-genai` SDK, model `imagen-3.0-generate-002`
- `openai` → use OpenAI SDK, model `dall-e-3`
- absent or `mermaid_only` → skip raster, note "raster not configured — add `image_provider` to repo-manifest.md"

If provider is configured:
- Compose a detailed generation prompt from `media.description`
- State the prompt in the media plan (do NOT call the API yet — let the professor review prompts first)
- Cache path: `aulas/<slug>/images/slide-<n>-<slug>.png`

## Step 3: Sample review

After resolving the first 3 slides, STOP and show the professor:

```
Aqui está o plano de mídia para os primeiros 3 slides:

Slide <n>: <title>
  Fonte: corpus | mermaid | raster
  [Código Mermaid ou path do corpus ou prompt de geração]
  Função pedagógica: <function>

A direção está certa? (sim / ajustar: slide=<n>, campo=<valor>)
```

Only continue after "sim".

## Step 4: Write media plan

Write `aulas/<slug>/media-plan.md` following `templates/media-plan.md`.

For each slide:
- `source`: `corpus | mermaid | raster | none`
- If `mermaid`: embed the full Mermaid/HTML code block
- If `corpus`: record file path and page
- If `raster`: record the generation prompt (not yet generated)

## Step 5: Generate raster images (if provider configured and professor approves)

After the professor approves the media plan, ask:
"Gerar as imagens raster agora? Isso chamará a API `<provider>` para <N> slides."

If yes: call the API for each raster slide, save to `aulas/<slug>/images/`, update `media-plan.md` with actual file paths and a hash.

## Output

Writes `aulas/<slug>/media-plan.md` and (optionally) `aulas/<slug>/images/` with generated images.

## GUARDRAILS

- NEVER declare `source: corpus` without an actual match in corpus-inventory or sources.md
- NEVER skip the `pedagogical_function` field — every image must justify its cognitive purpose
- NEVER call image APIs without explicit professor approval after reviewing the prompts
- NEVER generate raster images when `image_provider` is absent — fall back to Mermaid
- When Mermaid code is generated, validate syntax mentally (correct diagram type, no undefined nodes)

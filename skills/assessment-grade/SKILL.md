---
name: assessment-grade
description: Grade an assessment by processing photos in assessments/<slug>/photos/ using OMRChecker and Claude Vision fallback. Produces scores.json and grade-report.md. Run after placing photos in the photos/ directory.
---

You are orchestrating the grading pipeline for a paper assessment.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da avaliação? (ex: `2026-04-20-prova-p1-calculo-i`)"
2. Verify `assessments/<slug>/assessment-manifest.md` exists. If not: stop and say "Execute `/assessment-create` primeiro."
3. Verify `assessments/<slug>/photos/` contains at least one `.jpg` or `.png` file. If empty: stop and say "Adicione as fotos das folhas em `assessments/<slug>/photos/` e tente novamente."

## Step 1: Check OMRChecker

Run:
```bash
python -m omrchecker --version 2>&1
```

If it fails: stop and say "OMRChecker não encontrado. Execute: `pip install omrchecker`"

## Step 2: Process each photo with omr-processor

For each photo file in `assessments/<slug>/photos/`:

Dispatch the `omr-processor` subagent with:
- `photo_path`: absolute path to the photo
- `omr_template_path`: absolute path to `assessments/<slug>/omr-template.json`
- `output_dir`: `assessments/<slug>/results/omr-work/`

Collect the JSON result from each subagent call.

## Step 3: Apply Vision fallback for low-confidence questions

For each sheet result where `low_confidence_questions` is non-empty:

Dispatch the `vision-grader` subagent with:
- `photo_path`: absolute path to the photo
- `questions`: the list from `low_confidence_questions`
- `omr_answers`: the current answers dict for those questions

Merge the corrections into the sheet result: replace `value` and `confidence` for each corrected question with the vision-grader's values.

## Step 4: Build raw-omr.json

Assemble all sheet results (post-correction) into:

```json
{
  "sheets": [ ...all sheet result objects... ]
}
```

Write to `assessments/<slug>/results/raw-omr.json`.

## Step 5: Compute scores

Run:
```bash
python scripts/compute_scores.py \
  assessments/<slug>/results/raw-omr.json \
  assessments/<slug>/assessment-manifest.md \
  assessments/<slug>/results/
```

If this exits with a non-zero code, stop and surface the error output verbatim.

## Step 6: Report to teacher

Read `assessments/<slug>/results/grade-report.md` and display it.

Then say:
"Resultados salvos em `assessments/<slug>/results/`.
- `scores.json` — dados para integração
- `grade-report.md` — tabela de notas

Execute `/assessment-sync` para enviar as notas ao Google Classroom."

## GUARDRAILS

- NEVER modify original photos
- NEVER skip the Vision fallback when `low_confidence_questions` is non-empty
- NEVER proceed to scoring if `compute_scores.py` exits with non-zero — surface the error
- NEVER send grades to Classroom — that is `/assessment-sync`'s job

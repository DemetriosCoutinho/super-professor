---
name: assessment-grade
description: Grade a multiple-choice assessment (A–D alternatives, 0–100 score, passing score 60 by default) by processing photos using OMRChecker and Claude Vision fallback. Produces scores.json and grade-report.md. Use after /assessment-create when photos are placed in the photos/ directory.
---

You are orchestrating the grading pipeline for a paper assessment.

## Assessment contract

- Every question has exactly **4 alternatives labelled A, B, C, D**. No other bubble values are valid.
- Scores are on a **0–100 scale**: `score = round(correct / total * 100, 1)`.
- **Passing score default = 60**. Override via `passing_score:` field in `assessment-manifest.md`. A student passes when `score ≥ passing_score`.
- Student ID (matrícula) is a **14-digit string** read from the ID bubble area.
- Sheet schema: `schemas/raw-omr.v1.json` in the super_professor project.

## BEFORE STARTING

### Step 0: Locate the assessment directory

The assessment directory can be in one of two layouts:
- **Layout A (legacy):** `assessments/<slug>/` — check `assessments/` at repo root
- **Layout B (current):** `aulas/<date-slug>/assessment/` — check `aulas/` at repo root

Auto-discover: search for `assessment-manifest.md` using:
```bash
find . -name "assessment-manifest.md" -not -path "*/\.*" 2>/dev/null
```

If multiple are found, ask the teacher which one. If the teacher provided a slug or path, use it directly. Derive `ASSESSMENT_DIR` (absolute path to the dir containing `assessment-manifest.md`).

All subsequent paths are relative to `ASSESSMENT_DIR`:
- `photos/` — input photos
- `omr-config.json` — OMR template (also accept `omr-template.json` for legacy)
- `results/` — output dir
- `results/omr-work/` — OMRChecker work dir

### Step 0b: Verify prerequisites

```bash
ls "$ASSESSMENT_DIR/assessment-manifest.md"    # must exist
ls "$ASSESSMENT_DIR/omr-config.json" 2>/dev/null || ls "$ASSESSMENT_DIR/omr-template.json"  # must exist
ls "$ASSESSMENT_DIR/photos/"                   # must have files
```

If `assessment-manifest.md` missing: stop → "Execute `/assessment-create` primeiro."
If OMR config missing: stop → "Execute `/assessment-create` e regenere o omr-config.json."

### Step 0c: Create output dirs

```bash
mkdir -p "$ASSESSMENT_DIR/results/omr-work"
```

## Step 1: Check OMRChecker

```bash
/Users/demetrios/Projects/super_professor/tools/OMRChecker/.venv/bin/python3 \
  /Users/demetrios/Projects/super_professor/tools/OMRChecker/main.py --help 2>&1 | head -2
```

Say: `[1/6] OMRChecker OK ✓`

## Step 2: Convert HEIC photos and enumerate

For each `.HEIC` file in `photos/`:
- Convert using Python inline (no sips):
```bash
/Users/demetrios/Projects/super_professor/tools/OMRChecker/.venv/bin/python3 -c "
import pillow_heif, pathlib, PIL.Image
pillow_heif.register_heif_opener()
src = pathlib.Path('<heic_path>')
dst = src.with_suffix('.jpg')
PIL.Image.open(src).save(str(dst), 'JPEG', quality=95)
print(f'Converted {src.name} → {dst.name}')
"
```
After conversion, the `.jpg` file is in the same `photos/` directory.

Enumerate all `.jpg` and `.png` files in `photos/` (including just-converted ones). If empty after conversion: stop → "Nenhuma foto encontrada em photos/."

Say: `[2/6] Fotos encontradas: N (X convertidas de HEIC)`

## Step 3: Check for roster file (optional)

Look for `alunos.csv` in these locations (in order):
1. `$ASSESSMENT_DIR/../alunos.csv`
2. `$ASSESSMENT_DIR/../../<turma>/alunos.csv` where `<turma>` is detected from the path
3. Any `alunos.csv` in parent dirs up to repo root

If found and non-empty (has rows beyond header): load matrícula→nome mapping. Log: `Roster carregado: N alunos`
If not found or empty: proceed without roster (some sheets may be unmatched).

## Step 4: Process each photo with omr-processor

For each photo, say: `[3/6] Processando foto K/N: <filename>…`

Dispatch the `omr-processor` subagent with:
- `photo_path`: absolute path to the `.jpg`/`.png` file
- `omr_template_path`: absolute path to `omr-config.json` (or `omr-template.json`)
- `output_dir`: `$ASSESSMENT_DIR/results/omr-work/`

Collect JSON results. Handle `unreadable: true` by logging and continuing.

## Step 5: Vision fallback for low-confidence detections

For each sheet with non-empty `low_confidence_questions` OR `low_confidence_id_digits`:

Say: `[4/6] Vision fallback: <N> questões, <M> dígitos de ID em <filename>…`

**For answer questions** (from `low_confidence_questions`):
Dispatch `vision-grader` with `field_type: "mcq"`, `questions: [...]`.
Merge corrections — discard any value outside `{A,B,C,D}`.

**For ID digits** (from `low_confidence_id_digits`):
Dispatch `vision-grader` with `field_type: "digit"`, `questions: ["D9", "D13", ...]`.
Merge corrections — discard any value outside `{0,1,2,3,4,5,6,7,8,9}`.

## Step 6: Resolve student IDs

For each sheet:

1. If `student_id` is already a 14-digit string → confirmed, use as-is.
2. If `student_id` is null but `student_id_raw` has values:
   a. Build the candidate string (replace null digits with "?").
   b. If roster is loaded: find all matrículas matching the pattern (regex `^<D1><D2>...<D14>$` where `?` matches any digit).
      - Exactly 1 match → assign that matrícula, log `Auto-matched: <matricula> (<nome>)`.
      - 0 or >1 matches → mark `unmatched`, list candidates if any.
   c. If no roster or no match → mark `unmatched`, include the partial string for teacher review.

## Step 7: Build raw-omr.json

Assemble all sheet results (post-correction, post-ID-resolution) into:

```json
{"sheets": [...all sheet result objects conforming to schemas/raw-omr.v1.json...]}
```

Write to `$ASSESSMENT_DIR/results/raw-omr.json`.

Say: `[5/6] raw-omr.json gerado.`

## Step 8: Compute scores

```bash
python3 /Users/demetrios/Projects/super_professor/scripts/compute_scores.py \
  "$ASSESSMENT_DIR/results/raw-omr.json" \
  "$ASSESSMENT_DIR/assessment-manifest.md" \
  "$ASSESSMENT_DIR/results/"
```

If exit code ≠ 0: stop and show error verbatim.

Say: `[6/6] Notas calculadas.`

## Step 9: Report to teacher

Read `$ASSESSMENT_DIR/results/grade-report.md` and display it in full.

Then say:
```
Resultados salvos em results/:
- scores.json — dados para integração
- grade-report.md — tabela de notas

Execute /assessment-sync para enviar as notas ao Google Classroom.
```

## GUARDRAILS

- NEVER modify original photos (convert HEIC to a new .jpg, never overwrite the .HEIC)
- NEVER skip Vision fallback when `low_confidence_questions` or `low_confidence_id_digits` is non-empty
- NEVER accept a bubble value outside `{A,B,C,D}` from vision-grader for MCQ questions
- NEVER accept a digit value outside `{0..9}` from vision-grader for ID digits
- NEVER auto-match a matrícula if roster has 0 or >1 candidates — these go to `unmatched`
- NEVER proceed to scoring if `compute_scores.py` exits non-zero
- NEVER send grades to Classroom — that is `/assessment-sync`'s job

---
name: omr-processor
description: Run OMRChecker on a single answer sheet photo and return detected bubble values as JSON conforming to schemas/raw-omr.v1.json. Never scores. Never modifies the original photo.
---

You process one answer sheet image using OMRChecker and return the detected answers.

## Inputs (provided in the task prompt)
- `photo_path`: absolute path to the photo file (jpg, png, or heic)
- `omr_template_path`: absolute path to `omr-config.json` (also accept `omr-template.json`)
- `output_dir`: directory where OMRChecker should write its output

## Step 1: Convert HEIC if needed

If `photo_path` ends with `.heic` or `.HEIC`:
```bash
/Users/demetrios/Projects/super_professor/tools/OMRChecker/.venv/bin/python3 -c "
import pillow_heif, pathlib, PIL.Image
pillow_heif.register_heif_opener()
src = pathlib.Path('<photo_path>')
dst = src.with_suffix('.jpg')
PIL.Image.open(src).save(str(dst), 'JPEG', quality=95)
print(dst)
"
```
Update `photo_path` to the new `.jpg` path. NEVER delete the original HEIC.

## Step 2: Check OMRChecker

```bash
OMRCHECKER_DIR="/Users/demetrios/Projects/super_professor/tools/OMRChecker"
PYTHON="$OMRCHECKER_DIR/.venv/bin/python3"
"$PYTHON" "$OMRCHECKER_DIR/main.py" --help 2>&1 | head -2
```

If fails, return: `{"error": "omrchecker_not_installed", "unreadable": true, "source_file": "<basename>"}`

## Step 3: Run OMRChecker

```bash
OMRCHECKER_DIR="/Users/demetrios/Projects/super_professor/tools/OMRChecker"
PYTHON="$OMRCHECKER_DIR/.venv/bin/python3"
TMPDIR=$(mktemp -d)
cp "<photo_path>" "$TMPDIR/"
cp "<omr_template_path>" "$TMPDIR/template.json"
mkdir -p "<output_dir>"
cd "$OMRCHECKER_DIR"
"$PYTHON" main.py --inputDir "$TMPDIR" --outputDir "<output_dir>"
```

## Step 4: Parse CSV output

Read CSV from `<output_dir>/Results/*.csv`. One row per sheet. Columns include field block labels (D1..D14, q1..q20) and confidence scores.

## Step 5: Return structured JSON

Return ONLY this JSON (schema: `schemas/raw-omr.v1.json`):

```json
{
  "source_file": "sheet-001.jpg",
  "student_id": "20261094010005",
  "student_id_raw": {
    "D1": "2", "D2": "0", "D3": "2", "D4": "6",
    "D5": "1", "D6": "0", "D7": "9", "D8": "4",
    "D9": "0", "D10": "1", "D11": "0", "D12": "0",
    "D13": "0", "D14": "5"
  },
  "answers": {
    "q1": {"value": "A", "confidence": 0.98},
    "q2": {"value": "B", "confidence": 0.73}
  },
  "low_confidence_questions": ["q2"],
  "low_confidence_id_digits": [],
  "unreadable": false
}
```

Rules:
- `student_id`: join **14** digit columns D1–D14. If all 14 are detected → string. If any is null/blank → set `student_id: null` and list ambiguous columns in `low_confidence_id_digits`.
- `low_confidence_questions`: questions with confidence < 0.80
- `low_confidence_id_digits`: columns where OMR detection was absent or confidence < 0.80
- `unreadable`: true only if OMRChecker fails entirely

## GUARDRAILS
- NEVER modify the source photo (HEIC → new .jpg is fine, do NOT overwrite .HEIC)
- NEVER score the answers
- Return ONLY the JSON above — no extra text

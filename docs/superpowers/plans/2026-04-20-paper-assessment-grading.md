# Paper Assessment Grading System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three Claude Code skills (`/assessment-create`, `/assessment-grade`, `/assessment-sync`) to the super_professor plugin that let a teacher create printable multiple-choice answer sheets, grade them from photos using OMRChecker + Claude Vision, and post scores to Google Classroom via the `gws` CLI.

**Architecture:** Skills are markdown files in `skills/<name>/SKILL.md` that instruct Claude. Heavier logic (score computation) lives in a standalone Python script in `scripts/`. A fixed A4 bubble-sheet layout is used every time so one OMRChecker template JSON covers all assessments. The `gws classroom` CLI handles all Google Classroom API calls.

**Tech Stack:** Claude Code skills (markdown), Python 3 (`compute_scores.py`), OMRChecker (`pip install omrchecker`), gws CLI, Jinja2-free HTML template, Google Classroom API (via gws).

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/assessment-create/SKILL.md` | Create | Collect params, generate manifest + answer sheet HTML |
| `skills/assessment-grade/SKILL.md` | Create | Orchestrate OMRChecker → Vision fallback → scores |
| `skills/assessment-sync/SKILL.md` | Create | Post scores to Google Classroom via gws CLI |
| `agents/omr-processor.md` | Create | Subagent: run OMRChecker on one photo, return JSON |
| `agents/vision-grader.md` | Create | Subagent: re-evaluate low-confidence questions with Vision |
| `templates/assessment-manifest.template.md` | Create | Manifest YAML template |
| `templates/answer-sheet.template.html` | Create | Printable A4 bubble sheet (20 questions, A–D) |
| `templates/omr-template.json` | Create | OMRChecker layout config matching the HTML template |
| `scripts/compute_scores.py` | Create | Compare OMR output to answer key → scores.json + grade-report.md |
| `tests/test_compute_scores.py` | Create | Unit tests for score computation |
| `CLAUDE.md` | Modify | Add three new skills to the skills table |

---

## Task 1: Printable Answer Sheet HTML Template

**Files:**
- Create: `templates/answer-sheet.template.html`

The template uses `{{TITLE}}`, `{{DATE}}`, `{{QUESTIONS}}` placeholders that the `/assessment-create` skill fills in. It produces a fixed A4 layout with 20 questions in 2 columns, bubbles A–D per row, and a 9-digit student ID grid at the top. This fixed layout is what OMRChecker's template JSON (Task 2) maps against.

- [ ] **Step 1: Create the answer sheet HTML template**

Create `templates/answer-sheet.template.html`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>{{TITLE}}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Arial, sans-serif;
    width: 210mm;
    min-height: 297mm;
    padding: 15mm;
    background: white;
    font-size: 11pt;
  }
  h1 { font-size: 14pt; text-align: center; margin-bottom: 4mm; }
  .meta { text-align: center; font-size: 10pt; margin-bottom: 6mm; color: #444; }
  .student-id-section {
    border: 1.5px solid #000;
    padding: 4mm;
    margin-bottom: 6mm;
  }
  .student-id-section label { font-weight: bold; font-size: 10pt; }
  .id-grid {
    display: flex;
    gap: 3mm;
    margin-top: 2mm;
  }
  .id-col { display: flex; flex-direction: column; align-items: center; gap: 1mm; }
  .id-col span { font-size: 8pt; font-weight: bold; }
  .bubble-row { display: flex; gap: 1mm; }
  .bubble {
    width: 6mm;
    height: 6mm;
    border-radius: 50%;
    border: 1.5px solid #000;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 7pt;
    cursor: default;
  }
  .questions-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2mm 8mm;
  }
  .question-row {
    display: flex;
    align-items: center;
    gap: 3mm;
    padding: 1mm 0;
    border-bottom: 0.5px solid #ddd;
  }
  .q-num { font-weight: bold; font-size: 10pt; width: 8mm; text-align: right; }
  .options { display: flex; gap: 3mm; }
  .option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5mm;
  }
  .option span { font-size: 8pt; font-weight: bold; }
  .opt-bubble {
    width: 7mm;
    height: 7mm;
    border-radius: 50%;
    border: 1.5px solid #000;
  }
  .footer {
    margin-top: 8mm;
    font-size: 8pt;
    color: #666;
    text-align: center;
    border-top: 0.5px solid #ccc;
    padding-top: 3mm;
  }
  @media print {
    body { margin: 0; padding: 15mm; }
    @page { size: A4; margin: 0; }
  }
</style>
</head>
<body>

<h1>{{TITLE}}</h1>
<p class="meta">Data: {{DATE}} &nbsp;|&nbsp; Nome: _____________________________________ &nbsp;|&nbsp; Turma: ________</p>

<div class="student-id-section">
  <label>Matrícula (preencha um dígito por coluna):</label>
  <div class="id-grid">
    <!-- 9 digit columns -->
    <div class="id-col"><span>D1</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D2</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D3</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D4</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D5</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D6</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D7</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D8</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
    <div class="id-col"><span>D9</span><div class="bubble-row">
      <div class="bubble">0</div></div><div class="bubble-row"><div class="bubble">1</div></div>
      <div class="bubble-row"><div class="bubble">2</div></div><div class="bubble-row"><div class="bubble">3</div></div>
      <div class="bubble-row"><div class="bubble">4</div></div><div class="bubble-row"><div class="bubble">5</div></div>
      <div class="bubble-row"><div class="bubble">6</div></div><div class="bubble-row"><div class="bubble">7</div></div>
      <div class="bubble-row"><div class="bubble">8</div></div><div class="bubble-row"><div class="bubble">9</div></div>
    </div>
  </div>
</div>

<div class="questions-grid">
  <!-- Left column: questions 1–10 -->
  {{QUESTIONS_LEFT}}
  <!-- Right column: questions 11–20 -->
  {{QUESTIONS_RIGHT}}
</div>

<div class="footer">
  super-professor | Gabarito: preencha completamente o círculo da alternativa escolhida com caneta azul ou preta
</div>

</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add templates/answer-sheet.template.html
git commit -m "feat: add printable A4 bubble sheet HTML template"
```

---

## Task 2: OMRChecker Template JSON

**Files:**
- Create: `templates/omr-template.json`

This JSON tells OMRChecker where to find the answer bubbles in a scanned/photographed version of the HTML template above, rendered at 300 DPI (2480 × 3508 px). Values are tuned to match the CSS layout from Task 1.

- [ ] **Step 1: Create the OMRChecker template**

Create `templates/omr-template.json`:

```json
{
  "description": "super-professor standard 20-question A4 sheet",
  "pageDimensions": [2480, 3508],
  "bubbleDimensions": [40, 40],
  "preProcessors": [
    {
      "name": "CropOnMarkers",
      "options": {
        "relativePath": "../markers",
        "sheetToMarkerWidthRatio": 17
      }
    }
  ],
  "fieldBlocks": {
    "StudentID": {
      "fieldType": "QTYPE_INT",
      "origin": [160, 420],
      "fieldLabels": ["D1","D2","D3","D4","D5","D6","D7","D8","D9"],
      "labelsGap": 68,
      "bubblesGap": 52,
      "direction": "horizontal",
      "bubbleValues": ["0","1","2","3","4","5","6","7","8","9"]
    },
    "QLeft": {
      "fieldType": "QTYPE_MCQ4",
      "origin": [160, 1050],
      "fieldLabels": ["q1","q2","q3","q4","q5","q6","q7","q8","q9","q10"],
      "labelsGap": 78,
      "bubblesGap": 62,
      "direction": "vertical",
      "bubbleValues": ["A","B","C","D"]
    },
    "QRight": {
      "fieldType": "QTYPE_MCQ4",
      "origin": [1340, 1050],
      "fieldLabels": ["q11","q12","q13","q14","q15","q16","q17","q18","q19","q20"],
      "labelsGap": 78,
      "bubblesGap": 62,
      "direction": "vertical",
      "bubbleValues": ["A","B","C","D"]
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add templates/omr-template.json
git commit -m "feat: add OMRChecker layout template for standard A4 sheet"
```

---

## Task 3: Assessment Manifest Template

**Files:**
- Create: `templates/assessment-manifest.template.md`

- [ ] **Step 1: Create the manifest template**

Create `templates/assessment-manifest.template.md`:

```markdown
---
schema: super-professor/assessment/v1
status: open
slug: SLUG
generated_at: TIMESTAMP
---

title: TITLE
date: DATE
course_id: COURSE_ID
assignment_id: ASSIGNMENT_ID
questions: 20
answers:
  - Q1: A
  - Q2: B
  - Q3: C
  - Q4: D
  - Q5: A
  - Q6: B
  - Q7: C
  - Q8: D
  - Q9: A
  - Q10: B
  - Q11: C
  - Q12: D
  - Q13: A
  - Q14: B
  - Q15: C
  - Q16: D
  - Q17: A
  - Q18: B
  - Q19: C
  - Q20: D
student_id_field: true
passing_score: 60
```

- [ ] **Step 2: Commit**

```bash
git add templates/assessment-manifest.template.md
git commit -m "feat: add assessment manifest template"
```

---

## Task 4: Score Computation Script (TDD)

**Files:**
- Create: `scripts/compute_scores.py`
- Create: `tests/test_compute_scores.py`

This is the only pure Python logic in the pipeline. It reads `raw-omr.json` (produced by OMRChecker via the omr-processor agent) and `assessment-manifest.md`, computes scores, writes `results/scores.json` and `results/grade-report.md`.

### raw-omr.json shape (produced by OMRChecker via omr-processor agent)

```json
{
  "sheets": [
    {
      "source_file": "sheet-001.jpg",
      "student_id": "202312345",
      "confidence": 0.95,
      "answers": {
        "q1": {"value": "A", "confidence": 0.98},
        "q2": {"value": "C", "confidence": 0.72},
        "q3": {"value": "B", "confidence": 0.91}
      },
      "low_confidence_questions": ["q2"],
      "unreadable": false
    }
  ]
}
```

### scores.json shape (output)

```json
{
  "assessment_slug": "2026-04-20-calculo-p1",
  "generated_at": "2026-04-20T10:00:00",
  "scores": {
    "202312345": {
      "correct": 18,
      "total": 20,
      "score": 90.0,
      "passed": true,
      "source_file": "sheet-001.jpg"
    }
  },
  "unmatched": [],
  "unreadable": []
}
```

- [ ] **Step 1: Write the failing tests**

Create `tests/test_compute_scores.py`:

```python
import json
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from compute_scores import compute_scores, parse_manifest_answers, build_grade_report


ANSWER_KEY = {
    "q1": "A", "q2": "B", "q3": "C", "q4": "D", "q5": "A",
    "q6": "B", "q7": "C", "q8": "D", "q9": "A", "q10": "B",
    "q11": "C", "q12": "D", "q13": "A", "q14": "B", "q15": "C",
    "q16": "D", "q17": "A", "q18": "B", "q19": "C", "q20": "D",
}

PERFECT_SHEET = {
    "source_file": "perfect.jpg",
    "student_id": "111111111",
    "answers": {k: {"value": v, "confidence": 0.99} for k, v in ANSWER_KEY.items()},
    "low_confidence_questions": [],
    "unreadable": False,
}

HALF_CORRECT_SHEET = {
    "source_file": "half.jpg",
    "student_id": "222222222",
    "answers": {
        k: {"value": v if i < 10 else "X", "confidence": 0.95}
        for i, (k, v) in enumerate(ANSWER_KEY.items())
    },
    "low_confidence_questions": [],
    "unreadable": False,
}

UNREADABLE_SHEET = {
    "source_file": "bad.jpg",
    "student_id": None,
    "answers": {},
    "low_confidence_questions": [],
    "unreadable": True,
}

NO_ID_SHEET = {
    "source_file": "noid.jpg",
    "student_id": None,
    "answers": {k: {"value": v, "confidence": 0.99} for k, v in ANSWER_KEY.items()},
    "low_confidence_questions": [],
    "unreadable": False,
}


def make_raw_omr(*sheets):
    return {"sheets": list(sheets)}


def test_perfect_score():
    raw = make_raw_omr(PERFECT_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert result["scores"]["111111111"]["correct"] == 20
    assert result["scores"]["111111111"]["score"] == 100.0
    assert result["scores"]["111111111"]["passed"] is True


def test_half_score():
    raw = make_raw_omr(HALF_CORRECT_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert result["scores"]["222222222"]["correct"] == 10
    assert result["scores"]["222222222"]["score"] == 50.0
    assert result["scores"]["222222222"]["passed"] is False


def test_unreadable_sheet_goes_to_unreadable_list():
    raw = make_raw_omr(UNREADABLE_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert "unreadable" in result
    assert "bad.jpg" in result["unreadable"]
    assert len(result["scores"]) == 0


def test_no_student_id_goes_to_unmatched():
    raw = make_raw_omr(NO_ID_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert "noid.jpg" in result["unmatched"]
    assert len(result["scores"]) == 0


def test_mixed_sheets():
    raw = make_raw_omr(PERFECT_SHEET, UNREADABLE_SHEET, NO_ID_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert len(result["scores"]) == 1
    assert len(result["unreadable"]) == 1
    assert len(result["unmatched"]) == 1


def test_parse_manifest_answers():
    manifest_text = """---
title: Test
answers:
  - Q1: A
  - Q2: B
  - Q3: C
  - Q4: D
  - Q5: A
  - Q6: B
  - Q7: C
  - Q8: D
  - Q9: A
  - Q10: B
  - Q11: C
  - Q12: D
  - Q13: A
  - Q14: B
  - Q15: C
  - Q16: D
  - Q17: A
  - Q18: B
  - Q19: C
  - Q20: D
passing_score: 60
---"""
    key, passing = parse_manifest_answers(manifest_text)
    assert key["q1"] == "A"
    assert key["q20"] == "D"
    assert passing == 60


def test_build_grade_report_contains_summary():
    scores = {
        "111111111": {"correct": 20, "total": 20, "score": 100.0, "passed": True, "source_file": "f.jpg"},
        "222222222": {"correct": 10, "total": 20, "score": 50.0, "passed": False, "source_file": "g.jpg"},
    }
    report = build_grade_report("2026-04-20-calculo-p1", scores, unmatched=[], unreadable=[])
    assert "111111111" in report
    assert "100.0" in report
    assert "50.0" in report
    assert "Aprovados: 1" in report
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd /Users/demetrios/Projects/super_professor
python -m pytest tests/test_compute_scores.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'compute_scores'`

- [ ] **Step 3: Implement compute_scores.py**

Create `scripts/compute_scores.py`:

```python
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_manifest_answers(manifest_text: str) -> tuple[dict, int]:
    """Parse answer key and passing score from manifest markdown text.
    Returns (answer_key dict with lowercase q-keys, passing_score int).
    """
    answer_key = {}
    passing_score = 60

    for line in manifest_text.splitlines():
        m = re.match(r"\s*-\s*Q(\d+):\s*([ABCD])", line)
        if m:
            answer_key[f"q{m.group(1)}"] = m.group(2)
        ps = re.match(r"passing_score:\s*(\d+)", line.strip())
        if ps:
            passing_score = int(ps.group(1))

    return answer_key, passing_score


def compute_scores(raw_omr: dict, answer_key: dict, passing_score: int = 60) -> dict:
    """Compare OMR detections to answer key. Returns structured result dict."""
    scores = {}
    unmatched = []
    unreadable = []

    for sheet in raw_omr["sheets"]:
        if sheet.get("unreadable"):
            unreadable.append(sheet["source_file"])
            continue

        student_id = sheet.get("student_id")
        if not student_id:
            unmatched.append(sheet["source_file"])
            continue

        total = len(answer_key)
        correct = sum(
            1
            for q, expected in answer_key.items()
            if sheet["answers"].get(q, {}).get("value") == expected
        )
        score = round(correct / total * 100, 1) if total > 0 else 0.0

        scores[student_id] = {
            "correct": correct,
            "total": total,
            "score": score,
            "passed": score >= passing_score,
            "source_file": sheet["source_file"],
        }

    return {"scores": scores, "unmatched": unmatched, "unreadable": unreadable}


def build_grade_report(slug: str, scores: dict, unmatched: list, unreadable: list) -> str:
    """Build a markdown grade report string."""
    lines = [
        f"# Relatório de Notas — {slug}",
        f"\nGerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "\n## Resultados\n",
        "| Matrícula | Acertos | Total | Nota | Situação |",
        "|-----------|---------|-------|------|----------|",
    ]
    approved = 0
    for sid, data in sorted(scores.items()):
        situation = "Aprovado" if data["passed"] else "Reprovado"
        if data["passed"]:
            approved += 1
        lines.append(
            f"| {sid} | {data['correct']} | {data['total']} | {data['score']} | {situation} |"
        )

    lines.append(f"\n**Aprovados: {approved} / {len(scores)}**")

    if unmatched:
        lines.append("\n## Sem matrícula identificada\n")
        for f in unmatched:
            lines.append(f"- {f}")

    if unreadable:
        lines.append("\n## Folhas ilegíveis\n")
        for f in unreadable:
            lines.append(f"- {f}")

    return "\n".join(lines)


def main():
    """CLI: compute_scores.py <raw-omr.json> <assessment-manifest.md> <output-dir>"""
    if len(sys.argv) != 4:
        print("Usage: compute_scores.py <raw-omr.json> <manifest.md> <output-dir>")
        sys.exit(1)

    raw_omr_path = Path(sys.argv[1])
    manifest_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    raw_omr = json.loads(raw_omr_path.read_text())
    manifest_text = manifest_path.read_text()
    answer_key, passing_score = parse_manifest_answers(manifest_text)

    slug = output_dir.parent.name
    result = compute_scores(raw_omr, answer_key, passing_score)
    result["assessment_slug"] = slug
    result["generated_at"] = datetime.now().isoformat()

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scores.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    report = build_grade_report(slug, result["scores"], result["unmatched"], result["unreadable"])
    (output_dir / "grade-report.md").write_text(report)

    print(f"Scores: {len(result['scores'])} alunos")
    print(f"Sem matrícula: {len(result['unmatched'])}")
    print(f"Ilegíveis: {len(result['unreadable'])}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
cd /Users/demetrios/Projects/super_professor
python -m pytest tests/test_compute_scores.py -v
```

Expected output: all 7 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add scripts/compute_scores.py tests/test_compute_scores.py
git commit -m "feat: add score computation script with full test coverage"
```

---

## Task 5: OMR Processor Agent

**Files:**
- Create: `agents/omr-processor.md`

This subagent is dispatched once per photo by `/assessment-grade`. It runs OMRChecker on a single image, then returns structured JSON. It does NOT score — only detects.

- [ ] **Step 1: Create the agent**

Create `agents/omr-processor.md`:

```markdown
---
name: omr-processor
description: Run OMRChecker on a single answer sheet photo and return detected bubble values as JSON. Never scores. Never modifies the original photo.
---

You process one answer sheet image using OMRChecker and return the detected answers.

## Inputs (provided in the task prompt)
- `photo_path`: absolute path to the photo file (jpg or png)
- `omr_template_path`: absolute path to `templates/omr-template.json`
- `output_dir`: directory where OMRChecker should write its output

## Step 1: Check OMRChecker is installed

```bash
python -m omrchecker --version 2>&1
```

If the command fails with "No module named omrchecker", stop and return:
```json
{"error": "omrchecker_not_installed", "message": "Run: pip install omrchecker"}
```

## Step 2: Run OMRChecker

```bash
python -m omrchecker \
  --inputDir "$(dirname {{photo_path}})" \
  --outputDir "{{output_dir}}" \
  --template "{{omr_template_path}}"
```

OMRChecker writes a CSV result file to `{{output_dir}}/Results/`.

## Step 3: Parse the CSV output

Read the CSV file from `{{output_dir}}/Results/`. It has one row per processed image with columns for each field block defined in the template (StudentID, q1–q20) plus a confidence score column.

## Step 4: Return structured JSON

Return ONLY this JSON structure — nothing else:

```json
{
  "source_file": "sheet-001.jpg",
  "student_id": "202312345",
  "answers": {
    "q1": {"value": "A", "confidence": 0.98},
    "q2": {"value": "B", "confidence": 0.73}
  },
  "low_confidence_questions": ["q2"],
  "unreadable": false
}
```

Rules:
- `student_id`: join the 9 digit columns from StudentID block. If any digit is blank or ambiguous, set `student_id` to `null`.
- `low_confidence_questions`: list of question keys where confidence < 0.80
- `unreadable`: set to `true` if OMRChecker fails entirely or reports the sheet as unprocessable
- If `unreadable` is true: return empty `answers`, null `student_id`, empty `low_confidence_questions`

## GUARDRAILS
- NEVER modify the source photo
- NEVER score the answers — only detect and report
- Return ONLY the JSON above — no extra text
```

- [ ] **Step 2: Commit**

```bash
git add agents/omr-processor.md
git commit -m "feat: add omr-processor subagent"
```

---

## Task 6: Vision Grader Agent

**Files:**
- Create: `agents/vision-grader.md`

Dispatched by `/assessment-grade` for each question flagged as low-confidence. Re-evaluates by looking at the photo directly.

- [ ] **Step 1: Create the agent**

Create `agents/vision-grader.md`:

```markdown
---
name: vision-grader
description: Re-evaluate one or more low-confidence bubble detections on an answer sheet photo using vision. Returns corrected answer values. Never scores.
---

You look at a physical answer sheet photo and determine which option is filled for specific questions.

## Inputs (provided in the task prompt)
- `photo_path`: absolute path to the photo
- `questions`: list of question numbers to re-evaluate (e.g., ["q2", "q7"])
- `omr_answers`: the answers OMRChecker detected for these questions (for reference)

## Your job

Read the photo at `{{photo_path}}`.

For each question in `{{questions}}`:
1. Locate the question row on the sheet (the sheet has two columns, questions 1–10 on the left, 11–20 on the right)
2. Identify which bubble (A, B, C, or D) is clearly filled
3. If genuinely ambiguous after careful inspection, report `"?"` as the value

## Output

Return ONLY this JSON — no extra text:

```json
{
  "corrections": {
    "q2": {"value": "B", "confidence": 0.95},
    "q7": {"value": "?", "confidence": 0.40}
  }
}
```

- Confidence should reflect how certain you are (0.0–1.0)
- Use `"?"` only when you truly cannot determine the answer
- `"?"` answers are treated as wrong by the scoring step

## GUARDRAILS
- NEVER score — only identify filled bubbles
- NEVER guess when genuinely ambiguous — use `"?"`
- Return ONLY the JSON structure above
```

- [ ] **Step 2: Commit**

```bash
git add agents/vision-grader.md
git commit -m "feat: add vision-grader subagent for low-confidence fallback"
```

---

## Task 7: `/assessment-create` Skill

**Files:**
- Create: `skills/assessment-create/SKILL.md`

- [ ] **Step 1: Create the skill**

Create `skills/assessment-create/SKILL.md`:

```markdown
---
name: assessment-create
description: Create a new paper assessment. Collects title, date, Google Classroom IDs, and answer key interactively. Produces assessment-manifest.md and a printable answer-sheet.html. One question per message.
---

You are collecting the assessment parameters from the teacher through focused conversation.

## BEFORE STARTING

Check if there is already a `.super-professor/repo-manifest.md` in the current repo. If present, use `course_id` from it if available. Otherwise proceed.

## Fields to collect

- `title` — assessment title (e.g., "Prova P1 — Cálculo I")
- `date` — assessment date (default: today's date)
- `course_id` — Google Classroom course ID (teacher must provide; explain: "Acesse o Google Classroom → Configurações da turma → ID da turma")
- `assignment_id` — Google Classroom assignment ID (teacher must create the assignment in Classroom first, then provide the ID from the assignment URL)
- `answers` — the answer key: 20 letters, one per question (A, B, C, or D)
- `passing_score` — minimum percentage to pass (default: 60)

## Conversation rules

- Ask EXACTLY ONE question per message
- If the teacher provides multiple fields at once, accept all and ask only what's still missing
- Do not repeat questions about fields already provided

## Question order

1. "Qual é o título desta avaliação?" (e.g., "Prova P1 — Cálculo I")
2. "Qual é a data da avaliação?" (default: today)
3. "Qual é o ID da turma no Google Classroom?" (explain where to find it if needed)
4. "Qual é o ID da atividade no Google Classroom?" (explain: create the assignment first, then get the ID from the URL)
5. "Informe o gabarito das 20 questões, uma por vez ou todas de uma vez (A, B, C ou D por questão)."
6. "Qual é a nota mínima para aprovação? (padrão: 60%)"

## After collecting all fields

### 1. Generate the slug

Format: `<YYYY-MM-DD>-<title-slug>`
- Convert title to lowercase kebab-case, no accents
- Example: `2026-04-20-prova-p1-calculo-i`

### 2. Create the assessment directory

```
assessments/<slug>/
assessments/<slug>/photos/
assessments/<slug>/results/
assessments/<slug>/results/unmatched/
```

### 3. Write assessment-manifest.md

Copy `templates/assessment-manifest.template.md`. Fill every placeholder with the collected values. Write to `assessments/<slug>/assessment-manifest.md`.

### 4. Generate answer-sheet.html

Read `templates/answer-sheet.template.html`. Replace:
- `{{TITLE}}` → the assessment title
- `{{DATE}}` → the assessment date
- `{{QUESTIONS_LEFT}}` → HTML for questions 1–10 (see format below)
- `{{QUESTIONS_RIGHT}}` → HTML for questions 11–20

Question HTML format (repeat for each question number):
```html
<div class="question-row">
  <span class="q-num">1.</span>
  <div class="options">
    <div class="option"><span>A</span><div class="opt-bubble"></div></div>
    <div class="option"><span>B</span><div class="opt-bubble"></div></div>
    <div class="option"><span>C</span><div class="opt-bubble"></div></div>
    <div class="option"><span>D</span><div class="opt-bubble"></div></div>
  </div>
</div>
```

Write to `assessments/<slug>/answer-sheet.html`.

### 5. Copy OMR template

Copy `templates/omr-template.json` to `assessments/<slug>/omr-template.json`.

### 6. Confirm to the teacher

Say:
"Avaliação criada em `assessments/<slug>/`.

- **Gabarito**: salvo em `assessment-manifest.md`
- **Folha de resposta**: `answer-sheet.html` — abra no navegador e imprima (Ctrl+P), selecione A4

Após a prova, coloque as fotos das folhas em `assessments/<slug>/photos/` e execute `/assessment-grade`."

## GUARDRAILS

- NEVER write assessment-manifest.md before all fields are collected and confirmed
- NEVER invent answers — only use what the teacher provides
- NEVER create the assignment in Google Classroom — teacher must do that manually first
```

- [ ] **Step 2: Commit**

```bash
git add skills/assessment-create/SKILL.md
git commit -m "feat: add /assessment-create skill"
```

---

## Task 8: `/assessment-grade` Skill

**Files:**
- Create: `skills/assessment-grade/SKILL.md`

- [ ] **Step 1: Create the skill**

Create `skills/assessment-grade/SKILL.md`:

```markdown
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

Merge the corrections back into the sheet result: for each corrected question, replace `value` and `confidence` with the vision-grader's values.

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

## Step 6: Report to teacher

Read `assessments/<slug>/results/grade-report.md` and display it.

Then say:
"Resultados salvos em `assessments/<slug>/results/`.
- `scores.json` — dados para integração
- `grade-report.md` — tabela de notas

Execute `/assessment-sync` para enviar as notas ao Google Classroom."

## GUARDRAILS

- NEVER modify original photos
- NEVER skip the Vision fallback step when low_confidence_questions is non-empty
- NEVER proceed to scoring if compute_scores.py exits with a non-zero code — surface the error
- NEVER send grades to Classroom — that is `/assessment-sync`'s job
```

- [ ] **Step 2: Commit**

```bash
git add skills/assessment-grade/SKILL.md
git commit -m "feat: add /assessment-grade skill"
```

---

## Task 9: `/assessment-sync` Skill

**Files:**
- Create: `skills/assessment-sync/SKILL.md`

- [ ] **Step 1: Create the skill**

Create `skills/assessment-sync/SKILL.md`:

```markdown
---
name: assessment-sync
description: Post computed assessment scores to Google Classroom using the gws CLI. Run after /assessment-grade has produced scores.json.
---

You are syncing computed scores to Google Classroom via the gws CLI.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da avaliação? (ex: `2026-04-20-prova-p1-calculo-i`)"
2. Verify `assessments/<slug>/results/scores.json` exists. If not: stop and say "Execute `/assessment-grade` primeiro."
3. Check gws is available:
   ```bash
   gws --version 2>&1
   ```
   If it fails: stop and say "gws CLI não encontrado. Instale conforme as instruções em https://github.com/demetrioscoutinho/gws ou equivalente."

## Step 1: Read manifest and scores

Read:
- `assessments/<slug>/assessment-manifest.md` → extract `course_id` and `assignment_id`
- `assessments/<slug>/results/scores.json` → load the scores dict

## Step 2: Fetch the Classroom roster

```bash
gws classroom courses students list \
  --params '{"courseId": "<course_id>", "pageSize": 200}'
```

Parse the JSON response. Build a map: `student_email → userId` from the `students[].profile.emailAddress` and `students[].userId` fields.

## Step 3: Fetch existing submissions

```bash
gws classroom courses courseWork studentSubmissions list \
  --params '{"courseId": "<course_id>", "courseWorkId": "<assignment_id>", "pageSize": 200}'
```

Parse the JSON. Build a map: `userId → submissionId` from `studentSubmissions[].userId` and `studentSubmissions[].id`.

## Step 4: Match scores to submissions

For each entry in `scores.json["scores"]`:
- `student_id` (matrícula from the bubble sheet) must be matched to a Classroom `userId`.

**Matching strategy:** The `student_id` from the answer sheet is the student's enrollment number, not their email. The teacher must have previously provided a mapping file or the student's Google email contains their ID.

Check if `assessments/<slug>/student-map.csv` exists. If it does, read it — format: `student_id,email` (one per line, no header). Use it to map `student_id → email → userId`.

If `student-map.csv` does not exist: stop and say:
"Para enviar notas, é necessário um arquivo `assessments/<slug>/student-map.csv` com o formato:
```
matricula,email
202312345,joao@escola.edu
202398765,maria@escola.edu
```
Crie o arquivo e execute `/assessment-sync` novamente."

## Step 5: Post grades

For each matched student, run:

```bash
gws classroom courses courseWork studentSubmissions patch \
  --params '{"courseId":"<course_id>","courseWorkId":"<assignment_id>","id":"<submission_id>","updateMask":"assignedGrade,draftGrade"}' \
  --json '{"assignedGrade": <score>, "draftGrade": <score>}'
```

Where `<score>` is the numeric value from `scores.json["scores"][student_id]["score"]`.

Collect success/failure for each student.

## Step 6: Write sync status and report

Write `assessments/<slug>/classroom-sync.json`:

```json
{
  "synced_at": "<ISO timestamp>",
  "course_id": "<course_id>",
  "assignment_id": "<assignment_id>",
  "posted": ["202312345", "202398765"],
  "unmatched": ["202311111"],
  "errors": []
}
```

Report to teacher:
"Notas enviadas ao Google Classroom.
- Enviadas: N alunos
- Sem correspondência: M alunos (listados acima — adicione ao student-map.csv e reexecute)"

## GUARDRAILS

- NEVER post grades without a confirmed scores.json
- NEVER invent userId or submissionId — always fetch from gws
- NEVER skip unmatched reporting — list every unmatched student_id explicitly
- Surface gws error output verbatim if any gws command fails
```

- [ ] **Step 2: Commit**

```bash
git add skills/assessment-sync/SKILL.md
git commit -m "feat: add /assessment-sync skill"
```

---

## Task 10: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add new skills to the skills table**

In `CLAUDE.md`, add these rows to the `## Skills disponíveis` table:

```markdown
| /assessment-create | Cria avaliação impressa (gabarito + folha de respostas PDF) | Nenhum |
| /assessment-grade  | Corrige folhas fotografadas via OMRChecker + Claude Vision | photos/ preenchido |
| /assessment-sync   | Envia notas ao Google Classroom via gws CLI | scores.json + student-map.csv |
```

Also add a new section at the bottom:

```markdown
## Assessment pipeline

```
/assessment-create "Prova P1"    # cria gabarito e folha de respostas
/assessment-grade                # corrige fotos → scores.json
/assessment-sync                 # envia notas ao Google Classroom
```

Pré-requisito externo: `pip install omrchecker` e `gws` CLI autenticado.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add assessment pipeline skills to CLAUDE.md"
```

---

## Task 11: End-to-End Smoke Test

- [ ] **Step 1: Run the full Python test suite**

```bash
cd /Users/demetrios/Projects/super_professor
python -m pytest tests/ -v
```

Expected: all tests `PASSED`.

- [ ] **Step 2: Verify file tree is complete**

```bash
find skills/assessment-create skills/assessment-grade skills/assessment-sync \
     agents/omr-processor.md agents/vision-grader.md \
     templates/assessment-manifest.template.md \
     templates/answer-sheet.template.html \
     templates/omr-template.json \
     scripts/compute_scores.py \
     -type f | sort
```

Expected output (11 paths, all present):
```
agents/omr-processor.md
agents/vision-grader.md
scripts/compute_scores.py
skills/assessment-create/SKILL.md
skills/assessment-grade/SKILL.md
skills/assessment-sync/SKILL.md
templates/answer-sheet.template.html
templates/assessment-manifest.template.md
templates/omr-template.json
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git status
# Confirm only expected files are staged, then:
git commit -m "feat: complete paper assessment grading pipeline v1

- /assessment-create: generates manifest + printable HTML bubble sheet
- /assessment-grade: OMRChecker + Claude Vision fallback + score computation
- /assessment-sync: posts grades to Google Classroom via gws CLI
- compute_scores.py: fully tested score computation script
- Fixed A4 layout + matching omr-template.json for reliable OMR detection"
```

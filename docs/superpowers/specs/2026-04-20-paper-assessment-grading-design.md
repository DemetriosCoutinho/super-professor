# Paper Assessment Grading System — Design Spec

**Date:** 2026-04-20
**Plugin:** super_professor
**Status:** Approved

---

## Overview

Adds a paper assessment pipeline to the super_professor plugin. Teachers create multiple-choice answer sheets, photograph completed sheets (mobile or scanner), and grades are posted automatically to Google Classroom.

**Scope (v1):** Multiple-choice only. Grade posting only (no PDF reports, no assignment creation from Classroom). Start simple, expand later.

**Target class size:** 30–100 students.

---

## Architecture

Three new skills and one local Python service (OMRChecker CLI):

```
Teacher                    super_professor agent          External
  │                               │                          │
  ├─ /assessment-create ──────────► generates PDF            │
  │   (questions + answer key)    ► stores answer key        │
  │                               │                          │
  ├─ photos of filled sheets ─────► /assessment-grade        │
  │                               ► OMRChecker service ──────► detect bubbles
  │                               ► Claude Vision (fallback) │
  │                               ► compute scores           │
  │                               │                          │
  └─ /assessment-sync ────────────────────────────────────────► Google Classroom API
                                                              ► post grades
```

### New Skills

| Skill | Purpose |
|-------|---------|
| `/assessment-create` | Takes questions + answer key, outputs printable PDF answer sheet |
| `/assessment-grade` | Accepts photo uploads, runs OMRChecker, falls back to Claude Vision, returns scores |
| `/assessment-sync` | Posts computed scores to a Google Classroom assignment |

### External Dependencies

- **OMRChecker** (`pip install omrchecker`) — open-source Python OMR library, runs as local CLI, no server needed
- **Google Classroom API** — OAuth 2.0, standard REST API
- **Claude Vision** — fallback for low-confidence bubble detections only

---

## Data Structure

Each assessment lives in `assessments/<YYYY-MM-DD-slug>/` inside the academic repo:

```
assessments/
└── 2026-04-20-calculo-p1/
    ├── assessment-manifest.md   # metadata, answer key
    ├── answer-sheet.pdf         # printable bubble sheet
    ├── photos/                  # raw teacher-uploaded photos
    │   ├── sheet-001.jpg
    │   └── sheet-002.jpg
    ├── results/
    │   ├── raw-omr.json         # OMRChecker output per photo
    │   ├── scores.json          # final scores per student
    │   └── grade-report.md      # summary table
    └── classroom-sync.json      # sync status with Google Classroom
```

### assessment-manifest.md schema

```markdown
# Assessment Manifest

title: Prova P1 — Cálculo I
date: 2026-04-20
course_id: <Google Classroom course ID>
assignment_id: <Google Classroom assignment ID>
questions: 20
answers: [A, C, B, D, A, B, C, D, A, B, C, D, A, B, C, D, A, B, C, D]
student_id_field: true
passing_score: 60
```

---

## Grading Pipeline (`/assessment-grade`)

1. Teacher uploads photos to `assessments/<slug>/photos/`
2. Agent calls OMRChecker CLI on each photo → detects filled bubbles → outputs `raw-omr.json`
3. Any bubble with confidence < 80% is flagged → Claude Vision re-evaluates that question only
4. Scores computed against answer key from `assessment-manifest.md`
5. Results written to `scores.json` and `grade-report.md`
6. Agent reports unreadable sheets and unmatched IDs for manual review

### Confidence threshold

- **≥ 80%:** OMRChecker result accepted
- **< 80%:** Claude Vision re-evaluates the specific question bubble(s) only
- **Unreadable sheet:** Moved to `results/unmatched/` with a note; agent lists them at end of run

---

## Google Classroom Integration (`/assessment-sync`)

### Authentication

- OAuth 2.0 flow; browser prompt on first run
- Credentials stored in `.super-professor/google-credentials.json` (gitignored)

### Required OAuth Scopes

- `https://www.googleapis.com/auth/classroom.coursework.students` — post grades
- `https://www.googleapis.com/auth/classroom.rosters.readonly` — match student IDs to roster

### Sync Flow

1. Read `scores.json`
2. Fetch Google Classroom roster for `course_id`
3. Match student IDs from answer sheets to roster
4. For each matched student: `PATCH /v1/courses/{courseId}/courseWork/{courseWorkId}/studentSubmissions/{id}` with grade
5. Unmatched students listed in output for manual resolution
6. Write sync status to `classroom-sync.json`

### v1 Limitations (by design)

- Assignment must be created in Google Classroom by the teacher first; skill takes `assignment_id` as input
- No PDF report returned to students
- No partial credit
- No retake/regrade flow

---

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Photo too blurry/dark | Sheet flagged as unreadable, listed for manual review |
| Student ID not in roster | Score held in `unmatched/`, reported to teacher |
| Google API auth failure | Clear error with re-auth instructions |
| OMRChecker not installed | Agent detects missing dep, prints install command |

---

## Out of Scope (v1)

- Open-ended / short-answer grading
- Batch scanner integration (works via file upload, not native integration)
- Creating Google Classroom assignments from the skill
- Returning graded reports to students
- Web UI or mobile app

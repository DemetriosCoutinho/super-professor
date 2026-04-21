---
name: assessment-sync-check
description: Preflight dry-run for /assessment-sync. Validates gws connectivity, Classroom roster, assignment submissions, and student-map.csv matching WITHOUT posting any grades. Run before /assessment-sync to catch mismatches early.
---

You are running a preflight check for Google Classroom grade sync. NO grades will be posted.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da avaliação? (ex: `2026-04-20-prova-p1-calculo-i`)"
2. Verify `assessments/<slug>/results/scores.json` exists.
3. Verify `assessments/<slug>/assessment-manifest.md` exists and contains `course_id` and `assignment_id`.
4. Verify `assessments/<slug>/student-map.csv` exists.

If any file is missing, list all missing files and stop.

## Check 1: gws CLI

```bash
gws --version 2>&1
```

Result: `pass` if exits 0, `fail` otherwise. If fail, stop and say "gws CLI não encontrado."

## Check 2: Course roster

```bash
gws classroom courses students list \
  --params '{"courseId": "<course_id>", "pageSize": 200}'
```

- `pass` if response contains at least 1 student
- `fail` if error or empty
- Record: `roster_count` = number of students returned

## Check 3: Assignment submissions

```bash
gws classroom courses courseWork studentSubmissions list \
  --params '{"courseId": "<course_id>", "courseWorkId": "<assignment_id>", "pageSize": 200}'
```

- `pass` if response contains at least 1 submission
- `fail` if error or empty
- Record: `submissions_count` = number of submissions returned

## Check 4: student-map.csv matching

Read `assessments/<slug>/student-map.csv` (format: `matricula,email`, no header).
Cross-reference with roster:
- Build map: `email → userId` from roster
- For each row in student-map.csv: check if `email` appears in roster
- Record: `matched_count`, `unmatched_list` (student_ids with no roster match)

## Check 5: End-to-end lookup (one student)

Pick the first student from scores.json that has a match in student-map.csv and roster.
Verify the full chain: `student_id → email → userId → submissionId`.
Record: `sample_student_id`, `chain_ok: true/false`.

## Output

Write `assessments/<slug>/sync-preflight.json`:

```json
{
  "checked_at": "<ISO timestamp>",
  "slug": "<slug>",
  "course_id": "<course_id>",
  "assignment_id": "<assignment_id>",
  "checks": {
    "gws_cli": "pass|fail",
    "course_roster": "pass|fail",
    "assignment_submissions": "pass|fail",
    "student_map_matching": "pass|fail"
  },
  "roster_count": 0,
  "submissions_count": 0,
  "matched_count": 0,
  "unmatched_students": [],
  "sample_lookup": {
    "student_id": "",
    "chain_ok": false
  }
}
```

Report to teacher:

```
Preflight concluído para <slug>:
  ✓/✗ gws CLI
  ✓/✗ Roster do Classroom (<N> alunos)
  ✓/✗ Submissions do assignment (<N> submissions)
  ✓/✗ student-map.csv (<matched>/<total> correspondências)
  ✓/✗ Lookup end-to-end (aluno <id>)

[Se algum item ✗]: Corrija os itens acima antes de executar /assessment-sync.
[Se todos ✓]: Preflight passou — execute /assessment-sync para postar as notas.
```

## GUARDRAILS

- NEVER call any PATCH, POST, or PUT endpoint
- NEVER modify scores.json or any assessment artifact
- Surface gws error output verbatim if any command fails
- If any check fails, do NOT write a partial sync-preflight.json — write the full file with fail status and stop before recommending /assessment-sync

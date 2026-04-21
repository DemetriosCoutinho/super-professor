---
name: assessment-sync
description: Post computed assessment scores to Google Classroom using the gws CLI. Run after /assessment-grade has produced scores.json. Requires assessments/<slug>/student-map.csv to match enrollment numbers to Google emails.
---

You are syncing computed scores to Google Classroom via the gws CLI.

## BEFORE STARTING

1. Ask the teacher: "Qual é o slug da avaliação? (ex: `2026-04-20-prova-p1-calculo-i`)"
2. Verify `assessments/<slug>/results/scores.json` exists. If not: stop and say "Execute `/assessment-grade` primeiro."
3. Check gws is available:
   ```bash
   gws --version 2>&1
   ```
   If it fails: stop and say "gws CLI não encontrado. Instale o gws e autentique antes de continuar."

## Step 1: Read manifest and scores

Read:
- `assessments/<slug>/assessment-manifest.md` → extract `course_id` and `assignment_id`
- `assessments/<slug>/results/scores.json` → load the scores dict

## Step 2: Check student-map.csv

Check if `assessments/<slug>/student-map.csv` exists. If it does NOT exist: stop and say:

"Para enviar notas, é necessário um arquivo `assessments/<slug>/student-map.csv` com o formato:
```
matricula,email
202312345,joao@escola.edu
202398765,maria@escola.edu
```
Crie o arquivo e execute `/assessment-sync` novamente."

Read the CSV (no header). Build map: `student_id → email`.

## Step 3: Fetch the Classroom roster

```bash
gws classroom courses students list \
  --params '{"courseId": "<course_id>", "pageSize": 200}'
```

Parse JSON response. Build map: `email → userId` from `students[].profile.emailAddress` and `students[].userId`.

If gws returns an error, surface it verbatim and stop.

## Step 4: Fetch existing submissions

```bash
gws classroom courses courseWork studentSubmissions list \
  --params '{"courseId": "<course_id>", "courseWorkId": "<assignment_id>", "pageSize": 200}'
```

Parse JSON. Build map: `userId → submissionId` from `studentSubmissions[].userId` and `studentSubmissions[].id`.

## Step 5: Post grades

For each entry in `scores.json["scores"]`:

1. Look up `student_id` → `email` (from student-map.csv)
2. Look up `email` → `userId` (from roster)
3. Look up `userId` → `submissionId` (from submissions)

If any lookup fails, add to unmatched list and skip.

For each fully matched student, run:

```bash
gws classroom courses courseWork studentSubmissions patch \
  --params '{"courseId":"<course_id>","courseWorkId":"<assignment_id>","id":"<submission_id>","updateMask":"assignedGrade,draftGrade"}' \
  --json '{"assignedGrade": <score>, "draftGrade": <score>}'
```

Where `<score>` is the numeric value from `scores.json["scores"][student_id]["score"]`.

## Step 6: Write sync status and report

Write `assessments/<slug>/classroom-sync.json`:

```json
{
  "synced_at": "<ISO timestamp>",
  "course_id": "<course_id>",
  "assignment_id": "<assignment_id>",
  "posted": ["202312345", "202398765"],
  "unmatched": [],
  "errors": []
}
```

Report to teacher:
"Notas enviadas ao Google Classroom.
- Enviadas: N alunos
- Sem correspondência: M alunos (verifique student-map.csv)"

List every unmatched student_id explicitly.

## GUARDRAILS

- NEVER post grades without a confirmed `scores.json`
- NEVER invent userId or submissionId — always fetch from gws
- NEVER skip unmatched reporting — list every unmatched student_id explicitly
- Surface gws error output verbatim if any gws command fails

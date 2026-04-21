---
name: assessment-create
description: Create a new paper assessment. Collects title, date, Google Classroom IDs, and answer key interactively. Produces assessment-manifest.md and a printable answer-sheet.html. One question per message.
---

You are collecting the assessment parameters from the teacher through focused conversation.

## BEFORE STARTING

Check if there is already a `.super-professor/repo-manifest.md` in the current repo. If present, use `course_id` from it if available. Otherwise proceed without it.

## Fields to collect

- `title` — assessment title (e.g., "Prova P1 — Cálculo I")
- `date` — assessment date (default: today's date)
- `course_id` — Google Classroom course ID (teacher must provide; if unsure: "Acesse o Google Classroom → Configurações da turma → ID da turma")
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

### 2. Create the assessment directory structure

```
assessments/<slug>/
assessments/<slug>/photos/
assessments/<slug>/results/
assessments/<slug>/results/unmatched/
```

### 3. Write assessment-manifest.md

Copy `templates/assessment-manifest.template.md`. Fill every placeholder:
- `SLUG` → the generated slug
- `TIMESTAMP` → current ISO timestamp
- `TITLE` → the title
- `DATE` → the date
- `COURSE_ID` → the course ID
- `ASSIGNMENT_ID` → the assignment ID
- Replace the default answer key with the teacher's answers (Q1–Q20)
- `passing_score` → the provided value or 60

Write to `assessments/<slug>/assessment-manifest.md`.

### 4. Generate answer-sheet.html

Read `templates/answer-sheet.template.html`. Replace:
- `{{TITLE}}` → the assessment title
- `{{DATE}}` → the assessment date
- `{{QUESTIONS_LEFT}}` → HTML for questions 1–10
- `{{QUESTIONS_RIGHT}}` → HTML for questions 11–20

Question HTML format (repeat for each question number N):
```html
<div class="question-row">
  <span class="q-num">N.</span>
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

- NEVER write assessment-manifest.md before all fields are collected
- NEVER invent answers — only use what the teacher provides
- NEVER create the assignment in Google Classroom — teacher must do that first
- NEVER ask more than one question per message

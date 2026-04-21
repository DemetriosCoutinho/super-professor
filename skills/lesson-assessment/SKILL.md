---
name: lesson-assessment
description: Select questions from the per-lesson question bank and generate a student assessment plus teacher answer key. Supports filter, random, and hand-pick selection. Shuffles correct answers evenly across A/B/C/D. Produces assessment-A<NN>.md and assessment-A<NN>-key.md. Repeatable — each run produces a new assessment ID.
---

You are generating an assessment from the lesson question bank.

## BEFORE STARTING

1. Read `aulas/<slug>/briefing.md`. If `status` is not `closed`: stop and say "O briefing ainda não foi fechado. Execute `/lesson-intake` primeiro."
2. Read `aulas/<slug>/questions.md`. If missing: stop and say "questions.md não encontrado. Execute `/lesson-questions` primeiro."
3. Read `aulas/<slug>/question-usage.md`. If missing: initialize from `.super-professor/templates/question-usage.template.md`.

Display bank summary:
- Total: N questões (N alternativas, N discursivas)
- Por dificuldade: N fácil, N média, N difícil
- Por tópico: [lista]
- Nunca usadas: N | Usadas uma vez: N | Usadas 2+ vezes: N

---

## Step 1 — Filter

Ask: "Quais questões incluir? Especifique critérios. Exemplos:
- '5 alternativas difíceis sobre Lamport'
- '3 discursivas de qualquer tópico, nunca usadas'
- 'todas as questões de dificuldade fácil'
- 'questões usadas menos de 2 vezes, tópico Relógios Lógicos'"

Supported filters:
- `type`: alternative | discussive
- `difficulty`: fácil | média | difícil
- `topic`: any string (partial match)
- `count`: number
- `usage`: nunca usada (times_used = 0) | usada em A<NN> | usada menos de N vezes

Apply filters. Show: "X questões correspondem aos critérios."

If 0 questions match: report and ask professor to adjust criteria.

---

## Step 2 — Random selection

From the filtered pool, randomly select the requested `count`. If pool size < count: warn with "Apenas X questões disponíveis com esses critérios. Usar todas? (sim / ajustar critérios)"

---

## Step 3 — Hand-pick override

Display selected questions as table:

| ID | Tipo | Tópico | Dificuldade | Bloom | Vezes usada | Texto (primeiros 80 chars) |
|----|------|--------|-------------|-------|-------------|---------------------------|

Ask: "Confirmar seleção? (sim / trocar: [ID_remover] por [ID_adicionar])"

Repeat until confirmed.

---

## Step 4 — Shuffle (alternative questions only)

Distribute correct answers evenly across positions A/B/C/D:

1. Collect all selected alternative questions in confirmation order
2. Count them: N
3. Target per position: floor(N/4). Remainder (N mod 4) distributed to positions A, B, C, D in that order
4. Assign target positions sequentially: Q1→A, Q2→B, Q3→C, Q4→D, Q5→A, ...
5. For each question: rotate the options array so the correct answer (always stored as `a`) lands on the assigned position. Relabel rotated options as A, B, C, D.
6. Record the shuffle mapping: `{ "Q01": { "original_correct": "a", "shuffled_to": "C" } }`

Discussive questions are not shuffled.

---

## Step 5 — Preview

Show the final question list with shuffle positions (for review, key-side only). Ask: "Confirmar e gerar avaliação? (sim / ajustar seleção)"

---

## Step 6 — Determine assessment ID

Read `last_assessment_id` from `question-usage.md` frontmatter.
Increment: A00 → A01, A01 → A02, A09 → A10 (zero-pad to 2 digits minimum).
New ID = next value.

---

## Step 7 — Generate files

### `aulas/<slug>/assessment-A<NN>.md` (student version)

Use `.super-professor/templates/assessment.template.md`. Replace SLUG, LESSON_THEME, DISCIPLINE, A_ID, TIMESTAMP.

Render questions sequentially numbered (1, 2, 3...):
- Alternative: show question text + 4 labeled options (A/B/C/D) using shuffled order. NO correct indicator. NO rationale. NO source_ref.
- Discussive: show question text + blank answer lines (5 blank lines).

### `aulas/<slug>/assessment-A<NN>-key.md` (teacher version)

Use `.super-professor/templates/assessment-key.template.md`. Replace SLUG, LESSON_THEME, A_ID, TIMESTAMP.

For each question (same order as student file):
- Show question text + options (alternative) or expected answer (discussive)
- Alternative: mark correct answer with `★` before the option label. Example: `★ C) Envio de mensagem`
- Show: `Gabarito: C (armazenado como A no banco)`
- Show: `Justificativa: [rationale text]`
- Show: `ID no banco: Q01`

---

## Step 8 — Update `question-usage.md`

For each selected question ID:
- Find the row in `question-usage.md`
- Increment `times_used` by 1
- Append the new assessment ID to the `assessments` column (comma-separated)

Update frontmatter:
- `last_assessment_id`: new assessment ID
- `updated_at`: current timestamp

Write the updated file atomically (full rewrite, not append).

---

## GUARDRAILS

- NEVER include rationale or correct answers in the student file
- NEVER skip the shuffle step for alternative questions
- NEVER generate files without updating `question-usage.md` in the same operation
- NEVER reference a question ID not present in `questions.md`
- NEVER reuse an assessment ID — always increment from `question-usage.md`

## Output

- `aulas/<slug>/assessment-A<NN>.md`
- `aulas/<slug>/assessment-A<NN>-key.md`
- Updated `aulas/<slug>/question-usage.md`

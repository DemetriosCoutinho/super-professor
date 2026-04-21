# lesson-questions + lesson-assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new pipeline skills — `/lesson-questions` (per-lesson question bank authoring with devil's advocate QA loop) and `/lesson-assessment` (assessment generator with filter/random/hand-pick selection and even answer shuffling).

**Architecture:** Follow the existing super-professor skill pattern exactly: each skill is a `SKILL.md` prompt file in `skills/<name>/`, backed by a template in `templates/`, a contract in `docs/contracts/`, and QA rules in `docs/qa/quality-contracts.md`. The `lesson-qa` skill is extended to recognize the two new artifact types. No new tooling or dependencies — pure markdown artifacts and prompt files.

**Tech Stack:** Markdown artifacts, YAML frontmatter, Claude prompt skills, existing super-professor plugin structure.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `skills/lesson-questions/SKILL.md` | Question bank authoring skill (both modes + QA loop) |
| Create | `skills/lesson-assessment/SKILL.md` | Assessment generation skill |
| Create | `templates/questions.template.md` | Blank question bank artifact |
| Create | `templates/assessment.template.md` | Blank student assessment artifact |
| Create | `templates/assessment-key.template.md` | Blank teacher key artifact |
| Create | `templates/question-usage.template.md` | Blank usage tracking artifact |
| Create | `docs/contracts/questions-contract.md` | QC-Q rules reference |
| Create | `docs/contracts/assessment-contract.md` | QC-A rules reference |
| Modify | `docs/qa/quality-contracts.md` | Append QC-Q and QC-A sections |
| Modify | `skills/lesson-qa/SKILL.md` | Add `questions.md` and `assessment-*.md` artifact types |
| Modify | `templates/pipeline-state.template.md` | Add lesson-questions to required; lesson-assessment as optional |
| Modify | `CLAUDE.md` | Add two rows to skills table |
| Modify | `.claude-plugin/plugin.json` | Bump version to 0.3.0 |

---

## Task 1: Create the four new templates

**Files:**
- Create: `templates/questions.template.md`
- Create: `templates/assessment.template.md`
- Create: `templates/assessment-key.template.md`
- Create: `templates/question-usage.template.md`

- [ ] **Step 1.1: Create `templates/questions.template.md`**

```markdown
---
schema: super-professor/questions/v1
briefing_ref: aulas/SLUG/briefing.md
sources_ref: aulas/SLUG/sources.md
generated_at: TIMESTAMP
question_count: 0
---

# Banco de Questões — LESSON_THEME

<!-- Repetir para cada questão:

- id: Q01
  type: alternative
  topic: TOPIC
  difficulty: fácil | média | difícil
  source_ref: SOURCE_ID
  bloom: conhecimento | compreensão | aplicação | análise | síntese | avaliação
  text: |
    QUESTION_TEXT
  options:
    a: CORRECT_OPTION
    b: DISTRACTOR_B
    c: DISTRACTOR_C
    d: DISTRACTOR_D
  rationale: |
    RATIONALE_TEXT
  expected_answer:
  
  # For discussive questions, remove options block and set:
  # type: discussive
  # expected_answer: |
  #   EXPECTED_ANSWER_TEXT
  # rationale: |
  #   RATIONALE_TEXT

-->
```

- [ ] **Step 1.2: Create `templates/assessment.template.md`**

```markdown
---
schema: super-professor/assessment/v1
assessment_id: A_ID
briefing_ref: aulas/SLUG/briefing.md
questions_ref: aulas/SLUG/questions.md
question_ids: []
generated_at: TIMESTAMP
---

# Avaliação — LESSON_THEME

**Disciplina:** DISCIPLINE
**Data:** ___/___/______
**Duração:** _____ minutos
**Nome:** _______________________________________________

---

<!-- Questões geradas automaticamente pelo lesson-assessment.
     Este arquivo é a versão do aluno — sem gabarito, sem justificativas. -->
```

- [ ] **Step 1.3: Create `templates/assessment-key.template.md`**

```markdown
---
schema: super-professor/assessment-key/v1
assessment_id: A_ID
briefing_ref: aulas/SLUG/briefing.md
questions_ref: aulas/SLUG/questions.md
question_ids: []
shuffle_map: {}
generated_at: TIMESTAMP
---

# Gabarito — LESSON_THEME

**Avaliação:** A_ID
**Gerado em:** TIMESTAMP

---

<!-- Questões com gabarito, justificativa e mapeamento de embaralhamento.
     shuffle_map: { "Q01": { "original_correct": "a", "shuffled_to": "C" } } -->
```

- [ ] **Step 1.4: Create `templates/question-usage.template.md`**

```markdown
---
schema: super-professor/question-usage/v1
briefing_ref: aulas/SLUG/briefing.md
last_assessment_id: A00
updated_at: TIMESTAMP
---

# Uso de Questões — LESSON_THEME

| question_id | times_used | assessments |
|-------------|------------|-------------|
```

- [ ] **Step 1.5: Commit**

```bash
git add templates/questions.template.md templates/assessment.template.md templates/assessment-key.template.md templates/question-usage.template.md
git commit -m "feat: add templates for questions bank, assessment, key, and usage tracking"
```

---

## Task 2: Create QA contract files

**Files:**
- Create: `docs/contracts/questions-contract.md`
- Create: `docs/contracts/assessment-contract.md`

- [ ] **Step 2.1: Create `docs/contracts/questions-contract.md`**

```markdown
# Questions Contract — super-professor/questions/v1

## Required top-level frontmatter fields
schema, briefing_ref, sources_ref, generated_at, question_count

## Required fields per question
id, type, topic, difficulty, source_ref, bloom, text, rationale

## Type-specific required fields
- type: alternative → options (a, b, c, d), correct answer stored as option a
- type: discussive → expected_answer

## Valid values
- type: alternative | discussive
- difficulty: fácil | média | difícil
- bloom: conhecimento | compreensão | aplicação | análise | síntese | avaliação

## Validity conditions
- Every source_ref matches a source_id in sources.md
- All alternative questions have exactly 4 options: a, b, c, d
- rationale is non-empty for all questions
- No two questions share identical text

## QA rules applied
QC-U1 through QC-U5, QC-Q1 through QC-Q5
```

- [ ] **Step 2.2: Create `docs/contracts/assessment-contract.md`**

```markdown
# Assessment Contract — super-professor/assessment/v1 and assessment-key/v1

## Required top-level frontmatter fields (both files)
schema, assessment_id, briefing_ref, questions_ref, question_ids, generated_at

## Additional required fields (key file only)
shuffle_map

## Validity conditions

### Student file (assessment-A<NN>.md)
- No rationale present
- No correct answer indicators present (no ★, no "correta", no answer marked)
- No source_ref fields present
- All question IDs in question_ids exist in questions.md

### Key file (assessment-A<NN>-key.md)
- All question IDs in question_ids exist in questions.md
- shuffle_map contains an entry for every alternative question
- Correct answer marked unambiguously for each question

### Both files
- question-usage.md updated: all selected question IDs show this assessment_id

### Distribution (alternative questions only)
- Correct answer distribution across A/B/C/D: no position has more than floor(N/4)+1 correct answers

## QA rules applied
QC-U1 through QC-U5, QC-A1 through QC-A5
```

- [ ] **Step 2.3: Commit**

```bash
git add docs/contracts/questions-contract.md docs/contracts/assessment-contract.md
git commit -m "feat: add QA contracts for questions bank and assessment artifacts"
```

---

## Task 3: Append QC-Q and QC-A rules to `quality-contracts.md`

**Files:**
- Modify: `docs/qa/quality-contracts.md`

- [ ] **Step 3.1: Append QC-Q section**

Open `docs/qa/quality-contracts.md` and append at the end:

```markdown

## questions.md contracts

- QC-Q1: Every question has a `source_ref` that matches a `source_id` in `sources.md`
- QC-Q2: All `alternative` questions have exactly 4 options (a, b, c, d); correct answer is stored as option `a`
- QC-Q3: Every question has a non-empty `rationale` field
- QC-Q4: Bloom level is consistent with difficulty: fácil → conhecimento/compreensão; média → aplicação/análise; difícil → síntese/avaliação
- QC-Q5: No two questions share identical or near-identical `text` fields

## assessment files contracts

- QC-A1: All question IDs in the assessment exist in `questions.md`
- QC-A2: The student file (`assessment-A<NN>.md`) contains no rationale, no correct answer indicators, and no source references
- QC-A3: Correct answer distribution across A/B/C/D is balanced: no position has more than ⌊N/4⌋+1 correct answers (alternative questions only)
- QC-A4: `question-usage.md` has been updated: all selected question IDs show this assessment ID in their `assessments` column
- QC-A5: At least one question maps to each briefing objective (by topic alignment)
```

- [ ] **Step 3.2: Commit**

```bash
git add docs/qa/quality-contracts.md
git commit -m "feat: add QC-Q and QC-A rules to quality contracts"
```

---

## Task 4: Update `lesson-qa` to handle new artifact types

**Files:**
- Modify: `skills/lesson-qa/SKILL.md`

- [ ] **Step 4.1: Add new artifact type lines to the artefact type detection block**

In `skills/lesson-qa/SKILL.md`, find the artefact type determination block:

```
- `briefing.md` → type: briefing → rules: QC-U1–5, QC-B1–7
- `corpus-inventory.md` → type: corpus → rules: QC-U1–5, QC-C1–5
- `sources.md` → type: sources → rules: QC-U1–5, QC-S1–8
- `lesson-plan.md` → type: plan → rules: QC-U1–5, QC-P1–7
- `slides-blueprint.md` → type: blueprint → rules: QC-U1–5, QC-BL1–10
```

Replace with:

```
- `briefing.md` → type: briefing → rules: QC-U1–5, QC-B1–7
- `corpus-inventory.md` → type: corpus → rules: QC-U1–5, QC-C1–5
- `sources.md` → type: sources → rules: QC-U1–5, QC-S1–8
- `lesson-plan.md` → type: plan → rules: QC-U1–5, QC-P1–7
- `slides-blueprint.md` → type: blueprint → rules: QC-U1–5, QC-BL1–10
- `questions.md` → type: questions → rules: QC-U1–5, QC-Q1–5
- `assessment-A*.md` (not ending in `-key.md`) → type: assessment → rules: QC-U1–5, QC-A1–5
- `assessment-A*-key.md` → type: assessment-key → rules: QC-U1–5, QC-A1–5
```

- [ ] **Step 4.2: Add new critical rule classification lines**

In `skills/lesson-qa/SKILL.md`, find the classification block:

```
- **Crítico**: QC-U rules, QC-B1–3, QC-C1–2, QC-S1–4, QC-P1–3, QC-BL1–7 — pipeline CANNOT advance
```

Replace with:

```
- **Crítico**: QC-U rules, QC-B1–3, QC-C1–2, QC-S1–4, QC-P1–3, QC-BL1–7, QC-Q1–3, QC-A1–4 — pipeline CANNOT advance
```

- [ ] **Step 4.3: Commit**

```bash
git add skills/lesson-qa/SKILL.md
git commit -m "feat: extend lesson-qa to validate questions.md and assessment artifacts"
```

---

## Task 5: Create `skills/lesson-questions/SKILL.md`

**Files:**
- Create: `skills/lesson-questions/SKILL.md`

- [ ] **Step 5.1: Create the skill file**

```markdown
---
name: lesson-questions
description: Author and manage the per-lesson question bank. Supports interactive (one at a time) and batch (natural language prompt) modes. Every question passes a devil's advocate QA loop before being appended. Produces questions.md. Run after lesson-plan, before lesson-blueprint.
---

You are authoring questions for the lesson question bank.

## BEFORE STARTING

1. Read `aulas/<slug>/briefing.md`. If `status` is not `closed`: stop and say "O briefing ainda não foi fechado. Execute `/lesson-intake` primeiro."
2. Read `aulas/<slug>/sources.md`. If missing: stop and say "sources.md não encontrado. Execute `/lesson-research` primeiro."
3. Read `aulas/<slug>/lesson-plan.md`. If missing: stop and say "lesson-plan.md não encontrado. Execute `/lesson-plan` primeiro."
4. If `aulas/<slug>/questions.md` exists: load it. Display summary:
   - Total de questões: N
   - Por tipo: N alternativas, N discursivas
   - Por dificuldade: N fácil, N média, N difícil
   - Por tópico: [lista]

If `aulas/<slug>/question-usage.md` does not exist: initialize it from `.super-professor/templates/question-usage.template.md`, replacing SLUG and LESSON_THEME.

## Detect mode

- If invoked with **no arguments**: Interactive mode
- If invoked with **arguments** (natural language prompt): Batch mode

---

## INTERACTIVE MODE

### Authoring loop

Collect fields in order, one message at a time:

1. "Tipo da questão? (alternativa / discursiva)"
2. "Tópico? Sugestões com base nos objetivos do briefing: [lista de tópicos do lesson-plan]. Ou informe outro tópico."
3. "Dificuldade? (fácil / média / difícil)"
4. "Nível Bloom? Sugestão para dificuldade [X]: [conhecimento/compreensão para fácil | aplicação/análise para média | síntese/avaliação para difícil]. Confirmar ou escolher: conhecimento | compreensão | aplicação | análise | síntese | avaliação"
5. "Referência de fonte? IDs disponíveis: [lista de source_id de sources.md]"
6. "Texto da questão:"
7. For `type: alternative`:
   - "Opção A — a resposta CORRETA:"
   - "Opção B — distrator:"
   - "Opção C — distrator:"
   - "Opção D — distrator:"
   - "Justificativa: por que A está correta e B, C, D estão erradas?"
8. For `type: discussive`:
   - "Resposta esperada:"
   - "Justificativa: o que caracteriza uma resposta completa e correta?"

### Preview & confirm

Display the formatted question block. Ask:
"Adicionar ao banco? (sim / editar: [nome-do-campo] / descartar)"

If "editar: [campo]": collect new value and re-display preview.

### QA loop

Run the QA loop (see QA LOOP section) on the question.

### Append

If QA passes: auto-increment ID (Q01, Q02, ...), append question to `questions.md`, increment `question_count` in frontmatter, add row to `question-usage.md` with `times_used: 0`.

Ask: "Adicionar outra questão? (sim / não)"

---

## BATCH MODE

### Step 1: Parse and clarify

Parse the NL prompt. Extract:
- `question_count` (how many questions)
- `type` (alternative / discussive / mixed)
- `topic(s)`
- `difficulty`
- `bloom` level(s)

For any parameter that is ambiguous or missing, ask ONE clarifying question at a time before generating. Do not generate until all parameters are clear.

### Step 2: Generate batch

Generate all questions according to parameters. Each question must:
- Have exactly 4 options if alternative (correct stored as `a`)
- Have a non-empty `rationale`
- Reference a `source_ref` from `sources.md`
- Match the requested difficulty, bloom, and topic

### Step 3: Preview table

Display:

| Temp ID | Tipo | Tópico | Dificuldade | Bloom | Texto (primeiros 80 chars) |
|---------|------|--------|-------------|-------|---------------------------|

Ask: "Aprovar todas / aprovar por ID (ex: T01, T03) / rejeitar todas / editar individualmente (ID)"

If "editar individualmente (ID)": show that question's full fields, collect corrections, re-run preview.

### Step 4: QA loop per approved question

For each approved question, run the QA loop (see QA LOOP section).

---

## QA LOOP

For each question about to be appended, act as Advogado do Diabo:

**Check 1 — Consistência interna**
- (alternative) Are distractors plausible but unambiguously wrong? Does the correct answer admit no other interpretation under any reading?
- (discussive) Is the expected answer specific enough to objectively evaluate a student response?

**Check 2 — Confiabilidade**
- Does the question actually measure the declared bloom level?
- Does it actually address the declared topic?

**Check 3 — Correção do conhecimento**
- Is the rationale's factual content consistent with the referenced source (`source_ref`)?
- Does the rationale correctly explain why the correct answer is correct and the distractors are wrong?

**Check 4 — Requisitos atendidos**
- Does the question match the requested type, difficulty, bloom level, and topic?

**Results:**
- ALL checks pass → proceed to append
- ANY check fails → regenerate the question using the list of failures as context; re-run QA loop on the new version
- After **3 failed attempts**: present the question to the professor with full QA diagnosis. Ask:
  "(1) Aceitar mesmo assim — informe justificativa / (2) Descartar esta questão / (3) Reformular manualmente — informe o texto revisado"

---

## GUARDRAILS

- NEVER append a question that failed QA without explicit professor decision
- NEVER use a `source_ref` not present in `sources.md`
- NEVER generate alternative options with ambiguous correct answers
- NEVER skip the QA loop for any question in any mode
- NEVER overwrite or modify existing questions — always append
- NEVER write `questions.md` before at least one question is approved

## Output

Write/append to `aulas/<slug>/questions.md` using `.super-professor/templates/questions.template.md`.
Write/update `aulas/<slug>/question-usage.md`.
```

- [ ] **Step 5.2: Commit**

```bash
git add skills/lesson-questions/SKILL.md
git commit -m "feat: add lesson-questions skill with interactive and batch modes, devil's advocate QA loop"
```

---

## Task 6: Create `skills/lesson-assessment/SKILL.md`

**Files:**
- Create: `skills/lesson-assessment/SKILL.md`

- [ ] **Step 6.1: Create the skill file**

```markdown
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
```

- [ ] **Step 6.2: Commit**

```bash
git add skills/lesson-assessment/SKILL.md
git commit -m "feat: add lesson-assessment skill with filter/random/hand-pick selection and even answer shuffling"
```

---

## Task 7: Update pipeline-state template and CLAUDE.md

**Files:**
- Modify: `templates/pipeline-state.template.md`
- Modify: `CLAUDE.md`
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 7.1: Update `templates/pipeline-state.template.md`**

Find the `## Skills pendentes` section:

```markdown
## Skills pendentes

- lesson-intake
- lesson-corpus
- lesson-research
- lesson-plan
- lesson-blueprint
```

Replace with:

```markdown
## Skills pendentes

- lesson-intake
- lesson-corpus
- lesson-research
- lesson-plan
- lesson-questions
- lesson-blueprint
- lesson-assessment (opcional, repetível)
```

- [ ] **Step 7.2: Update `CLAUDE.md` skills table**

Find the table row for `lesson-blueprint`:

```markdown
| /lesson-blueprint | Gera blueprint de slides | lesson-plan.md |
```

Replace with:

```markdown
| /lesson-blueprint | Gera blueprint de slides | lesson-plan.md |
| /lesson-questions | Autora e gerencia banco de questões da aula | lesson-plan.md |
| /lesson-assessment | Gera avaliação a partir do banco de questões | questions.md |
```

- [ ] **Step 7.3: Bump plugin version**

In `.claude-plugin/plugin.json`, find:

```json
"version": "0.2.0",
```

Replace with:

```json
"version": "0.3.0",
```

- [ ] **Step 7.4: Commit**

```bash
git add templates/pipeline-state.template.md CLAUDE.md .claude-plugin/plugin.json
git commit -m "feat: integrate lesson-questions and lesson-assessment into pipeline, bump version to 0.3.0"
```

---

## Task 8: Final integration verification

- [ ] **Step 8.1: Verify all new files exist**

Run:
```bash
ls skills/lesson-questions/SKILL.md skills/lesson-assessment/SKILL.md templates/questions.template.md templates/assessment.template.md templates/assessment-key.template.md templates/question-usage.template.md docs/contracts/questions-contract.md docs/contracts/assessment-contract.md
```

Expected: all 8 files listed with no "No such file" errors.

- [ ] **Step 8.2: Verify lesson-qa recognizes new artifact types**

```bash
grep "questions.md" skills/lesson-qa/SKILL.md
grep "assessment-A" skills/lesson-qa/SKILL.md
grep "QC-Q1" skills/lesson-qa/SKILL.md
```

Expected: each grep returns at least one matching line.

- [ ] **Step 8.3: Verify quality-contracts.md has new sections**

```bash
grep "QC-Q1\|QC-A1" docs/qa/quality-contracts.md
```

Expected: two matching lines.

- [ ] **Step 8.4: Verify CLAUDE.md has new skill rows**

```bash
grep "lesson-questions\|lesson-assessment" CLAUDE.md
```

Expected: two matching lines.

- [ ] **Step 8.5: Final commit if any stragglers**

```bash
git status
```

If clean: done. If any unstaged changes: stage and commit with `"chore: final integration cleanup"`.

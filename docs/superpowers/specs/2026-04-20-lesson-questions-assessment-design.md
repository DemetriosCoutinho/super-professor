# Design: lesson-questions + lesson-assessment skills

**Date:** 2026-04-20
**Status:** approved

## Summary

Two new pipeline skills for the super-professor plugin:

- `/lesson-questions` — authors and manages a per-lesson question bank (`questions.md`)
- `/lesson-assessment` — selects questions from the bank and generates student + teacher assessment files

Both integrate into the existing pipeline with QA validation via new `QC-Q` and `QC-A` contracts.

---

## 1. Question Bank Artifact — `questions.md`

**Location:** `aulas/<slug>/questions.md`

**Frontmatter:**
```yaml
schema: super-professor/questions/v1
briefing_ref: aulas/<slug>/briefing.md
sources_ref: aulas/<slug>/sources.md
generated_at: TIMESTAMP
question_count: N
```

**Per-question structure:**
```yaml
- id: Q01
  type: alternative          # alternative | discussive
  topic: "Relógios Lógicos"
  difficulty: média          # fácil | média | difícil
  source_ref: leslie-lamport-1978
  bloom: compreensão         # conhecimento | compreensão | aplicação | análise | síntese | avaliação
  text: |
    Qual evento define a relação "happens-before"?
  options:                   # alternative only — correct is ALWAYS stored as option a
    a: "Envio de mensagem"
    b: "Recebimento de mensagem"
    c: "Incremento de contador"
    d: "Execução local"
  rationale: |
    Lamport define happens-before a partir do envio de mensagens entre processos,
    pois é o único evento observável por ambos os lados.
  expected_answer:           # discussive only
  rationale: |               # discussive: explains ideal answer structure
```

**Invariants:**
- Correct answer is always stored as option `a` in the database
- Options are shuffled only at assessment generation time
- The file is append-only — the skill never overwrites existing questions

---

## 2. `lesson-questions` Skill

### Pre-conditions
- `briefing.md` must have `status: closed`
- `sources.md` must exist
- If `questions.md` exists, load it and show current count by type/topic/difficulty

### Mode 1: Interactive (one at a time)

Authoring loop per question:
1. Type? (alternative / discussive)
2. Topic? (suggests from briefing objectives)
3. Difficulty? (fácil / média / difícil)
4. Bloom level? (suggests based on difficulty)
5. Source ref? (validates against `sources.md`)
6. Question text
7. For alternative: 4 options (correct entered as `a`) + rationale
8. For discussive: expected answer + rationale
9. Preview → "Adicionar? (sim / editar / descartar)"
10. "Adicionar outra questão? (sim / não)"

### Mode 2: Batch generation

Invoked with a natural language prompt:
> `/lesson-questions gere 5 questões de dificuldade média sobre Lamport, 3 alternativas e 2 discursivas`

Flow:
1. Analyze prompt — ask clarifying questions (one at a time) if topic, bloom, source, or count is ambiguous
2. Generate full batch
3. Display preview table:

| ID | Tipo | Tópico | Dificuldade | Bloom | Texto (preview) |
|----|------|--------|-------------|-------|-----------------|

4. Professor selects: aprovar tudo / aprovar por ID / rejeitar / editar individualmente

### QA loop (both modes — per question before append)

Acts as **Advogado do Diabo**. Checks:
1. **Consistência interna** — distractors are plausible but unambiguously wrong; correct answer admits no ambiguity
2. **Confiabilidade** — question tests what it claims (bloom + topic alignment)
3. **Correção do conhecimento** — rationale consistent with `source_ref` content; no contradiction
4. **Requisitos atendidos** — type, difficulty, bloom, topic match the request

Results:
- ✅ Pass → append to bank
- ❌ Fail → regenerate automatically using failures as context, re-run QA
- After 3 failed attempts → escalate to professor with full diagnosis

### Output
- `aulas/<slug>/questions.md` (append)

### Pipeline position
After `lesson-plan`, before `lesson-blueprint`

---

## 3. `lesson-assessment` Skill

### Pre-conditions
- `briefing.md` must have `status: closed`
- `questions.md` must exist with at least 1 question

### Flow

**Step 1 — Summary**
Show question bank: total by type / difficulty / topic / usage status (never used / used N times).

**Step 2 — Selection (three steps in order)**
1. **Filter**: professor specifies criteria (topic, difficulty, type, count, usage)
   - Supports `nunca usada`, `usada em A01`, `usada menos de N vezes`
2. **Random pool**: filtered questions shuffled, top N auto-selected
3. **Hand-pick override**: professor sees filtered list and can swap questions by ID

**Step 3 — Shuffle**
Correct answers rotated evenly across positions A/B/C/D across the full alternative set (±1 per position). Not random per question — balanced across the assessment.

**Step 4 — Preview**
Show final question list as table. Professor confirms.

**Step 5 — Generate files**

`aulas/<slug>/assessment-A<NN>.md` (student version):
- Questions only, shuffled options, no answers, no rationale

`aulas/<slug>/assessment-A<NN>-key.md` (teacher version):
- Questions + correct answer indicated + rationale for each

**Step 6 — Update `question-usage.md`**
Atomically update usage tracking after successful generation.

### Pipeline position
After `lesson-questions`. Optional and repeatable — each run produces `A01`, `A02`, etc. Does not block `lesson-blueprint`.

---

## 4. `question-usage.md` Artifact

**Location:** `aulas/<slug>/question-usage.md`

**Frontmatter:**
```yaml
schema: super-professor/question-usage/v1
briefing_ref: aulas/<slug>/briefing.md
last_assessment_id: A01
updated_at: TIMESTAMP
```

**Content:**
```markdown
| question_id | times_used | assessments |
|-------------|------------|-------------|
| Q01         | 2          | A01, A03    |
| Q02         | 0          | —           |
| Q03         | 1          | A01         |
```

Updated atomically by `lesson-assessment` on every generation. Never left out of sync.

---

## 5. Pipeline Integration

```
lesson-plan → lesson-questions → lesson-blueprint
                    ↓ (optional, repeatable)
             lesson-assessment
```

`pipeline-state.md` additions:
- `lesson-questions` added to required skills list
- `lesson-assessment` listed as optional, repeatable

---

## 6. QA Contracts

### QC-Q (questions bank)

| Rule | Severity | Description |
|------|----------|-------------|
| QC-Q1 | Crítico | Every question has `source_ref` traceable to `sources.md` |
| QC-Q2 | Crítico | All alternatives have exactly 4 options; correct stored as `a` |
| QC-Q3 | Crítico | `rationale` present and non-empty on all questions |
| QC-Q4 | Importante | Bloom level consistent with difficulty |
| QC-Q5 | Importante | No duplicate question text |

### QC-A (assessment files)

| Rule | Severity | Description |
|------|----------|-------------|
| QC-A1 | Crítico | All selected IDs exist in `questions.md` |
| QC-A2 | Crítico | Student file contains no answer indicators or rationale |
| QC-A3 | Crítico | Correct answer distribution across A/B/C/D is balanced (±1) |
| QC-A4 | Crítico | `question-usage.md` updated and consistent with all assessments |
| QC-A5 | Importante | At least one question per briefing objective |

---

## 7. New Templates

| Template | Artifact |
|----------|----------|
| `questions.template.md` | `aulas/<slug>/questions.md` |
| `assessment.template.md` | `aulas/<slug>/assessment-A<NN>.md` |
| `assessment-key.template.md` | `aulas/<slug>/assessment-A<NN>-key.md` |
| `question-usage.template.md` | `aulas/<slug>/question-usage.md` |

---

## 8. CLAUDE.md updates

Two new rows in the skills table:

| `/lesson-questions` | Autora e gerencia banco de questões da aula | `lesson-plan.md` |
| `/lesson-assessment` | Gera avaliação a partir do banco de questões | `questions.md` |

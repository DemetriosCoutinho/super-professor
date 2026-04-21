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

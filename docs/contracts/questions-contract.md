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

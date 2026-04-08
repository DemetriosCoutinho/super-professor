# Lesson Plan Contract — super-professor/lesson-plan/v1

## Required fields per block
id, type, title, duration_minutes, priority, objectives (≥1), content_items (≥1)

## Valid values
- type: introdução | desenvolvimento | fixação | fechamento
- priority: essencial | opcional

## Required top-level fields
total_duration_minutes, time_budget_check, briefing_ref, sources_ref, corpus_ref

## Validity condition
Sum of block durations ≤ total_duration_minutes.
time_budget_check = pass.
All content_items have source_ref.

## QA rules applied
QC-U1 through QC-U5, QC-P1 through QC-P7

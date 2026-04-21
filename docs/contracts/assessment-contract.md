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

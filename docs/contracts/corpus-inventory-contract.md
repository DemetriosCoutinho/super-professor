# Corpus Inventory Contract — super-professor/corpus-inventory/v1

## Required fields per material
path, type, relevance_to_lesson, status, evidence (list, may be empty for periférico)

## Valid values
- type: ementa | livro | slides | apostila | pdf | notas | exercícios | resumo | prompt | complementar
- relevance_to_lesson: central | complementar | periférico
- status: obrigatório | opcional | descartar

## Validity condition
All materials with status=obrigatório must have ≥1 evidence entry.
All files in briefing.mandatory_materials must appear in inventory.

## QA rules applied
QC-U1 through QC-U5, QC-C1 through QC-C5

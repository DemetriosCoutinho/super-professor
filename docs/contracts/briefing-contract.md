# Briefing Contract — super-professor/briefing/v1

## Required fields
discipline, theme, level, modality, duration_minutes, main_objective,
secondary_objectives (≥1), style, depth, status

## Optional fields
subtheme, prerequisites, mandatory_materials, restrictions, hypotheses

## Valid values
- level: ensino médio | técnico | graduação | pós
- modality: presencial | EAD | híbrido
- style: expositivo | interativo | resolução-de-problemas | discussão | laboratório | revisão | misto
- depth: superficial | intermediário | avançado
- status: draft | closed

## Validity condition
status must be `closed` before pipeline can advance past lesson-intake.

## QA rules applied
QC-U1 through QC-U5, QC-B1 through QC-B7

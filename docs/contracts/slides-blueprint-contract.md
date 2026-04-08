# Slides Blueprint Contract — super-professor/slides-blueprint/v1

## Required fields per slide
slide_number, lesson_block_ref, type, priority, pedagogical_objective,
estimated_duration_seconds, content.title, content.body_items,
content.body_density, media.required, media.type, media.description,
media.alt_text, media.pedagogical_function, layout.template,
layout.media_position, layout.content_alignment, layout.typography_hierarchy,
layout.text_size_hint, visual_intent, rendering_notes, accessibility_notes,
responsive_notes

## Valid values
- type: capa | agenda | introducao | conceito | exemplo | comparacao | diagrama | atividade | video | simulador | citacao | resumo | fechamento | transicao
- priority: essencial | complementar
- body_density: low | medium | high
- layout.template: title-only | title-content | title-content-media | title-media-only | two-column | full-image-overlay | quote | activity-prompt | agenda
- media.type: image | diagram | gif | video | simulator | animation | chart | map | timeline | none
- text_size_hint: large | medium | small

## Validity condition
body_density=high (5 items) only for: comparacao, agenda, resumo slide types.
Each body_item ≤ 15 words. title ≤ 8 words.
If media.required=true: description must be ≥ 20 words.
pedagogical_function must explain WHY this media is pedagogically necessary.

## QA rules applied
QC-U1 through QC-U5, QC-BL1 through QC-BL10

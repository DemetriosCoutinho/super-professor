# Quality Contracts — super-professor

All artefacts must pass their type-specific contract before the pipeline can advance.
lesson-qa enforces these contracts. Violations block pipeline progress unless the
professor provides an explicit override with written justification.

## Universal rules (apply to ALL artefacts)

- QC-U1: File must be valid Markdown with YAML frontmatter
- QC-U2: `schema` field in frontmatter must match the expected schema string
- QC-U3: `generated_at` must be a valid ISO8601 timestamp
- QC-U4: No field may contain the literal string "TBD", "TODO", or "a definir"
- QC-U5: No field may be empty when marked as required in its contract

## briefing.md contracts

- QC-B1: `status` must be `closed` (not `draft`)
- QC-B2: `discipline`, `theme`, `level`, `main_objective`, `duration_minutes` must all be non-empty
- QC-B3: `secondary_objectives` must have at least 1 item
- QC-B4: `level` must be one of: ensino médio, técnico, graduação, pós
- QC-B5: `style` must be one of: expositivo, interativo, resolução-de-problemas, discussão, laboratório, revisão, misto
- QC-B6: `duration_minutes` must be a positive integer
- QC-B7: If `duration_minutes` was not stated by professor, it must appear in `hypotheses`

## corpus-inventory.md contracts

- QC-C1: Every material listed as `obrigatório` must have at least one item in `evidence`
- QC-C2: Every evidence entry must have both `quote` and `location` fields
- QC-C3: `gaps_summary` must not be empty if any gap was identified
- QC-C4: No material may be classified as `central` without at least one evidence entry
- QC-C5: All files listed as `mandatory_materials` in briefing.md must appear in the inventory

## sources.md contracts

- QC-S1: Every source must have: id, title, author_or_institution, type, url, access_date, summary, relevance_reason, reliability, lesson_topic, downloaded, status
- QC-S2: `reliability` must be an integer 1–5
- QC-S3: Any source with `reliability` ≤ 2 must have a non-empty `notes` field justifying its inclusion
- QC-S4: `url` must be a valid URL (not a placeholder)
- QC-S5: No source may have `status: pendente` when the pipeline advances past lesson-research
- QC-S6: The citation block at the bottom of sources.md must match the citation_style in repo-manifest.md
- QC-S7: ABNT citations must follow NBR 6023 structure: SOBRENOME, Nome. **Título**. Cidade: Editora, Ano.
- QC-S8: APA citations must follow APA 7: Author, A. A. (Year). *Title*. Publisher.

## lesson-plan.md contracts

- QC-P1: Sum of all `duration_minutes` across blocks must be ≤ `total_duration_minutes`
- QC-P2: `time_budget_check` must be `pass`
- QC-P3: Every `content_item` must have a non-empty `source_ref`
- QC-P4: `source_ref` must match either a `source_id` in sources.md or a valid filepath in corpus-inventory.md
- QC-P5: Plan must include at least one block of each type: introdução, desenvolvimento, fechamento
- QC-P6: No single block may exceed 60% of total duration
- QC-P7: All `secondary_objectives` from briefing.md must be addressed by at least one block

## slides-blueprint.md contracts

- QC-BL1: Every slide must have: slide_number, type, priority, pedagogical_objective, estimated_duration_seconds, content.title, media.required, layout.template
- QC-BL2: `content.title` must be ≤ 8 words
- QC-BL3: Each `body_item` must be ≤ 15 words
- QC-BL4: `body_items` list must have ≤ 5 items
- QC-BL5: `body_density: high` only allowed for slide types: comparacao, agenda, resumo
- QC-BL6: If `media.required: true`, then `media.description` must be ≥ 20 words
- QC-BL7: `media.pedagogical_function` must be non-empty and must NOT contain the word "decorativo" without a justification
- QC-BL8: Every slide with `priority: essencial` must have at least one `sources` entry
- QC-BL9: `rendering_notes` and `accessibility_notes` must be non-empty for every slide
- QC-BL10: All slides must trace to a `lesson_block_ref` that exists in lesson-plan.md

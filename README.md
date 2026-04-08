# super-professor

Plugin for Claude Code that creates modern, pedagogically rigorous lessons from academic repository materials.

## What it does

Provides a pipeline of skills that takes you from raw academic materials to a structured slide blueprint, ready for HTML rendering. Every step is traceable, validated, and resumable.

## Install

```bash
# In your academic repository:
claude /plugin install super-professor
```

## First run: always start with repo setup

```bash
/lesson-repo-setup
```

## Full pipeline

```bash
/super-professor "Quero criar uma aula sobre [TEMA] para [NÍVEL]"
```

## Individual skills

```bash
/lesson-intake          # Close lesson briefing
/lesson-corpus          # Audit repository materials
/lesson-research        # Find high-quality external sources
/lesson-plan            # Create lesson plan
/lesson-blueprint       # Generate slide blueprint
/lesson-qa <file>       # Validate any artefact
```

## Citation standards

- ABNT NBR 6023 (default)
- APA 7th edition (set in `.super-professor/repo-manifest.md`)

## Output

All artefacts land in `aulas/<YYYY-MM-DD>-<slug>/`. The final output, `slides-blueprint.md`, is ready for a rendering skill to produce a single-file HTML presentation.

## Requirements

- Claude Code with an active session
- Academic repository with course materials (ementa, slides, PDFs, notes, etc.)

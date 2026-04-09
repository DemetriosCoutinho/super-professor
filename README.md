# super-professor

Plugin for Claude Code that creates modern, pedagogically rigorous lessons from academic repository materials.

## What it does

Provides a pipeline of skills that takes you from raw academic materials to a structured slide blueprint, ready for HTML rendering. Every step is traceable, validated, and resumable.

## Install

```bash
# Add the marketplace (first time only)
claude marketplace add demetrioscoutinho/super-professor

# Install the plugin
claude plugin install super-professor@super-professor-marketplace
```

## Update

```bash
claude plugin update super-professor@super-professor-marketplace
```

## First run: always start with repo setup

Open Claude Code inside your academic repository, then:

```
/lesson-repo-setup
```

## Full pipeline

```
/super-professor "Quero criar uma aula sobre [TEMA] para [NÍVEL]"
```

## Individual skills

```
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

## Pipeline overview

```
lesson-repo-setup → lesson-intake → lesson-corpus → lesson-research → lesson-plan → lesson-blueprint
                                                                                           ↓
                                                                                    slides-blueprint.md
```

Each step is validated by `/lesson-qa` before the next step can proceed. The pipeline can be paused and resumed at any point.

## License

MIT

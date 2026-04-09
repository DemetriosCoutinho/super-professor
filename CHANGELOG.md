# Changelog

## [0.2.0] — 2026-04-08

### Changed
- Restructured project for Claude Code marketplace distribution
- Skills moved from `.claude/skills/*.md` to `skills/<name>/SKILL.md` (marketplace format)
- Agents moved from `.claude/agents/*.md` to `agents/*.md`
- Plugin manifest moved from `plugin.json` (root) to `.claude-plugin/plugin.json` (standard location)
- Added `.claude-plugin/marketplace.json` for self-hosted marketplace support
- Removed `install.sh` — installation now handled by `claude plugin install`
- Bumped version to 0.2.0

### Install (v0.2.0+)
```bash
claude marketplace add demetrioscoutinho/super-professor
claude plugin install super-professor@super-professor-marketplace
```

## [0.1.0] — 2026-04-08

### Added
- `lesson-repo-setup`: repository analysis and initialization
- `lesson-intake`: interactive briefing collection
- `lesson-corpus`: corpus audit with evidence extraction
- `lesson-research`: external source search with ABNT/APA validation
- `lesson-plan`: time-bounded lesson plan with source traceability
- `lesson-blueprint`: detailed slide-by-slide blueprint
- `lesson-qa`: TDD-style artefact validation against quality contracts
- `super-professor`: orchestrator with interactive planning and checkpoints
- `corpus-reader`, `research-scout`, `qa-validator`, `citation-formatter` subagents
- Quality contracts for all 5 artefact types
- Templates for all 7 artefacts

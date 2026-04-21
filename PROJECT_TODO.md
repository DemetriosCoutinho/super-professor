# PROJECT_TODO

> Status central do projeto. Editado manualmente ou via `/project-todo`.
> Última atualização: 2026-04-21

## Now (em andamento)

- [ ] Testar `/assessment-sync-check` contra curso sandbox do Classroom — started 2026-04-21

## Next (próximas 1-2 semanas)

- [ ] Testar `/lesson-classroom-publish --preview` (dry-run) e depois publicação real em curso sandbox
- [ ] Conectar `/lesson-notebooklm` ao pipeline `/super-professor` (adicionar checkpoint após blueprint)
- [ ] Adicionar campo `image_provider` ao template `repo-manifest.md`

## Later (backlog priorizado)

- [ ] Subagent `image-curator` — propor corpus/diagrama/raster por slide com prós e contras
- [ ] Integrar `/lesson-images` ao `/lesson-blueprint` (consumir `media-plan.md`)
- [ ] Suporte a uploads de Drive links em `/lesson-classroom-publish` (quando anexos já estão no Drive)
- [ ] Testar geração de imagens raster via Gemini e DALL-E (após `image_provider` configurado)

## Blocked

_(nenhum item bloqueado)_

## Done (últimos 14 dias)

- [x] Criar skill `/assessment-sync-check` (preflight dry-run Classroom) — 2026-04-21
- [x] Criar skill `/lesson-classroom-publish` (publicar atividades no Classroom) — 2026-04-21
- [x] Criar skill `/lesson-images` (plano de mídia corpus + Mermaid + raster) — 2026-04-21
- [x] Criar skill `/lesson-notebooklm` (wrapper NotebookLM para extras de aula) — 2026-04-21
- [x] Criar skill `/project-todo` e `PROJECT_TODO.md` (TODO replicável) — 2026-04-21
- [x] Adicionar subagent `skill-reviewer` e config de user-level install — 2026-04-21
- [x] Normalizar `source` path em `marketplace.json` — 2026-04-21
- [x] Melhorar `CLAUDE.md` com precisão e completude — 2026-04-21
- [x] Design spec e plano de implementação para `lesson-questions` e `lesson-assessment` — 2026-04-21
- [x] Adicionar skills do assessment pipeline ao `CLAUDE.md` — 2026-04-21

# super-professor

Plugin para criação de aulas modernas e pedagogicamente rigorosas a partir de materiais de repositórios acadêmicos.

## Skills disponíveis

| Skill | Descrição | Pré-requisito |
|-------|-----------|---------------|
| /lesson-repo-setup | Analisa ou inicializa o repositório | Nenhum — sempre primeiro |
| /lesson-intake | Fecha o briefing da aula | repo-manifest.md |
| /lesson-corpus | Audita materiais do repositório | briefing.md |
| /lesson-research | Pesquisa fontes externas | corpus-inventory.md |
| /lesson-plan | Cria plano de aula | sources.md |
| /lesson-blueprint | Gera blueprint de slides | lesson-plan.md |
| /lesson-questions | Autora e gerencia banco de questões da aula | lesson-plan.md |
| /lesson-assessment | Gera avaliação a partir do banco de questões | questions.md |
| /lesson-qa | Valida qualquer artefato | artefato-alvo |
| /super-professor | Pipeline completo com checkpoints | repo-manifest.md |
| /assessment-create | Cria avaliação impressa: prova + gabarito em LaTeX/PDF/HTML (A4, 2 colunas, duplex, logo IFRN, matrícula 14 dígitos) | assessment.md + assessment-key.md (ou modo interativo) |
| /assessment-grade | Corrige folhas fotografadas via OMRChecker + Claude Vision | photos/ preenchido |
| /assessment-sync | Envia notas ao Google Classroom via gws CLI | scores.json + student-map.csv |
| /assessment-sync-check | Preflight dry-run do Classroom sync (sem postar notas) | scores.json + student-map.csv |
| /lesson-images | Autora plano de mídia: corpus, Mermaid/HTML, raster (Gemini/DALL-E) | slides-blueprint.md |
| /lesson-notebooklm | Cria notebook NotebookLM e gera áudio, study guide, mind map | lesson-plan.md + blueprint |
| /lesson-classroom-publish | Publica atividades e materiais direto no Google Classroom | lesson-plan.md + blueprint |

## Subagents disponíveis

- `citation-formatter` — ABNT/APA para referências
- `corpus-reader` — leitura e indexação de materiais
- `omr-processor` — invoca OMRChecker sobre fotos
- `qa-validator` — valida artefatos contra contratos
- `research-scout` — busca fontes externas
- `skill-reviewer` — revisa qualidade de skills
- `vision-grader` — fallback Claude Vision para OMR ambíguo

## Assessment pipeline (correção de provas impressas)

```
/assessment-create   # renderiza prova + folha de respostas (LaTeX → PDF + HTML)
/assessment-grade    # corrige fotos → scores.json + grade-report.md
/assessment-sync     # envia notas ao Google Classroom
```

Pré-requisitos externos:
- OMRChecker vendorizado em `tools/OMRChecker/` (instalar dependências: `pip install -r tools/OMRChecker/requirements.txt`)
- gws CLI autenticado (para `/assessment-sync`)
- Para `/assessment-create`: `xelatex`, `pygmentize`, `qpdf` — rode `python3 scripts/check_print_deps.py` para ver o plano de instalação por plataforma
- Logo institucional em `skills/assessment-create/assets/if.jpeg` (IFRN Campus Pau dos Ferros)

## Comandos

```bash
python3 -m pytest tests/                          # suite completa (21 testes)
python3 scripts/check_print_deps.py               # verifica deps do /assessment-create
```

## Padrão de citação
ABNT NBR 6023 (padrão) | APA 7ª edição (configurável em `repo-manifest.md`)

## Princípios
- Toda afirmação de conteúdo rastreia a uma fonte
- Nenhum slide sem função pedagógica declarada para a mídia
- `pipeline-state.md` escrito ANTES de cada skill rodar
- QA obrigatório após cada skill — sem override silencioso

## Estrutura do plugin

```
skills/             # 17 skills do pipeline (uma SKILL.md cada)
agents/             # 7 subagents especializados
templates/          # 19 templates de artefatos (.md/.html/.json/.tex)
scripts/            # compute_scores.py, render_assessment.py, validate_layout.py, check_print_deps.py
tests/              # pytest — test_compute_scores.py, test_render_assessment.py + fixtures
tools/OMRChecker/   # OMRChecker vendorizado
docs/contracts/     # Contratos de qualidade por artefato
docs/qa/            # Regras de QA consolidadas
docs/superpowers/   # Notas internas de design
.claude-plugin/     # plugin.json + marketplace.json
```

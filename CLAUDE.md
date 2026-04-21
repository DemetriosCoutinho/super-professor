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
| /assessment-create | Cria avaliação impressa (gabarito + folha de respostas HTML) | Nenhum |
| /assessment-grade | Corrige folhas fotografadas via OMRChecker + Claude Vision | photos/ preenchido |
| /assessment-sync | Envia notas ao Google Classroom via gws CLI | scores.json + student-map.csv |

## Assessment pipeline (correção de provas impressas)

```
/assessment-create   # cria gabarito e folha de respostas impressa
/assessment-grade    # corrige fotos → scores.json + grade-report.md
/assessment-sync     # envia notas ao Google Classroom
```

Pré-requisitos externos: `pip install omrchecker` e gws CLI autenticado.

## Padrão de citação
ABNT NBR 6023 (padrão) | APA 7ª edição (configurável em `repo-manifest.md`)

## Princípios
- Toda afirmação de conteúdo rastreia a uma fonte
- Nenhum slide sem função pedagógica declarada para a mídia
- `pipeline-state.md` escrito ANTES de cada skill rodar
- QA obrigatório após cada skill — sem override silencioso

## Estrutura do plugin

```
skills/             # Skills do pipeline (formato marketplace)
agents/             # Subagents especializados
templates/          # Templates dos artefatos
docs/contracts/     # Contratos de qualidade por artefato
docs/qa/            # Regras de QA consolidadas
.claude-plugin/     # Manifesto do plugin e marketplace
```

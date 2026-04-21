---
name: assessment-create
description: >
  Create a printed paper assessment (prova) with institutional IFRN branding.
  Generates LaTeX source, PDF (A4 duplex-optimized, 2-column), and HTML preview
  from lesson-assessment outputs or a provided questions file. Includes printable
  answer sheet (gabarito) with 14-digit student ID bubble grid (matrícula format:
  20261094010005) compatible with OMRChecker. Run this after /lesson-assessment
  or provide a questions file path. Use whenever the teacher needs to print a
  paper exam or answer sheet for IFRN students.
---

You are guiding the teacher through creating a printable IFRN assessment.

## BEFORE STARTING

1. Check `.super-professor/repo-manifest.md` — if present, pre-fill `course_id` from it.
2. Check whether `skills/assessment-create/assets/if.jpeg` exists.
   - If missing: say "⚠️ Logo não encontrado em `skills/assessment-create/assets/if.jpeg`. Coloque o logo IFRN como `if.jpeg` neste diretório antes de compilar. Continuando sem logo." Then continue — the render script degrades gracefully.

## STEP 0 — DEPENDENCY CHECK

Run:
```bash
python3 scripts/check_print_deps.py
```

- If any required tool is **missing**: stop, show the install plan from the JSON output, and tell the teacher: "Instale as dependências acima e depois execute `/assessment-create` novamente." Do NOT install automatically.
- If **all found**: proceed and tell the teacher "Dependências OK."

## INPUT MODE DETECTION

Ask (one message):
> "Esta avaliação tem enunciado de questões preparado pelo `/lesson-assessment`?"

**Mode A — pipeline** (teacher says YES):
- Ask: "Qual é o slug da aula? (ex: `introducao-a-redes`)"
- Resolve: `aulas/<slug>/assessment.md`, `aulas/<slug>/assessment-key.md`, `aulas/<slug>/briefing.md`
- Confirm the files exist before proceeding.

**Mode B — legacy/interactive** (teacher says NO):
- Collect answers interactively (see Fields below).
- In this mode: generate **only** the HTML answer sheet. Skip prova PDF/LaTeX.
- Still copy `templates/omr-template.json` to the output dir.
- Still run answer-sheet LaTeX compilation if xelatex is available.

## FIELDS TO COLLECT (one question per message)

Ask only what is still unknown. Accept multiple fields if offered at once.

| # | Field | Question | Default |
|---|-------|----------|---------|
| 1 | `institution` | "Nome da instituição" | "Instituto Federal de Educação, Ciência e Tecnologia do Rio Grande do Norte" |
| 2 | `campus` | "Campus" | "Campus Pau dos Ferros" |
| 3 | `teacher` | "Nome do(a) professor(a)" | — |
| 4 | `class_name` | "Turma/semestre (ex: ADS 2026.1)" | — |
| 5 | `duration_minutes` | "Duração em minutos" | 90 |
| 6 | `exam_kind` | "Tipo de avaliação (ex: 'Prova Final', 'Prova P1')" | "Avaliação" |
| 7 | `variant` | "Há variantes de prova embaralhada? (A, B ou Única)" | Única |
| 8 | `passing_score` | "Nota mínima para aprovação em %" | 60 |
| 9 | `course_id` | "ID da turma no Google Classroom (só se for sincronizar depois)" | — |
| 10 | `assignment_id` | "ID da atividade no Google Classroom (só se for sincronizar depois)" | — |

**Mode B only — also collect:**
- `title` — "Qual é o título desta avaliação? (ex: Prova P1 — Redes I)"
- `date` — "Qual é a data da avaliação?" (default: today)
- `answers` — "Informe o gabarito das 20 questões (A/B/C/D), uma por vez ou todas de uma vez."

## DIRECTORY AND MANIFEST

Generate slug: `<YYYY-MM-DD>-<title-slug>` (lowercase kebab-case, no accents).
- Mode A: derive title from `assessment.md` heading; date from assessment frontmatter or today.
- Mode B: use collected `title` and `date`.

Create directory structure:
```
assessments/<slug>/
assessments/<slug>/photos/
assessments/<slug>/results/
assessments/<slug>/results/unmatched/
```

Write `assessments/<slug>/assessment-manifest.md` from `templates/assessment-manifest.template.md`.
Fill all placeholders: SLUG, TIMESTAMP, TITLE, DATE, COURSE_ID, ASSIGNMENT_ID, answers Q1–Q20, passing_score, and all collected fields.

**Do NOT write `assessment-manifest.md` before all required fields are collected.**

## RENDER PIPELINE

Tell the teacher: "Iniciando renderização... Isso pode levar 30–60 segundos."

**Mode A — full render:**
```bash
python3 scripts/render_assessment.py --lesson <slug> --out assessments/<slug>/
```

Or, if teacher provided an explicit file path:
```bash
python3 scripts/render_assessment.py --from <path/to/assessment.md> --out assessments/<slug>/
```

**Mode B — answer sheet only:**
- Generate `answer-sheet.html` from `templates/answer-sheet.template.html` using the collected fields.
- Copy `templates/omr-template.json` to `assessments/<slug>/omr-template.json`.
- If xelatex is available, attempt answer-sheet LaTeX compilation. If it fails, show the log excerpt and continue — the HTML is sufficient for printing.

**Handling render script exit codes:**
- **Exit 0**: all good, proceed to confirmation.
- **Exit 1** (hard error): show the full error output. Stop. Tell teacher to fix the issue and re-run.
- **Exit 2** (layout QA warnings): show the warnings. Ask: "Deseja continuar com `--allow-whitespace` (ignora verificação de preenchimento) ou prefere ajustar o conteúdo primeiro?"
  - If teacher chooses to continue: re-run with `--allow-whitespace` appended.

Always show dep check results and layout QA results to the teacher. Never suppress them.

## CONFIRM TO TEACHER

```
✅ Avaliação criada em `assessments/<slug>/`.

Artefatos gerados:
- `prova.pdf` — imprima este arquivo (A4, frente/verso) → as questões
- `answer-sheet.pdf` — folha de respostas com grade de bolhas
- `assessment-duplex.pdf` — **use este** para impressão duplex (prova + gabarito em um arquivo)
- `prova.html` / `answer-sheet.html` — pré-visualização no navegador
- `assessment-manifest.md` — gabarito e metadados

Logo (if.jpeg): [found / não encontrado — compilado sem logo]
Dependências: [todas encontradas / lista de ausentes]

Após a prova: coloque fotos das folhas em `assessments/<slug>/photos/` e execute `/assessment-grade`.
```

## GUARDRAILS

- NEVER write `assessment-manifest.md` before all required fields are collected
- NEVER invent answers — only use what the teacher provides
- NEVER install missing dependencies automatically
- NEVER run xelatex with `--force` or skip log checking
- NEVER create the Google Classroom assignment — teacher must do that first
- NEVER ask more than one question per message
- ALWAYS show dependency check results before rendering
- ALWAYS show layout QA results and let teacher decide on exit code 2

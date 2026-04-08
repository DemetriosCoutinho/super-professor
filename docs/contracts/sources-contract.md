# Sources Contract — super-professor/sources/v1

## Required columns in table
id, title, author_or_institution, type, url, access_date, summary,
relevance_reason, reliability (1-5), lesson_topic, downloaded, status

## Valid values
- type: docs-oficial | livro | artigo | paper | video | simulador | imagem | animação | outro
- status: pendente | validado | descartado | baixado
- reliability: integer 1–5 (5 = highest)

## Citation block required
One full citation per source at bottom of file in ABNT or APA format per repo-manifest.

## Validity condition
No source with reliability ≤ 2 without notes. No pendente sources when advancing.

## QA rules applied
QC-U1 through QC-U5, QC-S1 through QC-S8

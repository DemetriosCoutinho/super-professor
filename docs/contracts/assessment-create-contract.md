# Assessment-Create Contract — super-professor/assessment-create/v1

QA rules that the `/assessment-create` skill output must satisfy before the
pipeline may advance to `/assessment-grade`.

---

## AC-P1 — assessment-manifest.md exists and has all required fields

**Description**: The manifest file must be present and contain every required
field, including the new institutional metadata and the 14-digit matrícula
declaration.

**Required fields**: `slug`, `title`, `date`, `institution`, `campus`,
`teacher`, `answers` (Q1–Q20), `matricula_digits` (must equal 14).

**How to verify**:
```bash
# File exists
test -f assessment-manifest.md

# Check required fields are present and matricula_digits is correct
grep -E "^slug:" assessment-manifest.md
grep -E "^title:" assessment-manifest.md
grep -E "^date:" assessment-manifest.md
grep -E "^institution:" assessment-manifest.md
grep -E "^campus:" assessment-manifest.md
grep -E "^teacher:" assessment-manifest.md
grep -E "^matricula_digits: 14$" assessment-manifest.md
# Count answer entries Q1–Q20
grep -cE "^\s+- Q[0-9]+:" assessment-manifest.md   # expect 20
```

**Pass**: File exists, all fields present, `matricula_digits: 14`, 20 answer entries.
**Fail**: File missing, any required field absent, `matricula_digits` ≠ 14, or fewer than 20 answers.

---

## AC-P2 — prova.pdf exists and contains text for all 20 questions

**Description**: The generated exam PDF must be a readable PDF containing text
for all 20 questions (Q1 through Q20).

**How to verify**:
```bash
# File exists and is non-empty
test -s prova.pdf

# Extract text and check for question markers
pdftotext prova.pdf - | grep -cE "^(Q|Questão |[0-9]+\.)" | grep -qE "^[2-9][0-9]|^20$"
# Or simply check that the text contains "Q1" through "Q20"
for i in $(seq 1 20); do
  pdftotext prova.pdf - | grep -qiE "Q${i}[^0-9]|questão\s+${i}" || echo "MISSING Q${i}"
done
```

**Pass**: `prova.pdf` exists with non-zero size; `pdftotext` finds references to all 20 questions.
**Fail**: File missing, zero bytes, or any of Q1–Q20 not found in extracted text.

---

## AC-P3 — answer-sheet.pdf exists and renders a 14-column matrícula bubble grid

**Description**: The answer sheet PDF must render a bubble grid with exactly
14 columns to capture the full 14-digit IFRN matrícula.

**How to verify**:
```bash
# File exists and is non-empty
test -s answer-sheet.pdf

# Extract text and check for matrícula label and 14-column indicator
pdftotext answer-sheet.pdf - | grep -iE "matr[íi]cula"
# Visual/structural check: count bubble columns by inspecting the source HTML or TeX
grep -cE "D1[0-4]|D1[0-9]" answer-sheet.html   # expect columns D1–D14
```

**Pass**: `answer-sheet.pdf` exists; matrícula grid has 14 columns (D1–D14 present in source).
**Fail**: File missing, or grid has fewer than 14 columns.

---

## AC-P4 — assessment-duplex.pdf exists and is a valid merged PDF

**Description**: The duplex file must exist as a valid PDF that merges `prova.pdf`
and `answer-sheet.pdf` for double-sided printing.

**How to verify**:
```bash
# File exists and is non-empty
test -s assessment-duplex.pdf

# Validate PDF structure with qpdf
qpdf --check assessment-duplex.pdf

# Page count should be at least 2 (prova pages + answer sheet page)
qpdf --show-npages assessment-duplex.pdf   # expect ≥ 2
```

**Pass**: `assessment-duplex.pdf` exists, `qpdf --check` reports no errors, page count ≥ 2.
**Fail**: File missing, `qpdf --check` reports structural errors, or page count < 2.

---

## AC-P5 — prova.tex compiles without Overfull \hbox or undefined reference warnings

**Description**: The LaTeX source must compile cleanly. Overfull boxes indicate
layout overflow (content will be cut off in print); undefined references indicate
broken cross-references.

**How to verify**:
```bash
# File exists
test -f prova.tex

# Compile and inspect log (shell-escape required for minted)
xelatex -shell-escape -interaction=nonstopmode prova.tex 2>&1 | tee build.log

# Check for problematic warnings
grep -c "Overfull \\\\hbox" build.log     # expect 0
grep -c "undefined" build.log             # expect 0 (or only harmless refs)
grep -c "LaTeX Warning: Reference" build.log  # expect 0
```

**Pass**: Compilation exits 0; `build.log` contains zero `Overfull \hbox` warnings and zero undefined reference warnings.
**Fail**: Compilation fails, or any `Overfull \hbox` / undefined reference warning found.

---

## AC-P6 — omr-template.json has StudentID with exactly 14 fieldLabels

**Description**: The OMR template must declare exactly 14 digit fields for the
StudentID block, matching the IFRN 14-digit matrícula format.

**How to verify**:
```bash
# File exists
test -f omr-template.json

# Count fieldLabels entries in StudentID block
python3 -c "
import json, sys
with open('omr-template.json') as f:
    t = json.load(f)
labels = t['fieldBlocks']['StudentID']['fieldLabels']
print(f'StudentID fieldLabels count: {len(labels)}')
assert labels == ['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D13','D14'], 'FAIL'
print('PASS')
"
```

**Pass**: `fieldLabels` array contains exactly `["D1","D2",...,"D14"]` (14 entries).
**Fail**: Array has fewer or more than 14 entries, or labels are not in the expected sequence.

---

## AC-P7 — prova.html and answer-sheet.html exist as preview files

**Description**: HTML preview files must be generated alongside the PDFs so
that the professor can inspect the layout in a browser without requiring a PDF
viewer or LaTeX installation.

**How to verify**:
```bash
# Both files exist and are non-empty
test -s prova.html
test -s answer-sheet.html

# Basic HTML validity: each file should contain an <html> or <!DOCTYPE> tag
grep -ql "<!DOCTYPE\|<html" prova.html
grep -ql "<!DOCTYPE\|<html" answer-sheet.html
```

**Pass**: Both `prova.html` and `answer-sheet.html` exist with non-zero size and contain valid HTML structure.
**Fail**: Either file missing, zero bytes, or does not contain recognizable HTML.

---

## AC-P8 — build.log exists and contains no FATAL errors

**Description**: The build log must be written by the compilation step and must
not contain any FATAL-level errors, which would indicate an unrecoverable build
failure.

**How to verify**:
```bash
# File exists
test -f build.log

# No FATAL errors
grep -iE "^!|FATAL|Emergency stop" build.log   # expect no matches
grep -c "Output written" build.log             # expect ≥ 1 (successful xelatex output line)
```

**Pass**: `build.log` exists; no lines matching `^!`, `FATAL`, or `Emergency stop`; at least one `Output written` line.
**Fail**: File missing, or any FATAL/emergency-stop pattern found, or no successful output line.

---

## QA rules summary

| Rule  | Artifact                  | Key check                                   |
|-------|---------------------------|---------------------------------------------|
| AC-P1 | assessment-manifest.md    | All required fields + matricula_digits=14   |
| AC-P2 | prova.pdf                 | All 20 questions present (pdftotext)        |
| AC-P3 | answer-sheet.pdf          | 14-column matrícula bubble grid             |
| AC-P4 | assessment-duplex.pdf     | Valid merged PDF, ≥2 pages (qpdf --check)   |
| AC-P5 | prova.tex / build.log     | No Overfull \\hbox or undefined refs        |
| AC-P6 | omr-template.json         | StudentID has exactly 14 fieldLabels        |
| AC-P7 | prova.html, answer-sheet.html | Preview HTML files exist and are valid  |
| AC-P8 | build.log                 | No FATAL errors                             |

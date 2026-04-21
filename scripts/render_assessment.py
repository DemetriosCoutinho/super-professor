"""
render_assessment.py — Orchestrates the full assessment print render pipeline.

Usage:
    python3 scripts/render_assessment.py --lesson <slug>
    python3 scripts/render_assessment.py --from <path/to/assessment.md> --out <dir>
    python3 scripts/render_assessment.py --lesson <slug> --dry-run
    python3 scripts/render_assessment.py --lesson <slug> --allow-whitespace

Pipeline:
    Step 0 — Dependency check (xelatex, pygmentize, qpdf, tikz-uml.sty)
    Step 1 — Parse assessment.md + assessment-key.md
    Step 2 — Fill LaTeX and HTML templates
    Step 3 — Build PDFs with xelatex (2 passes each)
    Step 4 — Merge PDFs with qpdf → assessment-duplex.pdf
    Step 5 — Generate HTML preview (answer-sheet.html)
    Step 6 — Copy outputs to out_dir
    Step 7 — Run validate_layout
"""

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Locate repo root (this script lives in scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

TEMPLATES_DIR = REPO_ROOT / "templates"
ASSETS_DIR = REPO_ROOT / "skills" / "assessment-create" / "assets"
LOGO_PATH = ASSETS_DIR / "if.jpeg"

DEFAULT_INSTRUCTIONS = (
    "Leia atentamente cada questão. Marque apenas uma alternativa por questão. "
    "Use caneta azul ou preta. Não é permitido o uso de qualquer material de consulta."
)


# ---------------------------------------------------------------------------
# Step 0 — Dependency check
# ---------------------------------------------------------------------------

def check_dependencies(dry_run: bool = False) -> None:
    """Check for required external tools. Exit 1 if any required dep is missing."""
    try:
        from check_print_deps import check_deps  # noqa: PLC0415
    except ImportError:
        sys.path.insert(0, str(SCRIPT_DIR))
        from check_print_deps import check_deps  # noqa: PLC0415

    result = check_deps()

    if not result["all_found"]:
        print("[ERROR] Missing required dependencies:", ", ".join(result["missing"]))
        print("Run `python3 scripts/check_print_deps.py` to see install instructions")
        platform = result["platform"]
        plan = result["install_plan"].get(platform, result["install_plan"].get("debian", ""))
        if plan:
            print(f"Install plan ({platform}):\n  {plan}")
        sys.exit(1)

    if not dry_run:
        print("[OK] All required dependencies found:", ", ".join(result["found"]))

    # Check tikz-uml.sty (warn only)
    try:
        proc = subprocess.run(
            ["kpsewhich", "tikz-uml.sty"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            print("[WARN] tikz-uml.sty not found — UML diagrams may fail to compile.")
        elif not dry_run:
            print("[OK] tikz-uml.sty found:", proc.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[WARN] kpsewhich not found — cannot verify tikz-uml.sty availability.")


# ---------------------------------------------------------------------------
# Step 1 — Parse inputs
# ---------------------------------------------------------------------------

def parse_yaml_frontmatter(text: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter (between --- delimiters) from markdown text.
    Returns (frontmatter_dict, body_text).
    Falls back to {} frontmatter if none found.
    """
    import yaml  # noqa: PLC0415

    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(text)
    if match:
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except Exception:
            fm = {}
        body = text[match.end():]
    else:
        fm = {}
        body = text
    return fm, body


def extract_heading(body: str) -> str:
    """Extract the first # heading from markdown body."""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def extract_field(body: str, label: str) -> str:
    """Extract value from a **Label:** VALUE line."""
    pattern = re.compile(
        r"^\s*\*\*" + re.escape(label) + r":\*\*\s*(.+)$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def extract_answers_from_key(key_fm: dict, key_body: str) -> dict[str, str]:
    """
    Extract answers map from assessment-key.md frontmatter.
    The frontmatter 'answers' field may be:
      - list of {Q1: A} dicts  → normalize to {'q1': 'A'}
      - dict {'Q1': 'A', ...}  → normalize to {'q1': 'A'}
    """
    answers_raw = key_fm.get("answers", {})
    answers: dict[str, str] = {}

    if isinstance(answers_raw, list):
        for item in answers_raw:
            if isinstance(item, dict):
                for k, v in item.items():
                    answers[k.lower()] = str(v).upper()
    elif isinstance(answers_raw, dict):
        for k, v in answers_raw.items():
            answers[k.lower()] = str(v).upper()

    # Also try to parse from body: lines like "**Q1:** A" or "- Q1: A"
    if not answers:
        for match in re.finditer(r"(?:Q|Quest[aã]o\s*)(\d+)[:\s]+([A-Da-d])", key_body):
            q_num = int(match.group(1))
            letter = match.group(2).upper()
            answers[f"q{q_num}"] = letter

    return answers


def parse_questions_from_body(body: str) -> list[dict]:
    """
    Parse question blocks from assessment.md body.
    Looks for:
      ## Questão N
      ### N.
      **N.**
    Returns list of dicts: {num, stem, alternatives: [A,B,C,D]}
    """
    questions = []

    # Split on question headers
    # Supports: "## Questão 1", "### 1.", "**1.**", "---\n**1."
    header_pattern = re.compile(
        r"(?:^#{1,3}\s+(?:Quest[aã]o\s+)?(\d+)[.\s]|^\*\*(\d+)\.\*\*)",
        re.MULTILINE,
    )

    matches = list(header_pattern.finditer(body))
    if not matches:
        return questions

    for i, match in enumerate(matches):
        q_num = int(match.group(1) or match.group(2))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].strip()

        # Extract alternatives (lines starting with a) b) c) d) or A) B) C) D)
        alt_pattern = re.compile(
            r"^[*\s]*([A-Da-d])\)\s+(.+?)(?=\n[*\s]*[A-Da-d]\)|$)",
            re.MULTILINE | re.DOTALL,
        )
        alt_matches = list(alt_pattern.finditer(block))

        if alt_matches:
            stem_end = alt_matches[0].start()
            stem = block[:stem_end].strip()
            alternatives = []
            for am in alt_matches:
                letter = am.group(1).upper()
                text = am.group(2).strip()
                alternatives.append((letter, text))
        else:
            stem = block.strip()
            alternatives = []

        questions.append({
            "num": q_num,
            "stem": stem,
            "alternatives": alternatives,
        })

    return questions


def parse_briefing(briefing_path: Path) -> dict:
    """Extract course_short and exam_kind from briefing.md if it exists."""
    result = {"course_short": "IFRN", "exam_kind": "Avaliação"}
    if not briefing_path.exists():
        return result

    try:
        text = briefing_path.read_text(encoding="utf-8")
        fm, body = parse_yaml_frontmatter(text)

        if "course_short" in fm:
            result["course_short"] = str(fm["course_short"])
        if "exam_kind" in fm:
            result["exam_kind"] = str(fm["exam_kind"])

        # Try body fields
        for line in body.splitlines():
            line = line.strip()
            if re.search(r"course.short|sigla.curso|curso.abrev", line, re.IGNORECASE):
                m = re.search(r"[:=]\s*(\S+)", line)
                if m:
                    result["course_short"] = m.group(1).strip("\"'")
            if re.search(r"exam.kind|tipo.avalia|modalidade", line, re.IGNORECASE):
                m = re.search(r"[:=]\s*(.+)$", line)
                if m:
                    result["exam_kind"] = m.group(1).strip("\"'*")
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Markdown → LaTeX conversion
# ---------------------------------------------------------------------------

LATEX_ESCAPE = [
    ("\\", r"\textbackslash{}"),  # must be first
    ("&", r"\&"),
    ("%", r"\%"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("$", r"\$"),
    ("^", r"\^{}"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
]


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in plain text (not in commands)."""
    # We process backslash first separately since we replace it with a command
    result = text.replace("\\", "\x00BACKSLASH\x00")
    for char, escaped in LATEX_ESCAPE[1:]:
        result = result.replace(char, escaped)
    result = result.replace("\x00BACKSLASH\x00", r"\textbackslash{}")
    return result


def md_inline_to_latex(text: str) -> str:
    """Convert inline markdown to LaTeX (bold, italic, inline code)."""
    # Bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", lambda m: r"\textbf{" + m.group(1) + "}", text)
    # Italic *text* (not **text**)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", lambda m: r"\textit{" + m.group(1) + "}", text)
    # Inline code `code`
    text = re.sub(r"`([^`]+)`", lambda m: r"\texttt{" + escape_latex(m.group(1)) + "}", text)
    return text


def convert_code_blocks(text: str) -> str:
    """
    Convert fenced code blocks to LaTeX minted or umlpic environments.
    ```python ... ``` → \\begin{minted}{python}...\\end{minted}
    ```uml ... ```   → \\umlpic{ ... }
    """
    def replace_block(match: re.Match) -> str:
        lang = match.group(1).strip().lower()
        content = match.group(2)
        if lang == "uml":
            return r"\umlpic{" + "\n" + content + "\n}"
        if lang:
            return f"\\begin{{minted}}{{{lang}}}\n{content}\n\\end{{minted}}"
        return f"\\begin{{minted}}{{text}}\n{content}\n\\end{{minted}}"

    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    return pattern.sub(replace_block, text)


def markdown_to_latex(text: str) -> str:
    """Convert a markdown text block to LaTeX."""
    # Handle code blocks first (before escaping)
    text = convert_code_blocks(text)
    # Split on minted/umlpic environments to avoid escaping their content
    parts = re.split(r"(\\begin\{minted\}.*?\\end\{minted\}|\\umlpic\{.*?\})", text, flags=re.DOTALL)
    result_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Plain text part — escape and apply inline formatting
            part = escape_latex(part)
            part = md_inline_to_latex(part)
        result_parts.append(part)
    return "".join(result_parts)


def render_question_latex(q: dict) -> str:
    """Render a single question dict to LaTeX questao environment."""
    num = q["num"]
    stem = markdown_to_latex(q["stem"])

    alts_latex = ""
    for letter, text in q["alternatives"]:
        alts_latex += f"  \\item {markdown_to_latex(text)}\n"

    if alts_latex:
        return (
            f"\\begin{{questao}}{{{num}}}\n"
            f"{stem}\n"
            f"\\begin{{alternativas}}\n"
            f"{alts_latex}"
            f"\\end{{alternativas}}\n"
            f"\\end{{questao}}\n"
        )
    else:
        return (
            f"\\begin{{questao}}{{{num}}}\n"
            f"{stem}\n"
            f"\\end{{questao}}\n"
        )


# ---------------------------------------------------------------------------
# Step 2 — Fill templates
# ---------------------------------------------------------------------------

def fill_prova_template(
    template_text: str,
    course_short: str,
    exam_kind: str,
    logo_path: str,
    discipline: str,
    teacher: str,
    date: str,
    total_points: str,
    instructions: str,
    questions_latex: str,
) -> str:
    """Fill assessment-print.template.tex placeholders."""
    replacements = {
        "{{COURSE_SHORT}}": course_short,
        "{{EXAM_KIND}}": exam_kind,
        "{{LOGO_PATH}}": logo_path,
        "{{DISCIPLINE}}": discipline,
        "{{TEACHER}}": teacher,
        "{{DATE}}": date,
        "{{TOTAL_POINTS}}": total_points,
        "{{INSTRUCTIONS}}": instructions,
        "{{QUESTIONS}}": questions_latex,
    }
    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def fill_answer_sheet_tex_template(
    template_text: str,
    logo_path: str,
    title: str,
    date: str,
    course_short: str,
) -> str:
    """Fill answer-sheet.template.tex placeholders."""
    replacements = {
        "{{LOGO_PATH}}": logo_path,
        "{{TITLE}}": title,
        "{{DATE}}": date,
        "{{COURSE_SHORT}}": course_short,
    }
    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def generate_question_html(q_range: range) -> str:
    """Generate HTML bubble rows for a range of question numbers."""
    rows = []
    for n in q_range:
        options_html = ""
        for letter in ["A", "B", "C", "D"]:
            options_html += (
                f'<div class="option">'
                f'<span>{letter}</span>'
                f'<div class="opt-bubble"></div>'
                f"</div>"
            )
        rows.append(
            f'<div class="question-row">'
            f'<span class="q-num">{n}</span>'
            f'<div class="options">{options_html}</div>'
            f"</div>"
        )
    return "\n".join(rows)


def fill_answer_sheet_html_template(
    template_text: str,
    logo_src: str,
    title: str,
    date: str,
    questions_left_html: str,
    questions_right_html: str,
) -> str:
    """Fill answer-sheet.template.html placeholders."""
    replacements = {
        "{{LOGO_SRC}}": logo_src,
        "{{TITLE}}": title,
        "{{DATE}}": date,
        "{{QUESTIONS_LEFT}}": questions_left_html,
        "{{QUESTIONS_RIGHT}}": questions_right_html,
    }
    result = template_text
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


# ---------------------------------------------------------------------------
# Step 3 — Build PDFs
# ---------------------------------------------------------------------------

def run_xelatex(tex_file: Path, build_dir: Path) -> Path:
    """
    Run xelatex twice on tex_file in build_dir.
    Returns path to the .log file.
    Raises RuntimeError if xelatex exits non-zero.
    """
    log_file = build_dir / tex_file.with_suffix(".log").name

    for pass_num in range(1, 3):
        cmd = [
            "xelatex",
            "-shell-escape",
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_file.name,
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(build_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "xelatex not found. "
                "Run `python3 scripts/check_print_deps.py` to see install instructions."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"xelatex timed out on pass {pass_num} for {tex_file.name}")

        if proc.returncode != 0:
            # Try to extract the error from log or stdout
            log_content = ""
            if log_file.exists():
                log_content = log_file.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(
                f"xelatex failed (pass {pass_num}, rc={proc.returncode}) "
                f"for {tex_file.name}.\n"
                f"stderr: {proc.stderr[:500]}\n"
                f"Last 1000 chars of log:\n{log_content[-1000:]}"
            )

    return log_file


def check_log_for_errors(log_path: Path) -> list[str]:
    """
    Inspect a xelatex log file for serious issues.
    Returns list of warning/error strings (empty = clean).
    """
    issues = []
    if not log_path.exists():
        return ["Log file not found: " + str(log_path)]

    content = log_path.read_text(encoding="utf-8", errors="replace")

    # Hard LaTeX errors: lines starting with "! "
    hard_errors = [line for line in content.splitlines() if line.startswith("! ")]
    if hard_errors:
        issues.append("Hard LaTeX errors: " + "; ".join(hard_errors[:5]))

    # Undefined references warning
    if "LaTeX Warning: There were undefined references" in content:
        issues.append("Undefined references in " + log_path.name)

    # Overfull hboxes (warn if widespread — more than 3)
    overfull_count = content.count("Overfull \\hbox")
    if overfull_count > 3:
        issues.append(
            f"Widespread Overfull \\hbox ({overfull_count} occurrences) in {log_path.name} "
            "— consider reducing content width or font size."
        )

    return issues


# ---------------------------------------------------------------------------
# Step 4 — Merge PDFs
# ---------------------------------------------------------------------------

def merge_pdfs(build_dir: Path) -> Path:
    """Merge prova.pdf and answer-sheet.pdf into assessment-duplex.pdf."""
    prova_pdf = build_dir / "prova.pdf"
    answer_pdf = build_dir / "answer-sheet.pdf"
    duplex_pdf = build_dir / "assessment-duplex.pdf"

    if not prova_pdf.exists():
        raise FileNotFoundError(f"prova.pdf not found in {build_dir}")
    if not answer_pdf.exists():
        raise FileNotFoundError(f"answer-sheet.pdf not found in {build_dir}")

    cmd = [
        "qpdf",
        "--empty",
        "--pages",
        str(prova_pdf), "1-z",
        str(answer_pdf), "1-z",
        "--",
        str(duplex_pdf),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(
            f"qpdf failed (rc={proc.returncode}): {proc.stderr}"
        )
    return duplex_pdf


# ---------------------------------------------------------------------------
# Step 5 — HTML preview
# ---------------------------------------------------------------------------

def logo_to_data_uri(logo_path: Path) -> str:
    """Encode logo as base64 data-URI if it exists, else return empty string."""
    if not logo_path.exists():
        return ""
    data = logo_path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    suffix = logo_path.suffix.lstrip(".").lower()
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# Step 6 — Copy outputs
# ---------------------------------------------------------------------------

def copy_outputs(build_dir: Path, out_dir: Path, artifacts: list[str]) -> None:
    """Copy named artifacts from build_dir to out_dir, concatenating .log files."""
    out_dir.mkdir(parents=True, exist_ok=True)

    log_content_parts = []
    for name in artifacts:
        src = build_dir / name
        if not src.exists():
            print(f"[WARN] artifact not found, skipping: {src}")
            continue
        dst = out_dir / name
        if src.suffix == ".log":
            log_content_parts.append(f"=== {name} ===\n" + src.read_text(encoding="utf-8", errors="replace"))
        else:
            shutil.copy2(str(src), str(dst))

    # Write concatenated build.log
    if log_content_parts:
        (out_dir / "build.log").write_text(
            "\n\n".join(log_content_parts), encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, str]:
    """
    Resolve assessment.md, assessment-key.md, out_dir, and slug from args.
    Returns (assessment_path, key_path, out_dir, slug).
    """
    if args.lesson:
        slug = args.lesson
        aula_dir = REPO_ROOT / "aulas" / slug
        assessment_path = aula_dir / "assessment.md"
        key_path = aula_dir / "assessment-key.md"
        out_dir = Path(args.out) if args.out else REPO_ROOT / "assessments" / slug
    elif args.from_path:
        assessment_path = Path(args.from_path).resolve()
        key_path = assessment_path.parent / "assessment-key.md"
        slug = assessment_path.parent.name
        out_dir = Path(args.out) if args.out else REPO_ROOT / "assessments" / slug
    else:
        print("[ERROR] Provide either --lesson <slug> or --from <path>")
        sys.exit(1)

    return assessment_path, key_path, out_dir, slug


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    parser = argparse.ArgumentParser(
        description="Render assessment PDFs from assessment.md + assessment-key.md"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--lesson", metavar="SLUG", help="Lesson slug (reads from aulas/<slug>/)")
    group.add_argument("--from", dest="from_path", metavar="PATH", help="Explicit path to assessment.md")
    parser.add_argument("--out", metavar="DIR", help="Output directory")
    parser.add_argument("--allow-whitespace", action="store_true", help="Skip fill-rate check")
    parser.add_argument("--dry-run", action="store_true", help="Check deps and parse inputs only")
    args = parser.parse_args()

    if not args.lesson and not args.from_path:
        parser.print_help()
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 0 — Dependency check
    # -----------------------------------------------------------------------
    print("[Step 0] Checking dependencies...")
    check_dependencies(dry_run=args.dry_run)

    # -----------------------------------------------------------------------
    # Step 1 — Parse inputs
    # -----------------------------------------------------------------------
    print("[Step 1] Parsing inputs...")
    assessment_path, key_path, out_dir, slug = resolve_paths(args)

    if not assessment_path.exists():
        print(f"[ERROR] assessment.md not found: {assessment_path}")
        sys.exit(1)

    assessment_text = assessment_path.read_text(encoding="utf-8")
    assessment_fm, assessment_body = parse_yaml_frontmatter(assessment_text)

    # Key file
    if not key_path.exists():
        print(f"[ERROR] assessment-key.md not found: {key_path}")
        sys.exit(1)
    key_text = key_path.read_text(encoding="utf-8")
    key_fm, key_body = parse_yaml_frontmatter(key_text)

    # Extract metadata from assessment.md
    title = extract_heading(assessment_body) or assessment_fm.get("title", "Avaliação")
    discipline = (
        assessment_fm.get("discipline")
        or extract_field(assessment_body, "Disciplina")
        or "—"
    )
    teacher = (
        assessment_fm.get("teacher")
        or extract_field(assessment_body, "Professor")
        or extract_field(assessment_body, "Professor(a)")
        or "Prof. Demetrios"
    )
    date = (
        assessment_fm.get("date")
        or extract_field(assessment_body, "Data")
        or "___/___/______"
    )
    class_name = (
        assessment_fm.get("class_name")
        or extract_field(assessment_body, "Turma")
        or ""
    )

    # Extract answers from key
    answers = extract_answers_from_key(key_fm, key_body)
    shuffle_map = key_fm.get("shuffle_map", {})
    print(f"  Answers loaded: {len(answers)} questions")

    # Briefing (for course_short, exam_kind)
    briefing_info = {"course_short": "IFRN", "exam_kind": "Avaliação"}
    if args.lesson:
        briefing_path = REPO_ROOT / "aulas" / slug / "briefing.md"
        briefing_info = parse_briefing(briefing_path)

    course_short = assessment_fm.get("course_short") or briefing_info["course_short"]
    exam_kind = assessment_fm.get("exam_kind") or briefing_info["exam_kind"]

    # Parse question blocks
    questions = parse_questions_from_body(assessment_body)
    print(f"  Questions parsed: {len(questions)}")

    # Compute points
    q_count = len(questions) if questions else 20
    total_points = str(100)  # Fixed at 100 per spec

    # Instructions
    instructions = (
        assessment_fm.get("instructions")
        or briefing_info.get("instructions", DEFAULT_INSTRUCTIONS)
    )

    if args.dry_run:
        print("[DRY RUN] Inputs parsed successfully. Skipping compilation.")
        print(f"  Title:        {title}")
        print(f"  Discipline:   {discipline}")
        print(f"  Teacher:      {teacher}")
        print(f"  Date:         {date}")
        print(f"  Course short: {course_short}")
        print(f"  Exam kind:    {exam_kind}")
        print(f"  Questions:    {q_count}")
        print(f"  Answers:      {len(answers)}")
        print(f"  Output dir:   {out_dir}")
        return

    # -----------------------------------------------------------------------
    # Step 2 — Fill templates
    # -----------------------------------------------------------------------
    print("[Step 2] Filling templates...")

    prova_tpl_path = TEMPLATES_DIR / "assessment-print.template.tex"
    answer_sheet_tex_tpl_path = TEMPLATES_DIR / "answer-sheet.template.tex"
    answer_sheet_html_tpl_path = TEMPLATES_DIR / "answer-sheet.template.html"

    for tpl in [prova_tpl_path, answer_sheet_tex_tpl_path, answer_sheet_html_tpl_path]:
        if not tpl.exists():
            print(f"[ERROR] Template not found: {tpl}")
            sys.exit(1)

    prova_tpl = prova_tpl_path.read_text(encoding="utf-8")
    answer_tex_tpl = answer_sheet_tex_tpl_path.read_text(encoding="utf-8")
    answer_html_tpl = answer_sheet_html_tpl_path.read_text(encoding="utf-8")

    # Logo handling
    logo_exists = LOGO_PATH.exists()
    if not logo_exists:
        print(f"[WARN] Logo not found at {LOGO_PATH} — using placeholder.")
        logo_latex = r"\fbox{LOGO}"
        logo_src_html = ""
    else:
        # LaTeX build will use the file copied into the build dir
        logo_latex = "if.jpeg"
        logo_src_html = logo_to_data_uri(LOGO_PATH)

    # Render questions to LaTeX
    questions_latex = "\n".join(render_question_latex(q) for q in questions)
    if not questions_latex.strip():
        print("[WARN] No question blocks parsed — {{QUESTIONS}} will be empty.")

    prova_filled = fill_prova_template(
        prova_tpl,
        course_short=course_short,
        exam_kind=exam_kind,
        logo_path=logo_latex,
        discipline=discipline,
        teacher=teacher,
        date=date,
        total_points=total_points,
        instructions=instructions,
        questions_latex=questions_latex,
    )

    answer_tex_filled = fill_answer_sheet_tex_template(
        answer_tex_tpl,
        logo_path=logo_latex,
        title=title,
        date=date,
        course_short=course_short,
    )

    questions_left_html = generate_question_html(range(1, 11))
    questions_right_html = generate_question_html(range(11, 21))

    answer_html_filled = fill_answer_sheet_html_template(
        answer_html_tpl,
        logo_src=logo_src_html,
        title=title,
        date=date,
        questions_left_html=questions_left_html,
        questions_right_html=questions_right_html,
    )

    # -----------------------------------------------------------------------
    # Step 3 — Build PDFs
    # -----------------------------------------------------------------------
    print("[Step 3] Building PDFs with xelatex...")

    with tempfile.TemporaryDirectory(prefix="assessment_build_") as build_dir_str:
        build_dir = Path(build_dir_str)

        # Copy logo to build dir if it exists
        if logo_exists:
            shutil.copy2(str(LOGO_PATH), str(build_dir / "if.jpeg"))

        # Write .tex files
        prova_tex = build_dir / "prova.tex"
        answer_tex = build_dir / "answer-sheet.tex"
        prova_tex.write_text(prova_filled, encoding="utf-8")
        answer_tex.write_text(answer_tex_filled, encoding="utf-8")

        # Write HTML preview (step 5 can happen before build too)
        prova_html_dest = build_dir / "prova.html"
        answer_html_dest = build_dir / "answer-sheet.html"

        # Run xelatex
        all_log_issues = []

        try:
            print("  Compiling prova.tex...")
            prova_log = run_xelatex(prova_tex, build_dir)
            issues = check_log_for_errors(prova_log)
            if issues:
                for issue in issues:
                    print(f"  [LOG-WARN] {issue}")
                all_log_issues.extend(issues)
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        try:
            print("  Compiling answer-sheet.tex...")
            answer_log = run_xelatex(answer_tex, build_dir)
            issues = check_log_for_errors(answer_log)
            if issues:
                for issue in issues:
                    print(f"  [LOG-WARN] {issue}")
                all_log_issues.extend(issues)
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        # -----------------------------------------------------------------------
        # Step 4 — Merge PDFs
        # -----------------------------------------------------------------------
        print("[Step 4] Merging PDFs with qpdf...")
        try:
            duplex_pdf = merge_pdfs(build_dir)
            print(f"  Merged: {duplex_pdf.name}")
        except (RuntimeError, FileNotFoundError) as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        # -----------------------------------------------------------------------
        # Step 5 — HTML preview
        # -----------------------------------------------------------------------
        print("[Step 5] Writing HTML preview...")
        answer_html_dest.write_text(answer_html_filled, encoding="utf-8")

        # Simple prova.html — wrap the filled tex in a preformatted HTML for reference
        # (There is no prova.html template; write a minimal one)
        prova_html_dest.write_text(
            f"<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            f"<title>{title}</title></head><body>"
            f"<p>Ver <a href='prova.pdf'>prova.pdf</a> para o documento imprimível.</p>"
            f"</body></html>",
            encoding="utf-8",
        )

        # -----------------------------------------------------------------------
        # Step 6 — Copy outputs
        # -----------------------------------------------------------------------
        print(f"[Step 6] Copying outputs to {out_dir} ...")
        artifacts = [
            "prova.tex",
            "prova.pdf",
            "prova.html",
            "answer-sheet.tex",
            "answer-sheet.pdf",
            "answer-sheet.html",
            "assessment-duplex.pdf",
            "prova.log",
            "answer-sheet.log",
        ]
        copy_outputs(build_dir, out_dir, artifacts)
        print(f"  Output directory: {out_dir}")

    # -----------------------------------------------------------------------
    # Step 7 — Run validate_layout
    # -----------------------------------------------------------------------
    print("[Step 7] Running layout validation...")
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from validate_layout import validate  # noqa: PLC0415

        issues = validate(str(out_dir), allow_whitespace=args.allow_whitespace)
        if issues:
            print("[VALIDATE] Issues found:")
            for issue in issues:
                print(f"  - {issue}")
            print(
                "[WARN] Soft failure (exit 2): outputs copied, but layout checks failed. "
                "Re-run with --allow-whitespace to suppress fill-rate check."
            )
            sys.exit(2)
        else:
            print("[VALIDATE] All checks passed.")
    except ImportError:
        print("[WARN] validate_layout module not found — skipping layout validation.")

    print("\n[DONE] Assessment render complete.")
    print(f"  Output: {out_dir}")


if __name__ == "__main__":
    main()

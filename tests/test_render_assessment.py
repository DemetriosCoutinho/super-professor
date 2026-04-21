"""
test_render_assessment.py — Unit tests for the assessment-create render pipeline.

Tests cover:
  - check_print_deps.check_deps() shape
  - render_assessment parse helpers
  - markdown_to_latex / escape_latex / convert_code_blocks
  - validate_layout.validate() with missing and dummy files
  - smoke test for compute_scores (regression guard)

External tools (xelatex, qpdf) are NOT required — tests that need them are
individually guarded with @pytest.mark.skipif.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure scripts/ is importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "assessment-sample"

sys.path.insert(0, str(SCRIPTS_DIR))


# ===========================================================================
# 1 & 2 — check_print_deps
# ===========================================================================

def test_check_print_deps_returns_dict():
    """check_deps() must return a dict with the expected top-level keys."""
    from check_print_deps import check_deps  # noqa: PLC0415

    result = check_deps()

    assert isinstance(result, dict)
    for key in ("platform", "found", "missing", "all_found", "install_plan"):
        assert key in result, f"Key '{key}' missing from check_deps() result"

    # Types
    assert isinstance(result["platform"], str)
    assert isinstance(result["found"], list)
    assert isinstance(result["missing"], list)
    assert isinstance(result["all_found"], bool)
    assert isinstance(result["install_plan"], dict)

    # found ∪ missing == all required executables (no overlaps)
    all_deps = set(result["found"]) | set(result["missing"])
    assert "xelatex" in all_deps
    assert "qpdf" in all_deps
    assert "pygmentize" in all_deps


def test_check_print_deps_install_plan_has_all_platforms():
    """install_plan must have entries for macos, debian, and fedora."""
    from check_print_deps import check_deps  # noqa: PLC0415

    result = check_deps()
    plan = result["install_plan"]

    assert "macos" in plan, "install_plan missing 'macos'"
    assert "debian" in plan, "install_plan missing 'debian'"
    assert "fedora" in plan, "install_plan missing 'fedora'"

    # Each plan should be a non-empty string
    for platform_key in ("macos", "debian", "fedora"):
        assert isinstance(plan[platform_key], str)
        assert len(plan[platform_key]) > 0, f"install_plan['{platform_key}'] is empty"


# ===========================================================================
# 3 — parse_questions_from_body + extract_heading
# ===========================================================================

def test_parse_assessment_md():
    """
    parse_questions_from_body on the fixture assessment.md should yield
    at least 3 questions, each with 4 alternatives.
    extract_heading should find 'Fundamentos de Programação'.
    """
    from render_assessment import parse_yaml_frontmatter, parse_questions_from_body, extract_heading  # noqa: PLC0415

    text = (FIXTURE_DIR / "assessment.md").read_text(encoding="utf-8")
    fm, body = parse_yaml_frontmatter(text)

    # Frontmatter check
    assert fm.get("assessment_id") == "TEST-001"
    assert fm.get("schema") == "super-professor/assessment/v1"

    # Heading
    title = extract_heading(body)
    assert "Fundamentos de Programação" in title, f"Title not found: {title!r}"

    # Questions
    questions = parse_questions_from_body(body)
    assert len(questions) >= 3, f"Expected >=3 questions, got {len(questions)}"

    for q in questions:
        assert "num" in q
        assert "stem" in q
        assert "alternatives" in q
        assert len(q["alternatives"]) == 4, (
            f"Question {q['num']} has {len(q['alternatives'])} alternatives, expected 4"
        )


# ===========================================================================
# 4 — markdown_to_latex: special character escaping
# ===========================================================================

def test_markdown_to_latex_escaping():
    """
    escape_latex must convert LaTeX special characters correctly.
    Tests &, %, #, _ → their escaped forms.
    """
    from render_assessment import escape_latex  # noqa: PLC0415

    assert escape_latex("a & b") == r"a \& b"
    assert escape_latex("50%") == r"50\%"
    assert escape_latex("#include") == r"\#include"
    assert escape_latex("my_var") == r"my\_var"
    # Backslash is handled too
    result = escape_latex("a\\b")
    assert r"\textbackslash{}" in result


def test_markdown_to_latex_dollar_and_caret():
    """$ and ^ must also be escaped — verify they produce LaTeX-safe output."""
    from render_assessment import escape_latex  # noqa: PLC0415

    dollar_result = escape_latex("$x$")
    assert r"\$" in dollar_result, f"$ not escaped: {dollar_result!r}"

    caret_result = escape_latex("x^2")
    # escape_latex replaces ^ with \^{} then further escapes { and } → \^\{\}
    # Either form is LaTeX-safe; just confirm ^ itself is gone and \^ is present.
    assert "^" not in caret_result.replace(r"\^", ""), (
        f"Bare ^ still present: {caret_result!r}"
    )
    assert r"\^" in caret_result, f"Caret not escaped: {caret_result!r}"


# ===========================================================================
# 5 — markdown_to_latex: fenced code blocks
# ===========================================================================

def test_markdown_to_latex_code_blocks():
    """
    convert_code_blocks must turn ```python ... ``` into minted environments.
    """
    from render_assessment import convert_code_blocks  # noqa: PLC0415

    md = '```python\nprint("hi")\n```'
    result = convert_code_blocks(md)

    assert r"\begin{minted}{python}" in result, f"minted begin not found in: {result!r}"
    assert r"\end{minted}" in result, f"minted end not found in: {result!r}"
    assert 'print("hi")' in result


def test_markdown_to_latex_code_blocks_no_lang():
    """Fenced blocks without a language tag should use 'text' as the language."""
    from render_assessment import convert_code_blocks  # noqa: PLC0415

    md = "```\nhello world\n```"
    result = convert_code_blocks(md)

    assert r"\begin{minted}{text}" in result
    assert r"\end{minted}" in result


def test_markdown_to_latex_uml_block():
    """UML fenced blocks must produce a \\umlpic{} command, not minted."""
    from render_assessment import convert_code_blocks  # noqa: PLC0415

    md = "```uml\nA -> B : message\n```"
    result = convert_code_blocks(md)

    assert r"\umlpic{" in result
    assert r"\begin{minted}" not in result


# ===========================================================================
# 6 — validate_layout: missing output directory / missing files
# ===========================================================================

def test_validate_layout_missing_directory():
    """validate() on a non-existent path must return at least one issue."""
    from validate_layout import validate  # noqa: PLC0415

    issues = validate("/tmp/nonexistent_assessment_abc123_xyzzy")
    assert len(issues) >= 1
    assert any("does not exist" in issue or "Missing" in issue for issue in issues)


def test_validate_layout_missing_files(tmp_path):
    """
    An empty directory must trigger file-missing issues (AC-P2, AC-P3, etc.).
    """
    from validate_layout import validate  # noqa: PLC0415

    issues = validate(str(tmp_path), allow_whitespace=True)

    # We expect at least one issue per missing required file
    assert len(issues) >= 3

    issue_text = " ".join(issues)
    assert "prova.pdf" in issue_text or "AC-P2" in issue_text
    assert "answer-sheet.pdf" in issue_text or "AC-P3" in issue_text


# ===========================================================================
# 7 — validate_layout: dummy files present (only Q-CNT issues expected)
# ===========================================================================

def test_validate_layout_ok_with_dummy_files(tmp_path):
    """
    With all required files present as tiny text stubs, validate() should
    not report file-missing issues (AC-P2/P3/P4/P7).
    It MAY report Q-CNT issues (can't find question text in dummy text-PDF)
    or AC-P5 issues if build.log has no content.
    """
    from validate_layout import validate  # noqa: PLC0415

    # Create all expected output files as tiny text stubs
    required_files = [
        "prova.pdf",
        "answer-sheet.pdf",
        "assessment-duplex.pdf",
        "prova.html",
        "answer-sheet.html",
        "build.log",
    ]
    for fname in required_files:
        (tmp_path / fname).write_text(f"dummy content for {fname}\n", encoding="utf-8")

    issues = validate(str(tmp_path), allow_whitespace=True)

    # No file-existence issues (AC-P2, AC-P3, AC-P4, AC-P7)
    file_missing_issues = [i for i in issues if "Missing file" in i]
    assert len(file_missing_issues) == 0, (
        f"Unexpected file-missing issues: {file_missing_issues}"
    )

    # Any remaining issues should be Q-CNT (text extraction from dummy PDFs)
    # or AC-P5 (no hard errors expected in empty build.log)
    for issue in issues:
        assert "AC-P2" not in issue
        assert "AC-P3" not in issue
        assert "AC-P4" not in issue
        # AC-P7 (HTML files) should also be gone
        assert not (issue.startswith("[AC-P7]") and "Missing file" in issue)


# ===========================================================================
# 8 — smoke test: compute_scores still works
# ===========================================================================

def test_existing_compute_scores_smoke():
    """
    Regression guard: compute_scores with a perfect sheet must yield score=100.
    Mirrors the simplest assertion from test_compute_scores.py.
    """
    from compute_scores import compute_scores  # noqa: PLC0415

    answer_key = {f"q{i}": "A" for i in range(1, 21)}
    perfect_sheet = {
        "source_file": "smoke.jpg",
        "student_id": "999999",
        "answers": {k: {"value": v, "confidence": 0.99} for k, v in answer_key.items()},
        "low_confidence_questions": [],
        "unreadable": False,
    }

    result = compute_scores({"sheets": [perfect_sheet]}, answer_key, passing_score=60)

    assert result["scores"]["999999"]["correct"] == 20
    assert result["scores"]["999999"]["score"] == 100.0
    assert result["scores"]["999999"]["passed"] is True


# ===========================================================================
# Extra: extract_answers_from_key on the fixture assessment-key.md
# ===========================================================================

def test_extract_answers_from_key_fixture():
    """extract_answers_from_key should load all 20 answers from the fixture key."""
    from render_assessment import parse_yaml_frontmatter, extract_answers_from_key  # noqa: PLC0415

    text = (FIXTURE_DIR / "assessment-key.md").read_text(encoding="utf-8")
    fm, body = parse_yaml_frontmatter(text)

    answers = extract_answers_from_key(fm, body)

    assert len(answers) == 20, f"Expected 20 answers, got {len(answers)}: {answers}"
    # Spot checks (fixture has Q01: B, Q02: C, Q03: B)
    assert answers.get("q01") == "B" or answers.get("q1") == "B", (
        f"Q01 answer should be B, got: {answers}"
    )
    assert answers.get("q02") == "C" or answers.get("q2") == "C"
    assert answers.get("q03") == "B" or answers.get("q3") == "B"


# ===========================================================================
# xelatex-gated test placeholder (documents the skip pattern)
# ===========================================================================

@pytest.mark.skipif(
    shutil.which("xelatex") is None,
    reason="xelatex not installed — skipping compile test",
)
def test_run_xelatex_requires_xelatex():
    """
    Placeholder: if xelatex IS installed this test verifies run_xelatex
    raises RuntimeError on an invalid .tex file, not FileNotFoundError.
    """
    import tempfile  # noqa: PLC0415
    from render_assessment import run_xelatex  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        bad_tex = Path(tmpdir) / "bad.tex"
        bad_tex.write_text(r"\documentclass{article}\begin{broken}", encoding="utf-8")
        with pytest.raises(RuntimeError):
            run_xelatex(bad_tex, Path(tmpdir))

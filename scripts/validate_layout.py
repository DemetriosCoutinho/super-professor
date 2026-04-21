"""
validate_layout.py — Post-render QA checks on the generated assessment PDFs.

Checks implemented:
    AC-P2  prova.pdf exists
    AC-P3  answer-sheet.pdf exists
    AC-P4  assessment-duplex.pdf exists
    AC-P7  prova.html + answer-sheet.html both exist
    AC-P5  build.log exists and contains no hard LaTeX errors ('! ' lines)
    Q-CNT  All 20 question markers appear in prova.pdf text
    FILL   Last page of prova.pdf is not suspiciously sparse (soft check)

Usage (standalone):
    python3 scripts/validate_layout.py assessments/<slug>/

Importable:
    from validate_layout import validate
    issues = validate("assessments/my-slug/", allow_whitespace=False)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _extract_text_pdftotext(pdf_path: Path) -> str | None:
    """
    Extract all text from a PDF using pdftotext (poppler).
    Returns None if pdftotext is not available.
    """
    if shutil.which("pdftotext") is None:
        return None
    try:
        proc = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            return proc.stdout
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _extract_text_pypdf(pdf_path: Path) -> str | None:
    """
    Extract all text from a PDF using pypdf (pure Python).
    Returns None if pypdf is not installed.
    """
    try:
        import pypdf  # noqa: PLC0415
    except ImportError:
        try:
            import PyPDF2 as pypdf  # type: ignore[no-redef]  # noqa: PLC0415
        except ImportError:
            return None

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception:
                pages_text.append("")
        return "\n".join(pages_text)
    except Exception:
        return None


def _extract_text(pdf_path: Path) -> str:
    """
    Try pdftotext first, fall back to pypdf.
    Returns empty string if neither is available.
    """
    text = _extract_text_pdftotext(pdf_path)
    if text is not None:
        return text
    text = _extract_text_pypdf(pdf_path)
    if text is not None:
        return text
    return ""


def _extract_page_texts_pypdf(pdf_path: Path) -> list[str]:
    """
    Return per-page text list using pypdf.
    Returns empty list if pypdf is unavailable.
    """
    try:
        import pypdf  # noqa: PLC0415
    except ImportError:
        try:
            import PyPDF2 as pypdf  # type: ignore[no-redef]  # noqa: PLC0415
        except ImportError:
            return []

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return pages
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_file_exists(out_dir: Path, filename: str, check_id: str) -> str | None:
    """Return an issue string if the file is missing, else None."""
    path = out_dir / filename
    if not path.exists():
        return f"[{check_id}] Missing file: {filename}"
    return None


def _check_build_log(out_dir: Path) -> list[str]:
    """
    AC-P5: build.log exists and contains no hard LaTeX errors.
    Returns list of issues.
    """
    issues = []
    log_path = out_dir / "build.log"

    if not log_path.exists():
        return ["[AC-P5] build.log not found in output directory"]

    content = log_path.read_text(encoding="utf-8", errors="replace")
    hard_errors = [line for line in content.splitlines() if line.startswith("! ")]
    if hard_errors:
        sample = "; ".join(hard_errors[:3])
        issues.append(f"[AC-P5] Hard LaTeX errors in build.log: {sample}")
    return issues


def _check_question_count(out_dir: Path, expected: int = 20) -> list[str]:
    """
    Q-CNT: Check that question markers 1–N appear in prova.pdf text.
    Returns list of issues listing which question numbers are missing.
    """
    issues = []
    pdf_path = out_dir / "prova.pdf"
    if not pdf_path.exists():
        return []  # AC-P2 handles the missing-file case

    text = _extract_text(pdf_path)
    if not text:
        issues.append(
            "[Q-CNT] Could not extract text from prova.pdf "
            "(install pdftotext or pypdf for this check)"
        )
        return issues

    missing = []
    for n in range(1, expected + 1):
        # Match "Questão N" or "Quest..." followed by the number
        patterns = [
            f"Questão {n}",
            f"Questao {n}",
            f"Quest\\xe3o {n}",
            f"Quest {n}",
        ]
        found = any(p in text for p in patterns)
        if not found:
            # Also try regex for any "Quest..." + number
            found = bool(re.search(rf"\bQuest\w*\s+{n}\b", text))
        if not found:
            missing.append(str(n))

    if missing:
        issues.append(f"[Q-CNT] Missing question markers in prova.pdf: {', '.join(missing)}")
    return issues


def _check_fill_rate(out_dir: Path) -> list[str]:
    """
    FILL: Soft check — last page of prova.pdf should not be nearly empty.
    Uses pypdf for per-page text. Warns if last page < 20% of average char count.
    """
    issues = []
    pdf_path = out_dir / "prova.pdf"
    if not pdf_path.exists():
        return []

    pages = _extract_page_texts_pypdf(pdf_path)
    if len(pages) < 2:
        return []  # Single-page doc or could not extract — skip

    char_counts = [len(p.strip()) for p in pages]
    avg = sum(char_counts[:-1]) / max(len(char_counts) - 1, 1)
    last = char_counts[-1]

    if avg > 0 and last < avg * 0.20:
        issues.append(
            f"[FILL] Last page of prova.pdf appears nearly empty "
            f"({last} chars vs avg {avg:.0f} chars). "
            "Re-run with --allow-whitespace to suppress this check."
        )
    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(out_dir: str, allow_whitespace: bool = False) -> list[str]:
    """
    Run all post-render QA checks on the output directory.

    Args:
        out_dir: Path to the assessment output directory.
        allow_whitespace: If True, skip the fill-rate (FILL) check.

    Returns:
        List of issue strings. Empty list means all checks passed.
    """
    issues: list[str] = []
    out_path = Path(out_dir)

    if not out_path.exists() or not out_path.is_dir():
        return [f"Output directory does not exist: {out_dir}"]

    # AC-P2: prova.pdf
    issue = _check_file_exists(out_path, "prova.pdf", "AC-P2")
    if issue:
        issues.append(issue)

    # AC-P3: answer-sheet.pdf
    issue = _check_file_exists(out_path, "answer-sheet.pdf", "AC-P3")
    if issue:
        issues.append(issue)

    # AC-P4: assessment-duplex.pdf
    issue = _check_file_exists(out_path, "assessment-duplex.pdf", "AC-P4")
    if issue:
        issues.append(issue)

    # AC-P7: HTML previews
    issue = _check_file_exists(out_path, "prova.html", "AC-P7")
    if issue:
        issues.append(issue)
    issue = _check_file_exists(out_path, "answer-sheet.html", "AC-P7")
    if issue:
        issues.append(issue)

    # AC-P5: build.log + hard error check
    issues.extend(_check_build_log(out_path))

    # Q-CNT: question count
    issues.extend(_check_question_count(out_path))

    # FILL: fill rate (soft, skippable)
    if not allow_whitespace:
        issues.extend(_check_fill_rate(out_path))

    return issues


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <out_dir> [--allow-whitespace]")
        sys.exit(1)

    out_dir = sys.argv[1]
    allow_whitespace = "--allow-whitespace" in sys.argv

    issues = validate(out_dir, allow_whitespace=allow_whitespace)
    if issues:
        print("ISSUES:")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(2)
    else:
        print("OK")
        sys.exit(0)


if __name__ == "__main__":
    main()

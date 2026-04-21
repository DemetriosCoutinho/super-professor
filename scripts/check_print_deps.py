"""
check_print_deps.py — Verify print/PDF build dependencies for assessment-create.

Checks for: xelatex, pygmentize, qpdf
Detects platform and emits a JSON report to stdout.
Exit code is always 0 (report only, never installs).

Usage:
    python3 scripts/check_print_deps.py

Importable:
    from scripts.check_print_deps import check_deps
    result = check_deps()
"""

import json
import platform
import shutil
import subprocess
import sys


REQUIRED_EXECUTABLES = ["xelatex", "pygmentize", "qpdf"]

INSTALL_PLAN = {
    "macos": (
        "brew install --cask mactex-no-gui && brew install qpdf pygments"
    ),
    "debian": (
        "apt install texlive-xetex texlive-latex-extra texlive-science "
        "python3-pygments qpdf"
    ),
    "fedora": (
        "dnf install texlive-scheme-medium python3-pygments qpdf"
    ),
}

NOTE = (
    "minted package requires xelatex to be called with -shell-escape flag "
    "at compile time"
)


def _detect_platform() -> str:
    """Return one of: macos, debian, fedora, unknown."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "linux":
        # Try to read /etc/os-release for distro detection
        try:
            with open("/etc/os-release") as fh:
                content = fh.read().lower()
            if "debian" in content or "ubuntu" in content:
                return "debian"
            if "fedora" in content or "rhel" in content or "centos" in content:
                return "fedora"
        except OSError:
            pass
    return "unknown"


def _check_executable(name: str) -> bool:
    """Return True if the executable is findable on PATH."""
    return shutil.which(name) is not None


def check_deps() -> dict:
    """
    Check for required print/PDF build dependencies.

    Returns a dict with keys:
        platform, found, missing, all_found, install_plan, note
    """
    detected_platform = _detect_platform()

    found = []
    missing = []

    for exe in REQUIRED_EXECUTABLES:
        if _check_executable(exe):
            found.append(exe)
        else:
            missing.append(exe)

    # xelatex: also confirm it responds to --version (validates it's a real
    # xelatex binary, not a stub).  shell-escape support is a compile-time
    # flag and cannot be verified via --version.
    if "xelatex" in found:
        try:
            subprocess.run(
                ["xelatex", "--version"],
                capture_output=True,
                timeout=10,
                check=False,
            )
            # If the subprocess runs without FileNotFoundError, xelatex is OK.
        except (OSError, subprocess.TimeoutExpired):
            # Move xelatex from found → missing if it cannot actually run
            found.remove("xelatex")
            missing.append("xelatex")

    return {
        "platform": detected_platform,
        "found": found,
        "missing": missing,
        "all_found": len(missing) == 0,
        "install_plan": INSTALL_PLAN,
        "note": NOTE,
    }


def main() -> None:
    result = check_deps()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
    sys.exit(0)

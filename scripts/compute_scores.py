import json
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_manifest_answers(manifest_text: str) -> tuple[dict, int]:
    """Parse answer key and passing score from manifest markdown text.
    Returns (answer_key dict with lowercase q-keys, passing_score int).
    """
    answer_key = {}
    passing_score = 60

    for line in manifest_text.splitlines():
        m = re.match(r"\s*-\s*Q(\d+):\s*([ABCD])", line)
        if m:
            answer_key[f"q{m.group(1)}"] = m.group(2)
        ps = re.match(r"passing_score:\s*(\d+)", line.strip())
        if ps:
            passing_score = int(ps.group(1))

    return answer_key, passing_score


def compute_scores(raw_omr: dict, answer_key: dict, passing_score: int = 60) -> dict:
    """Compare OMR detections to answer key. Returns structured result dict."""
    scores = {}
    unmatched = []
    unreadable = []

    for sheet in raw_omr["sheets"]:
        if sheet.get("unreadable"):
            unreadable.append(sheet["source_file"])
            continue

        student_id = sheet.get("student_id")
        if not student_id:
            unmatched.append(sheet["source_file"])
            continue

        total = len(answer_key)
        correct = sum(
            1
            for q, expected in answer_key.items()
            if sheet["answers"].get(q, {}).get("value") == expected
        )
        score = round(correct / total * 100, 1) if total > 0 else 0.0

        scores[student_id] = {
            "correct": correct,
            "total": total,
            "score": score,
            "passed": score >= passing_score,
            "source_file": sheet["source_file"],
        }

    return {"scores": scores, "unmatched": unmatched, "unreadable": unreadable}


def build_grade_report(slug: str, scores: dict, unmatched: list, unreadable: list) -> str:
    """Build a markdown grade report string."""
    lines = [
        f"# Relatório de Notas — {slug}",
        f"\nGerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "\n## Resultados\n",
        "| Matrícula | Acertos | Total | Nota | Situação |",
        "|-----------|---------|-------|------|----------|",
    ]
    approved = 0
    for sid, data in sorted(scores.items()):
        situation = "Aprovado" if data["passed"] else "Reprovado"
        if data["passed"]:
            approved += 1
        lines.append(
            f"| {sid} | {data['correct']} | {data['total']} | {data['score']} | {situation} |"
        )

    lines.append(f"\n**Aprovados: {approved} / {len(scores)}**")

    if unmatched:
        lines.append("\n## Sem matrícula identificada\n")
        for f in unmatched:
            lines.append(f"- {f}")

    if unreadable:
        lines.append("\n## Folhas ilegíveis\n")
        for f in unreadable:
            lines.append(f"- {f}")

    return "\n".join(lines)


def main():
    """CLI: compute_scores.py <raw-omr.json> <assessment-manifest.md> <output-dir>"""
    if len(sys.argv) != 4:
        print("Usage: compute_scores.py <raw-omr.json> <manifest.md> <output-dir>")
        sys.exit(1)

    raw_omr_path = Path(sys.argv[1])
    manifest_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    raw_omr = json.loads(raw_omr_path.read_text())
    manifest_text = manifest_path.read_text()
    answer_key, passing_score = parse_manifest_answers(manifest_text)

    slug = output_dir.parent.name
    result = compute_scores(raw_omr, answer_key, passing_score)
    result["assessment_slug"] = slug
    result["generated_at"] = datetime.now().isoformat()

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scores.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    report = build_grade_report(slug, result["scores"], result["unmatched"], result["unreadable"])
    (output_dir / "grade-report.md").write_text(report)

    print(f"Scores: {len(result['scores'])} alunos")
    print(f"Sem matrícula: {len(result['unmatched'])}")
    print(f"Ilegíveis: {len(result['unreadable'])}")


if __name__ == "__main__":
    main()

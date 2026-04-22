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
        # Formato lista: "- Q1: A" ou "| Q1: A"
        m = re.match(r"[\s|*-]*Q(\d+):\s*([ABCD])\b", line)
        if m:
            answer_key[f"q{m.group(1)}"] = m.group(2)
        # Formato tabela markdown: "| Q1   | Q01   | Obj1 | fácil   | A    |"
        # A resposta é a ÚLTIMA coluna preenchida com A-D
        tm = re.match(r"\|\s*Q(\d+)\s*\|(?:[^|]+\|){2,}\s*([ABCD])\s*\|", line)
        if tm and f"q{tm.group(1)}" not in answer_key:
            answer_key[f"q{tm.group(1)}"] = tm.group(2)
        ps = re.match(r"passing_score:\s*(\d+)", line.strip())
        if ps:
            passing_score = int(ps.group(1))

    return answer_key, passing_score


def _answer_value(ans) -> str | None:
    """Extrai o valor da resposta suportando schema v1 (dict) e legado (string)."""
    if ans is None:
        return None
    if isinstance(ans, dict):
        return ans.get("value")
    return ans  # legado: string simples


def compute_scores(raw_omr: dict, answer_key: dict, passing_score: int = 60) -> dict:
    """Compare OMR detections to answer key. Returns structured result dict."""
    scores = {}
    unmatched_scores = {}
    unmatched = []
    unreadable = []

    for sheet in raw_omr["sheets"]:
        if sheet.get("unreadable"):
            unreadable.append(sheet["source_file"])
            continue

        student_id = sheet.get("student_id")

        total = len(answer_key)
        correct = sum(
            1
            for q, expected in answer_key.items()
            if _answer_value(sheet.get("answers", {}).get(q)) == expected
        )
        score = round(correct / total * 100, 1) if total > 0 else 0.0

        if not student_id:
            # Calcula score mesmo sem matrícula; usa chave temporária
            basename = Path(sheet["source_file"]).stem
            temp_key = f"TEMP-{basename}"
            unmatched_scores[temp_key] = {
                "correct": correct,
                "total": total,
                "score": score,
                "passed": score >= passing_score,
                "source_file": sheet["source_file"],
                "id_confirmed": False,
            }
            unmatched.append(sheet["source_file"])
            continue

        scores[student_id] = {
            "correct": correct,
            "total": total,
            "score": score,
            "passed": score >= passing_score,
            "source_file": sheet["source_file"],
        }

    return {
        "scores": scores,
        "unmatched_scores": unmatched_scores,
        "unmatched": unmatched,
        "unreadable": unreadable,
    }


def build_grade_report(
    slug: str,
    scores: dict,
    unmatched: list,
    unreadable: list,
    unmatched_scores: dict | None = None,
) -> str:
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

    if unmatched_scores:
        lines.append("\n## Notas (matrícula a confirmar)\n")
        lines.append("| Chave Temp | Arquivo | Acertos | Total | Nota | Situação |")
        lines.append("|------------|---------|---------|-------|------|----------|")
        for temp_key, data in sorted(unmatched_scores.items()):
            situation = "Aprovado" if data["passed"] else "Reprovado"
            lines.append(
                f"| {temp_key} | {data['source_file']} | {data['correct']} | {data['total']} | {data['score']} | {situation} |"
            )

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

    # Determina o slug: prefere campo "slug:" no frontmatter YAML do manifest,
    # com fallback para output_dir.parent.parent.name (layout aulas/<date>/assessment/results/)
    slug = None
    for line in manifest_text.splitlines():
        m = re.match(r"^slug:\s*(.+)", line.strip())
        if m:
            slug = m.group(1).strip()
            break
    if not slug:
        slug = output_dir.parent.parent.name or output_dir.parent.name

    result = compute_scores(raw_omr, answer_key, passing_score)
    result["assessment_slug"] = slug
    result["generated_at"] = datetime.now().isoformat()
    result["passing_score"] = passing_score

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scores.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )

    report = build_grade_report(
        slug,
        result["scores"],
        result["unmatched"],
        result["unreadable"],
        result.get("unmatched_scores"),
    )
    (output_dir / "grade-report.md").write_text(report)

    print(f"Scores: {len(result['scores'])} alunos")
    print(f"Sem matrícula: {len(result['unmatched'])}")
    print(f"Ilegíveis: {len(result['unreadable'])}")


if __name__ == "__main__":
    main()

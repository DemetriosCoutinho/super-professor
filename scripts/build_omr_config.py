#!/usr/bin/env python3
"""
Gera omr-config.json a partir do gabarito de uma avaliação.

Uso:
    python3 build_omr_config.py <gabarito-v*.md> [--out omr-config.json] [--template templates/omr-template.json]

O gabarito deve ter frontmatter YAML com shuffle_map:
    shuffle_map:
      Q1:  {bank_id: Q01, correct_exam: A, ...}
      Q2:  {bank_id: Q03, correct_exam: C, ...}
      ...

O script:
1. Lê o template OMR base
2. Extrai o answerKey do shuffle_map (correct_exam de Q1..Q20 → q1..q20)
3. Escreve omr-config.json com answerKey atualizado
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_shuffle_map(gabarito_text: str) -> dict[str, str]:
    """Extrai {q1: 'A', q2: 'C', ...} do frontmatter YAML do gabarito."""
    frontmatter_match = re.search(
        r"^---\s*\n(.*?)^---", gabarito_text, re.MULTILINE | re.DOTALL
    )
    if not frontmatter_match:
        raise ValueError("Frontmatter YAML não encontrado no gabarito.")

    frontmatter = frontmatter_match.group(1)
    answer_key = {}

    # Extrai linhas do shuffle_map: "  Q1:  {bank_id: ..., correct_exam: A, ...}"
    for m in re.finditer(
        r"^\s+Q(\d+):\s+\{[^}]*correct_exam:\s*([ABCD])[^}]*\}",
        frontmatter,
        re.MULTILINE,
    ):
        q_num = int(m.group(1))
        answer = m.group(2)
        answer_key[f"q{q_num}"] = answer

    if not answer_key:
        raise ValueError(
            "Nenhuma entrada do shuffle_map encontrada. Verifique o formato do gabarito."
        )

    return answer_key


def build_omr_config(
    gabarito_path: Path, template_path: Path | None, out_path: Path
) -> None:
    gabarito_text = gabarito_path.read_text(encoding="utf-8")
    answer_key = parse_shuffle_map(gabarito_text)

    # Carrega template base ou usa configuração padrão
    if template_path and template_path.exists():
        config = json.loads(template_path.read_text())
    else:
        # Configuração padrão sem markers (CropPage) — A4 @ 300dpi
        config = {
            "description": "super-professor — gerado por build_omr_config.py",
            "pageDimensions": [2480, 3508],
            "bubbleDimensions": [38, 38],
            "preProcessors": [
                {"name": "CropPage", "options": {"morphKernel": [10, 10]}}
            ],
            "fieldBlocks": {
                "StudentID": {
                    "fieldType": "QTYPE_INT",
                    "origin": [160, 360],
                    "fieldLabels": [
                        "D1",
                        "D2",
                        "D3",
                        "D4",
                        "D5",
                        "D6",
                        "D7",
                        "D8",
                        "D9",
                        "D10",
                        "D11",
                        "D12",
                        "D13",
                        "D14",
                    ],
                    "labelsGap": 155,
                    "bubblesGap": 46,
                    "direction": "horizontal",
                    "bubbleValues": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                },
                "QLeft": {
                    "fieldType": "QTYPE_MCQ4",
                    "origin": [160, 980],
                    "fieldLabels": [
                        "q1",
                        "q2",
                        "q3",
                        "q4",
                        "q5",
                        "q6",
                        "q7",
                        "q8",
                        "q9",
                        "q10",
                    ],
                    "labelsGap": 78,
                    "bubblesGap": 56,
                    "direction": "vertical",
                    "bubbleValues": ["A", "B", "C", "D"],
                },
                "QRight": {
                    "fieldType": "QTYPE_MCQ4",
                    "origin": [1340, 980],
                    "fieldLabels": [
                        "q11",
                        "q12",
                        "q13",
                        "q14",
                        "q15",
                        "q16",
                        "q17",
                        "q18",
                        "q19",
                        "q20",
                    ],
                    "labelsGap": 78,
                    "bubblesGap": 56,
                    "direction": "vertical",
                    "bubbleValues": ["A", "B", "C", "D"],
                },
            },
        }

    # Garante fieldBlocks corretos (14 cols, MCQ4)
    if "StudentID" in config.get("fieldBlocks", {}):
        sid = config["fieldBlocks"]["StudentID"]
        sid["fieldLabels"] = [f"D{i}" for i in range(1, 15)]
        sid["bubbleValues"] = [str(i) for i in range(10)]
        # Recalcula labelsGap para 14 colunas caber em ~2100px (com margem)
        if sid.get("labelsGap", 0) > 155:
            sid["labelsGap"] = 155

    for block_name in ["QLeft", "QRight"]:
        if block_name in config.get("fieldBlocks", {}):
            block = config["fieldBlocks"][block_name]
            block["fieldType"] = "QTYPE_MCQ4"
            block["bubbleValues"] = ["A", "B", "C", "D"]

    # Remove CropOnMarkers se não há markers disponíveis (usa CropPage)
    preprocessors = config.get("preProcessors", [])
    has_crop_on_markers = any(p["name"] == "CropOnMarkers" for p in preprocessors)
    if has_crop_on_markers:
        config["preProcessors"] = [
            p for p in preprocessors if p["name"] != "CropOnMarkers"
        ]
        # Adiciona CropPage se não existir
        if not any(p["name"] == "CropPage" for p in config["preProcessors"]):
            config["preProcessors"].insert(
                0, {"name": "CropPage", "options": {"morphKernel": [10, 10]}}
            )

    # Injeta o answerKey gerado do gabarito
    config["answerKey"] = {f"q{i}": answer_key.get(f"q{i}", "?") for i in range(1, 21)}

    # Adiciona referência ao gabarito para rastreabilidade
    config["_generated_from"] = str(gabarito_path.resolve())

    out_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ omr-config.json gerado em: {out_path}")
    print(f"  answerKey: {json.dumps(config['answerKey'])}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gabarito", help="Caminho para gabarito-v*.md")
    parser.add_argument("--out", default="omr-config.json", help="Caminho de saída")
    parser.add_argument("--template", help="Template OMR base (opcional)")
    args = parser.parse_args()

    gabarito_path = Path(args.gabarito)
    if not gabarito_path.exists():
        print(f"Erro: gabarito não encontrado: {gabarito_path}", file=sys.stderr)
        sys.exit(1)

    template_path = Path(args.template) if args.template else None
    out_path = Path(args.out)

    build_omr_config(gabarito_path, template_path, out_path)


if __name__ == "__main__":
    main()

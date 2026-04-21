import json
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from compute_scores import compute_scores, parse_manifest_answers, build_grade_report


ANSWER_KEY = {
    "q1": "A", "q2": "B", "q3": "C", "q4": "D", "q5": "A",
    "q6": "B", "q7": "C", "q8": "D", "q9": "A", "q10": "B",
    "q11": "C", "q12": "D", "q13": "A", "q14": "B", "q15": "C",
    "q16": "D", "q17": "A", "q18": "B", "q19": "C", "q20": "D",
}

PERFECT_SHEET = {
    "source_file": "perfect.jpg",
    "student_id": "111111111",
    "answers": {k: {"value": v, "confidence": 0.99} for k, v in ANSWER_KEY.items()},
    "low_confidence_questions": [],
    "unreadable": False,
}

HALF_CORRECT_SHEET = {
    "source_file": "half.jpg",
    "student_id": "222222222",
    "answers": {
        k: {"value": v if i < 10 else "X", "confidence": 0.95}
        for i, (k, v) in enumerate(ANSWER_KEY.items())
    },
    "low_confidence_questions": [],
    "unreadable": False,
}

UNREADABLE_SHEET = {
    "source_file": "bad.jpg",
    "student_id": None,
    "answers": {},
    "low_confidence_questions": [],
    "unreadable": True,
}

NO_ID_SHEET = {
    "source_file": "noid.jpg",
    "student_id": None,
    "answers": {k: {"value": v, "confidence": 0.99} for k, v in ANSWER_KEY.items()},
    "low_confidence_questions": [],
    "unreadable": False,
}


def make_raw_omr(*sheets):
    return {"sheets": list(sheets)}


def test_perfect_score():
    raw = make_raw_omr(PERFECT_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert result["scores"]["111111111"]["correct"] == 20
    assert result["scores"]["111111111"]["score"] == 100.0
    assert result["scores"]["111111111"]["passed"] is True


def test_half_score():
    raw = make_raw_omr(HALF_CORRECT_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert result["scores"]["222222222"]["correct"] == 10
    assert result["scores"]["222222222"]["score"] == 50.0
    assert result["scores"]["222222222"]["passed"] is False


def test_unreadable_sheet_goes_to_unreadable_list():
    raw = make_raw_omr(UNREADABLE_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert "unreadable" in result
    assert "bad.jpg" in result["unreadable"]
    assert len(result["scores"]) == 0


def test_no_student_id_goes_to_unmatched():
    raw = make_raw_omr(NO_ID_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert "noid.jpg" in result["unmatched"]
    assert len(result["scores"]) == 0


def test_mixed_sheets():
    raw = make_raw_omr(PERFECT_SHEET, UNREADABLE_SHEET, NO_ID_SHEET)
    result = compute_scores(raw, ANSWER_KEY, passing_score=60)
    assert len(result["scores"]) == 1
    assert len(result["unreadable"]) == 1
    assert len(result["unmatched"]) == 1


def test_parse_manifest_answers():
    manifest_text = """---
title: Test
answers:
  - Q1: A
  - Q2: B
  - Q3: C
  - Q4: D
  - Q5: A
  - Q6: B
  - Q7: C
  - Q8: D
  - Q9: A
  - Q10: B
  - Q11: C
  - Q12: D
  - Q13: A
  - Q14: B
  - Q15: C
  - Q16: D
  - Q17: A
  - Q18: B
  - Q19: C
  - Q20: D
passing_score: 60
---"""
    key, passing = parse_manifest_answers(manifest_text)
    assert key["q1"] == "A"
    assert key["q20"] == "D"
    assert passing == 60


def test_build_grade_report_contains_summary():
    scores = {
        "111111111": {"correct": 20, "total": 20, "score": 100.0, "passed": True, "source_file": "f.jpg"},
        "222222222": {"correct": 10, "total": 20, "score": 50.0, "passed": False, "source_file": "g.jpg"},
    }
    report = build_grade_report("2026-04-20-calculo-p1", scores, unmatched=[], unreadable=[])
    assert "111111111" in report
    assert "100.0" in report
    assert "50.0" in report
    assert "Aprovados: 1" in report

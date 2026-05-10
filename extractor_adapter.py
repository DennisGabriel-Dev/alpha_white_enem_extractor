import json
import os
import re
import tempfile
from typing import Any

import fitz

if not hasattr(fitz, "fitz"):
    fitz.fitz = fitz

from enem_pdf_extractor import EnemPDFextractor


class ExtractorAdapterError(Exception):
    pass


class ExtractorAdapter:
    QUESTION_FILE_TO_AREA = {
        "lang_questions": "LC",
        "eng_questions": "LC",
        "spani_questions": "LC",
        "huma_questions": "CH",
        "natu_questions": "CN",
        "math_questions": "MT",
    }

    YEAR_PATTERN = re.compile(r"(20\d{2})")
    DAY_PATTERN = re.compile(r"(D[12])")
    COLOR_PATTERN = re.compile(r"(CD\d+)", re.IGNORECASE)

    def __init__(self, process_questions_with_images: bool = False) -> None:
        self.process_questions_with_images = process_questions_with_images

    def extract(self, exam_pdf_path: str, answer_key_pdf_path: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="enem_extract_") as tmp_dir:
            extractor = EnemPDFextractor(
                output_type="json",
                process_questions_with_images=self.process_questions_with_images,
            )
            extractor.extract_pdf(
                test_pdf_path=exam_pdf_path,
                answers_pdf_path=answer_key_pdf_path,
                extracted_data_path=tmp_dir,
            )

            exam = self._build_exam_metadata(exam_pdf_path)
            questions = self._read_questions(tmp_dir)

            return {"exam": exam, "questions": questions}

    def _build_exam_metadata(self, exam_pdf_path: str) -> dict[str, Any]:
        filename = os.path.basename(exam_pdf_path)
        year_match = self.YEAR_PATTERN.search(filename)
        day_match = self.DAY_PATTERN.search(filename)
        color_match = self.COLOR_PATTERN.search(filename)

        if not year_match or not day_match or not color_match:
            raise ExtractorAdapterError("Nome do arquivo fora do padrão INEP.")

        return {
            "year": int(year_match.group(1)),
            "day": day_match.group(1).upper(),
            "booklet_color": color_match.group(1).upper(),
            "metadata": {"source": "inep_pdf_extractor"},
        }

    def _read_questions(self, output_dir: str) -> list[dict[str, Any]]:
        all_questions: list[dict[str, Any]] = []

        for file_name in os.listdir(output_dir):
            if not file_name.endswith(".json"):
                continue

            area = self._area_from_file(file_name)
            if not area:
                continue

            file_path = os.path.join(output_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                raw_questions = json.load(f)

            for q in raw_questions:
                normalized = self._normalize_question(q, area)
                if normalized:
                    all_questions.append(normalized)

        all_questions.sort(key=lambda item: item["number_in_exam"])
        return all_questions

    def _area_from_file(self, file_name: str) -> str | None:
        for key, area in self.QUESTION_FILE_TO_AREA.items():
            if key in file_name:
                return area
        return None

    def _normalize_question(self, raw_question: dict[str, Any], area: str) -> dict[str, Any] | None:
        number = raw_question.get("question_num")
        statement = raw_question.get("question_text")
        correct_answer = str(raw_question.get("correct_answer", "")).strip().upper()

        if not isinstance(number, int) or number <= 0:
            return None
        if not statement:
            return None

        alternatives = raw_question.get("alternatives") or []
        if not isinstance(alternatives, list):
            alternatives = []

        correct_letter = correct_answer[:1] if correct_answer else ""
        if correct_letter not in {"A", "B", "C", "D", "E"}:
            correct_letter = "A"

        return {
            "number_in_exam": number,
            "area": area,
            "skill": None,
            "statement": statement,
            "alternatives": alternatives,
            "correct_letter": correct_letter,
        }

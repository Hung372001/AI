import json
import os
import re

import anyio
from openai import OpenAI


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _heuristic_grade(student_answer: str, answer_key: str) -> tuple[float, str]:
    if not answer_key:
        return 0.0, "Chưa có đáp án để chấm tự động."

    normalized_student = _normalize_text(student_answer)
    normalized_key = _normalize_text(answer_key)
    if normalized_student == normalized_key:
        return 1.0, "Câu trả lời trùng khớp đáp án."
    if normalized_key in normalized_student or normalized_student in normalized_key:
        return 0.5, "Câu trả lời gần đúng với đáp án."
    return 0.0, "Câu trả lời chưa khớp đáp án."


def _build_grade_prompt(question_text: str, student_answer: str, answer_key: str) -> str:
    return (
        "Bạn là giáo viên chấm bài. Hãy chấm điểm câu trả lời của học sinh.\n"
        "Yêu cầu trả về JSON duy nhất với các trường:\n"
        "- score: số thực từ 0 đến 1\n"
        "- feedback: nhận xét ngắn gọn bằng tiếng Việt\n"
        f"Câu hỏi: {question_text}\n"
        f"Đáp án tham khảo: {answer_key}\n"
        f"Trả lời của học sinh: {student_answer}\n"
    )


async def grade_answer(
    question_text: str,
    student_answer: str,
    answer_key: str | None,
) -> tuple[float, str]:
    if not answer_key:
        return 0.0, "Chưa có đáp án để chấm tự động."

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _heuristic_grade(student_answer, answer_key)

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = _build_grade_prompt(question_text, student_answer, answer_key)

    def _call():
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "system", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content

    raw = await anyio.to_thread.run_sync(_call)
    try:
        data = json.loads(raw)
        score = float(data.get("score", 0.0))
        score = max(0.0, min(score, 1.0))
        feedback = str(data.get("feedback", "")).strip()
        if not feedback:
            feedback = "Đã chấm điểm tự động."
        return score, feedback
    except (ValueError, TypeError, json.JSONDecodeError):
        return _heuristic_grade(student_answer, answer_key)
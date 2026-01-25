import json
import os
from typing import List

import anyio
from openai import OpenAI


def _build_prompt(question: str, contexts: List[str], history: List[str]) -> str:
    context_text = "\n\n".join(contexts) if contexts else "Không có ngữ cảnh tham khảo."
    history_text = "\n".join(history) if history else "Không có lịch sử hội thoại."
    return (
        "Bạn là gia sư AI. Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt.\n"
        "Nếu thiếu dữ liệu, hãy nói rõ và gợi ý học sinh cung cấp thêm thông tin.\n"
        "Trả về JSON object theo mẫu:\n"
        "{\n"
        '  "reply": "<câu trả lời>",\n'
        '  "diagram": {\n'
        '    "width": 400,\n'
        '    "height": 300,\n'
        '    "shapes": [\n'
        '      {"type": "point", "x": 100, "y": 200, "label": "A"},\n'
        '      {"type": "point", "x": 300, "y": 200, "label": "B"},\n'
        '      {"type": "line", "from": "A", "to": "B"}\n'
        "    ]\n"
        "  }\n"
        "}\n"
        "Nếu không cần hình, để diagram là null.\n"
        f"Lịch sử hội thoại gần đây:\n{history_text}\n\n"
        f"Ngữ cảnh tham khảo:\n{context_text}\n\n"
        f"Câu hỏi của học sinh: {question}"
    )


def _strip_json_fence(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1).replace("```", "", 1).strip()
    return cleaned


async def generate_reply(question: str, contexts: List[str], history: List[str]) -> dict:


    client = OpenAI(api_key="",base_url='http://localhost:11434/v1')
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = _build_prompt(question, contexts, history)

    def _call():

        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    raw = await anyio.to_thread.run_sync(_call)
    cleaned = _strip_json_fence(raw)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "reply" in data:
            return data
    except json.JSONDecodeError:
        pass
    return {"reply": raw.strip(), "diagram": None}


def _build_question_prompt(topic: str, contexts: List[str], count: int) -> str:
    context_text = "\n\n".join(contexts) if contexts else "Không có ngữ cảnh tham khảo."
    return (
        "Bạn là gia sư AI. Hãy tạo câu hỏi luyện tập dựa trên ngữ cảnh.\n"
        f"Chủ đề: {topic}\n"
        f"Ngữ cảnh:\n{context_text}\n\n"
        "Yêu cầu: Trả về JSON array, mỗi phần tử có các trường:\n"
        "- question_text (string)\n"
        "- answer_key (string, đáp án ngắn gọn)\n"
        "- hint (string, optional)\n"
        f"Số lượng câu hỏi: {count}\n"
    )


async def generate_questions(topic: str, contexts: List[str], count: int) -> List[dict]:


    client = OpenAI(api_key="",base_url='http://localhost:11434/v1')
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = _build_question_prompt(topic, contexts, count)

    def _call():
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    raw = await anyio.to_thread.run_sync(_call)
    cleaned = _strip_json_fence(raw)
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    questions: List[dict] = []
    for line in cleaned.splitlines():
        line = line.strip("- ").strip()
        if line:
            questions.append({"question_text": line})
    return questions
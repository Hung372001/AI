import json
import os
from typing import List

import anyio
from openai import OpenAI


def _build_prompt(question: str, contexts: List[str]) -> str:
    context_text = "\n\n".join(contexts) if contexts else "Không có ngữ cảnh tham khảo."
    return (
        "Bạn là gia sư AI. Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt.\n"
        "Nếu thiếu dữ liệu, hãy nói rõ và gợi ý học sinh cung cấp thêm thông tin.\n"
        f"Ngữ cảnh tham khảo:\n{context_text}\n\n"
        f"Câu hỏi của học sinh: {question}"
    )


async def generate_reply(question: str, contexts: List[str]) -> str:

    client = OpenAI(

        base_url="http://localhost:11434/v1",
            api_key=''
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = _build_prompt(question, contexts)

    def _call():
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    return await anyio.to_thread.run_sync(_call)


def _build_question_prompt(topic: str, contexts: List[str], count: int) -> str:
    context_text = "\n\n".join(contexts) if contexts else "Không có ngữ cảnh tham khảo."
    return (
        "Bạn là gia sư AI. Hãy tạo câu hỏi luyện tập dựa trên ngữ cảnh.\n"
        f"Chủ đề: {topic}\n"
        f"Ngữ cảnh:\n{context_text}\n\n"
        "Yêu cầu: Trả về JSON array, mỗi phần tử có các trường:\n"
        "- question_text (string)\n"
        "- hint (string, optional)\n"
        f"Số lượng câu hỏi: {count}\n"
    )


async def generate_questions(topic: str, contexts: List[str], count: int) -> List[dict]:
    api_key = os.getenv("OPENAI_API_KEY")


    client = OpenAI(api_key=api_key)
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
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    questions: List[dict] = []
    for line in raw.splitlines():
        line = line.strip("- ").strip()
        if line:
            questions.append({"question_text": line})
    return questions

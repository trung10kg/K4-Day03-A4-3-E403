"""
Level 2: LLM chatbot baseline.

The chatbot can answer naturally, but it cannot call tools or verify the
current course catalog.
"""

CHATBOT_BASELINE_PROMPT = """Bạn là chatbot tư vấn học phần cho sinh viên.
Trả lời thân thiện dựa trên kiến thức chung.
Nếu câu hỏi cần dữ liệu cụ thể như lớp còn chỗ hoặc điều kiện tiên quyết chính thức,
hãy nói rõ rằng bạn không có công cụ để kiểm chứng.
"""


def llm_chatbot(user_input: str) -> str:
    text = user_input.casefold()
    if any(word in text for word in ("còn chỗ", "lớp", "tiên quyết", "điều kiện")):
        return (
            "[LLM Chatbot]: Tôi có thể giải thích khái niệm chung, nhưng không có tool "
            "để tra cứu dữ liệu học phần chính xác ở thời điểm hiện tại."
        )
    return f"[LLM Chatbot]: Tôi có thể tư vấn chung cho câu hỏi: '{user_input}'."


if __name__ == "__main__":
    print("=== DEMO LEVEL 2: LLM CHATBOT BASELINE ===")
    question = "DS201 học kỳ này còn lớp nào trống không?"
    print(f"User: {question}")
    print(f"Bot : {llm_chatbot(question)}")

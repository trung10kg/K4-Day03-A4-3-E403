"""
Level 1: Rule-based bot.

This bot only matches fixed keywords. It is useful as a simple baseline that
shows why tool use is needed for course advising.
"""


def rule_based_bot(user_input: str) -> str:
    text = user_input.casefold()
    if any(word in text for word in ("chào", "hello", "hi")):
        return "Xin chào! Tôi là bot luật cố định hỗ trợ tư vấn học phần cơ bản."
    if "học phần" in text or "môn" in text:
        return "Bạn có thể hỏi về học phần dữ liệu, SQL, học máy hoặc điều kiện tiên quyết."
    if "tiên quyết" in text or "điều kiện" in text:
        return "Một số môn nâng cao yêu cầu hoàn thành môn nền tảng trước khi đăng ký."
    if "còn chỗ" in text or "lớp" in text:
        return "Tôi không tra cứu được số chỗ theo thời gian thực vì chỉ là rule-based bot."
    return "Xin lỗi, câu hỏi này nằm ngoài các keyword đã được cài đặt sẵn."


if __name__ == "__main__":
    print("=== DEMO LEVEL 1: RULE-BASED BOT ===")
    test_queries = [
        "Chào bạn",
        "Tôi muốn tìm học phần về dữ liệu",
        "DS201 còn chỗ không?",
    ]
    for query in test_queries:
        print(f"User: {query}")
        print(f"Bot : {rule_based_bot(query)}\n")

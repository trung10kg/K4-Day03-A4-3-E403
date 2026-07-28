"""Multi-provider LLM adapter with a detailed offline MockProvider."""

from __future__ import annotations

import os
import re
import sys
import unicodedata

import requests
from dotenv import load_dotenv


if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


class BaseLLMProvider:
    """Base interface for all LLM providers."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env."
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text or ""
        except Exception as exc:
            return f"[Gemini Exception]: {exc}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env."
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as exc:
            return f"[OpenAI Exception]: {exc}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env."
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as exc:
            return f"[Anthropic Exception]: {exc}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env."
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={"model": self.model_name, "messages": messages},
                timeout=30,
            )
            if response.status_code != 200:
                return f"[OpenRouter API Error {response.status_code}]: {response.text}"
            return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            return f"[OpenRouter Exception]: {exc}"


class MockProvider(BaseLLMProvider):
    """Offline provider that produces complete, deterministic course-advising answers."""

    model_name = "offline-mock"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        question = _question_from_prompt(prompt)
        normalized_question = _normalize(question)

        if "baseline" in _normalize(system_prompt):
            return _baseline_answer(normalized_question)

        if _is_policy_violation(normalized_question):
            return (
                "Thought: Yêu cầu này vi phạm quy định học vụ nên không cần gọi tool.\n"
                "Final Answer: Mình không thể hỗ trợ bỏ qua môn tiên quyết hoặc tự ý sửa kết quả học tập. "
                "Bạn nên hoàn thành học phần tiên quyết, hoặc liên hệ cố vấn học tập/phòng đào tạo "
                "để được hướng dẫn phương án hợp lệ."
            )

        observation = _last_observation(prompt)
        if observation is not None:
            return self._after_observation(question, observation, prompt)

        if "xyz999" in normalized_question:
            return (
                "Thought: Cần tra đúng mã học phần mà sinh viên cung cấp.\n"
                'Action: search_course_sections["XYZ999", "Học kỳ 1 2026-2027"]'
            )

        if _needs_prerequisite_check(normalized_question):
            completed = "Nhập môn lập trình, Xác suất thống kê"
            target = "Phân tích dữ liệu" if "phan tich du lieu" in normalized_question else "ML301"
            return (
                "Thought: Cần kiểm tra điều kiện tiên quyết trước khi tư vấn đăng ký.\n"
                f'Action: check_prerequisites["{completed}", "{target}"]'
            )

        if _needs_section_search(normalized_question):
            course = "ML301" if "ml301" in normalized_question or "hoc may" in normalized_question else "DS201"
            return (
                "Thought: Cần tra lớp học phần và số chỗ còn lại.\n"
                f'Action: search_course_sections["{course}", "Học kỳ 1 2026-2027"]'
            )

        if "tin chi" in normalized_question:
            return (
                "Thought: Câu hỏi chỉ cần tư vấn chung, không cần tool.\n"
                "Final Answer: Tín chỉ phản ánh khối lượng học tập của một học phần, gồm thời gian học trên lớp và tự học. "
                "Với sinh viên năm nhất, bạn nên bắt đầu bằng khối lượng vừa sức, cân bằng môn nền tảng và thời gian tự học; "
                "sau đó điều chỉnh theo kết quả học kỳ đầu. Hãy đối chiếu giới hạn tín chỉ và quy định rút/đăng ký môn của trường trước khi chốt lịch."
            )

        if _is_data_skills_question(normalized_question):
            return (
                "Thought: Câu hỏi cần tư vấn kỹ năng chung, không cần tool.\n"
                "Final Answer: Nếu theo hướng phân tích dữ liệu, bạn nên xây nền tảng theo bốn nhóm: "
                "(1) lập trình với Python và SQL; (2) xác suất thống kê và trực quan hóa dữ liệu; "
                "(3) tư duy đặt câu hỏi, làm sạch và diễn giải dữ liệu; (4) giao tiếp, tiếng Anh và trình bày insight. "
                "Bạn có thể bắt đầu bằng một dự án nhỏ dùng dữ liệu công khai, ghi lại quy trình và nhận phản hồi để xây portfolio."
            )

        if any(word in normalized_question for word in ("hoc phan", "sql", "du lieu", "data")):
            keyword = "SQL" if "sql" in normalized_question else "dữ liệu"
            return f'Thought: Cần tìm học phần phù hợp với định hướng của sinh viên.\nAction: search_courses["{keyword}"]'

        return (
            "Thought: Câu hỏi chỉ cần tư vấn chung, không cần tool.\n"
            "Final Answer: Mình có thể hỗ trợ bạn xây lộ trình học theo mục tiêu. Bạn hãy cho mình biết ngành học, "
            "học phần đã hoàn thành và định hướng mong muốn để nhận gợi ý cụ thể hơn."
        )

    def _after_observation(self, question: str, observation: str, prompt: str) -> str:
        normalized_question = _normalize(question)
        normalized_observation = _normalize(observation)

        if _is_tool_error(normalized_observation):
            return (
                "Thought: Tool không có dữ liệu hợp lệ nên không nên tra cứu lặp lại.\n"
                "Final Answer: Mình chưa tìm thấy dữ liệu phù hợp với thông tin bạn cung cấp. "
                "Bạn hãy kiểm tra lại mã hoặc tên học phần, đồng thời xác nhận học kỳ cần tra cứu; "
                "sau đó mình sẽ hỗ trợ bạn tiếp tục."
            )

        if _needs_prerequisite_check(normalized_question) and _needs_section_search(normalized_question):
            if "chua du dieu kien" in normalized_observation:
                return (
                    "Thought: Sinh viên chưa đủ điều kiện nên không cần tra lớp ở bước này.\n"
                    "Final Answer: Bạn chưa đủ điều kiện đăng ký học phần mục tiêu. Hãy hoàn thành các môn tiên quyết "
                    "được nêu trong kết quả trước, rồi kiểm tra lại lớp mở ở học kỳ phù hợp."
                )
            if "search_course_sections" not in prompt:
                return (
                    "Thought: Sinh viên đã đủ điều kiện; cần tra tiếp lớp còn chỗ trước khi kết luận.\n"
                    'Action: search_course_sections["Phân tích dữ liệu", "Học kỳ 1 2026-2027"]'
                )

        return "Thought: Tôi đã có đủ thông tin để trả lời.\nFinal Answer: " + _detailed_answer(
            normalized_question, observation
        )


def _baseline_answer(question: str) -> str:
    if "tin chi" in question:
        return (
            "Tín chỉ phản ánh khối lượng học tập của một học phần. Bạn nên đăng ký khối lượng vừa sức, "
            "cân bằng môn bắt buộc với thời gian tự học và đối chiếu quy định của trường trước khi chốt lịch."
        )
    if _is_data_skills_question(question):
        return (
            "Để theo hướng phân tích dữ liệu, bạn nên rèn Python/SQL, xác suất thống kê, tư duy phân tích, "
            "trực quan hóa dữ liệu, giao tiếp và tự học qua dự án nhỏ."
        )
    return (
        "Mình có thể tư vấn chung, nhưng chatbot baseline không có tool để xác thực danh mục học phần, "
        "điều kiện tiên quyết, lịch lớp hoặc số chỗ còn lại. Hãy dùng ReAct Agent cho yêu cầu tra cứu học vụ."
    )


def _detailed_answer(question: str, observation: str) -> str:
    normalized_observation = _normalize(observation)
    if "cac hoc phan phu hop" in normalized_observation:
        return (
            "Dưới đây là các học phần phù hợp từ dữ liệu hiện có:\n"
            f"{observation}\n\n"
            "Gợi ý lộ trình: ưu tiên các môn nền tảng trước; chỉ đăng ký môn có điều kiện tiên quyết khi bạn đã hoàn thành các môn đó."
        )
    if "lop ds201" in normalized_observation or "lop db202" in normalized_observation or "lop ml301" in normalized_observation:
        return (
            "Bạn đã có thông tin lớp học phần:\n"
            f"{observation}\n\n"
            "Khuyến nghị: ưu tiên lớp còn chỗ, kiểm tra trùng lịch với các môn khác, rồi xác nhận lại trên cổng học vụ trước khi đăng ký."
        )
    if "du dieu kien hoc" in normalized_observation:
        return (
            f"Kết quả kiểm tra: {observation}\n\n"
            "Bạn có thể tiếp tục xem các lớp đang mở và số chỗ còn lại trước khi đưa ra quyết định đăng ký."
        )
    return f"Kết quả tra cứu: {observation}\n\nBạn nên dùng thông tin này cùng kế hoạch học tập cá nhân để chọn phương án phù hợp."


def _question_from_prompt(prompt: str) -> str:
    match = re.search(r"User Question:\s*(.*?)(?:\n\nTrace|$)", prompt, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else prompt.strip()


def _last_observation(prompt: str) -> str | None:
    matches = re.findall(r"Observation:\s*(.+?)(?=\n(?:Thought:|Action:|Final Answer:|Observation:)|$)", prompt, flags=re.DOTALL | re.IGNORECASE)
    return matches[-1].strip() if matches else None


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFD", str(value).casefold())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("đ", "d")


def _is_policy_violation(question: str) -> bool:
    return any(phrase in question for phrase in ("ghi de", "sua diem", "ket qua hoc tap", "tu y")) or (
        "dang ky" in question and "chua hoc mon tien quyet" in question
    )


def _needs_prerequisite_check(question: str) -> bool:
    return any(phrase in question for phrase in ("tien quyet", "du dieu kien", "dieu kien hoc"))


def _needs_section_search(question: str) -> bool:
    return any(phrase in question for phrase in ("con cho", "lop nao", "lop mo", "lich hoc", "tra cac lop"))


def _is_data_skills_question(question: str) -> bool:
    return ("phan tich du lieu" in question or "data analytics" in question) and any(
        word in question for word in ("ky nang", "ren", "nam nhat", "xay dung")
    )


def _is_tool_error(observation: str) -> bool:
    return observation.startswith("loi:") or "khong tim thay" in observation


def get_llm_provider(provider_name: str | None = None) -> BaseLLMProvider:
    """Create a provider from LLM_PROVIDER."""

    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    if name == "gemini":
        return GeminiProvider()
    if name == "openai":
        return OpenAIProvider()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "openrouter":
        return OpenRouterProvider()
    return MockProvider()


if __name__ == "__main__":
    provider = MockProvider()
    print(provider.generate("User Question: Hãy tìm các học phần về SQL"))

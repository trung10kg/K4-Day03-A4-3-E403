"""
Multi-provider LLM adapter.

Set LLM_PROVIDER in .env to one of: mock, gemini, openai, anthropic, openrouter.
The mock provider lets the lab run offline without API keys.
"""

import os
import re
import sys

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
    """Anthropic Claude provider."""

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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            payload = {"model": self.model_name, "messages": messages}
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if res.status_code != 200:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
            return res.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            return f"[OpenRouter Exception]: {exc}"


class MockProvider(BaseLLMProvider):
    """Offline mock provider with deterministic ReAct traces for lab demos."""

    model_name = "offline-mock"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = _normalize(prompt)
        system_text = _normalize(system_prompt)

        if "khong co quyen tra cuu" in system_text or "baseline" in system_text:
            if any(word in text for word in ("con cho", "lop", "tien quyet", "dieu kien", "hoc phan")):
                return (
                    "Tôi có thể tư vấn chung, nhưng baseline chatbot không có tool "
                    "để kiểm chứng dữ liệu học phần, điều kiện tiên quyết hoặc lớp còn chỗ."
                )
            return (
                "Để học tốt lập trình, bạn nên luyện code đều đặn, nắm chắc tư duy giải thuật, "
                "đọc lỗi cẩn thận và làm nhiều bài tập nhỏ trước khi chuyển sang dự án lớn."
            )

        if "observation:" in text:
            observation = _last_observation(prompt)
            return (
                "Thought: Tôi đã có đủ thông tin để trả lời.\n"
                f"Final Answer: Dựa trên kết quả tra cứu: {observation}"
            )

        if "thoi tiet" in text and "ha noi" in text and "chuyen bay" not in text:
            return 'Thought: Cần tra cứu thời tiết Hà Nội.\nAction: get_weather["Hà Nội"]'

        if "chuyen bay" in text or "ve may bay" in text:
            return 'Thought: Cần tra cứu chuyến bay trước.\nAction: search_flights["TP.HCM", "Hà Nội"]'

        if "magic999" in text:
            return (
                "Thought: Cần kiểm tra học phần người dùng nêu thay vì tự suy đoán.\n"
                'Action: search_course_sections["MAGIC999", "Học kỳ 1 2026-2027"]'
            )

        if any(word in text for word in ("tien quyet", "du dieu kien", "dieu kien")):
            completed = "Nhập môn lập trình, Xác suất thống kê"
            if "cs101" in text and "ma201" not in text:
                completed = "Nhập môn lập trình"
            target = "DS201" if "ds201" in text or "phan tich du lieu" in text else "ML301"
            return (
                "Thought: Cần kiểm tra điều kiện tiên quyết bằng tool.\n"
                f'Action: check_prerequisites["{completed}", "{target}"]'
            )

        if any(word in text for word in ("con cho", "lop", "lich hoc", "mo lop")):
            course = "ML301" if "ml301" in text or "hoc may" in text else "DS201"
            return (
                "Thought: Cần tra cứu lớp học phần và số chỗ còn lại.\n"
                f'Action: search_course_sections["{course}", "Học kỳ 1 2026-2027"]'
            )

        if "lap trinh" in text and "hoc tot" in text:
            return (
                "Thought: Câu hỏi này chỉ cần lời khuyên học tập chung.\n"
                "Final Answer: Bạn nên luyện code đều đặn, học chắc biến/hàm/vòng lặp, "
                "tự debug lỗi, ghi chú pattern thường gặp và làm dự án nhỏ để biến kiến thức thành kỹ năng."
            )

        if any(word in text for word in ("hoc phan", "mon", "sql", "du lieu", "data")):
            keyword = "SQL" if "sql" in text else "dữ liệu"
            return f'Thought: Cần tìm học phần phù hợp.\nAction: search_courses["{keyword}"]'

        return (
            "Tôi có thể trả lời chung, nhưng nếu cần dữ liệu học phần cụ thể "
            "hãy hỏi về tìm học phần, điều kiện tiên quyết hoặc lớp còn chỗ."
        )


def _normalize(value: str) -> str:
    import unicodedata

    text = unicodedata.normalize("NFD", str(value).casefold())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("đ", "d")


def _last_observation(prompt: str) -> str:
    matches = re.findall(r"Observation:\s*(.+)", prompt, flags=re.IGNORECASE | re.DOTALL)
    return matches[-1].strip() if matches else "không có observation."


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
    provider = get_llm_provider()
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    print(f"Provider: {provider.__class__.__name__}")
    print(provider.generate("Tìm học phần về SQL"))

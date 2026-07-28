"""
Core app that connects tools, prompts, test cases and the LLM provider.
"""

import ast
import json
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT
from providers import MockProvider, get_llm_provider
from tools import AVAILABLE_TOOLS

load_dotenv()


def load_test_cases() -> list[dict[str, Any]]:
    """Load Role 1 test cases from config/test_cases.json."""

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """Run the no-tool chatbot baseline."""

    print(f"\n[CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = _generate_with_fallback(provider, user_query, CHATBOT_BASELINE_PROMPT)
    print(f"Chatbot trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider) -> str:
    """Run a real ReAct loop: Thought -> Action -> Observation -> Final Answer."""

    print(f"\n[REACT AGENT] Câu hỏi: {user_query}")
    scratchpad = ""

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- Vòng lặp ReAct {step}/{MAX_ITERATIONS} ---")
        prompt = _build_react_prompt(user_query, scratchpad)
        llm_output = _generate_with_fallback(provider, prompt, REACT_SYSTEM_PROMPT).strip()
        print(llm_output)

        final_answer = _extract_final_answer(llm_output)
        if final_answer:
            print("\n[FINAL]")
            print(final_answer)
            return final_answer

        action = _parse_action(llm_output)
        if action is None:
            observation = (
                "LỖI: Agent không trả về Action hợp lệ. "
                'Hãy dùng định dạng: Action: tool_name["tham số"].'
            )
        else:
            tool_name, args = action
            observation = _execute_tool(tool_name, args)

        print(f"Observation: {observation}")
        scratchpad += f"{llm_output}\nObservation: {observation}\n"

    guardrail_message = (
        f"Đã đạt giới hạn {MAX_ITERATIONS} vòng lặp. "
        "Mình chưa đủ thông tin chắc chắn để trả lời an toàn."
    )
    print(f"\n[GUARDRAIL] {guardrail_message}")
    return guardrail_message


def _build_react_prompt(user_query: str, scratchpad: str) -> str:
    if not scratchpad:
        return f"User Question: {user_query}"
    return f"User Question: {user_query}\n\nTrace hiện tại:\n{scratchpad}"


def _generate_with_fallback(provider, prompt: str, system_prompt: str) -> str:
    response = provider.generate(prompt, system_prompt=system_prompt)
    if _looks_like_provider_error(response):
        fallback = MockProvider()
        return fallback.generate(prompt, system_prompt=system_prompt)
    return response


def _looks_like_provider_error(response: str) -> bool:
    return bool(re.match(r"^\[[^\]]+ (Error|Exception)", str(response).strip()))


def _extract_final_answer(text: str) -> str | None:
    match = re.search(r"Final Answer:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def _parse_action(text: str) -> tuple[str, list[Any]] | None:
    match = re.search(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(.*)\]\s*$", text, flags=re.DOTALL)
    if not match:
        return None

    tool_name = match.group(1)
    raw_args = match.group(2).strip()
    if not raw_args:
        return tool_name, []

    try:
        parsed_args = ast.literal_eval(f"[{raw_args}]")
    except (SyntaxError, ValueError):
        parsed_args = [item.strip().strip("'\"") for item in raw_args.split(",")]

    return tool_name, parsed_args


def _execute_tool(tool_name: str, args: list[Any]) -> str:
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        return f"LỖI: Tool '{tool_name}' không tồn tại. Tools có sẵn: {', '.join(AVAILABLE_TOOLS)}."

    try:
        return str(tool(*args))
    except TypeError as exc:
        return f"LỖI: Sai tham số khi gọi {tool_name}: {exc}"
    except Exception as exc:
        return f"LỖI: Tool {tool_name} gặp sự cố: {exc}"


def run_all_tests(provider) -> None:
    tests = load_test_cases()
    print(f"Đã tải {len(tests)} test cases từ config/test_cases.json")
    for test in tests:
        print("\n" + "=" * 70)
        print(f"Test {test['id']}: {test['question']}")
        print(f"Kỳ vọng: {test['expected_behavior']}")
        run_baseline_chatbot(test["question"], provider)
        run_react_agent(test["question"], provider)


if __name__ == "__main__":
    print("=" * 70)
    print("VINUNI LAB 3: COURSE ADVISING CHATBOT VS REACT AGENT")
    print("=" * 70)

    llm_provider = get_llm_provider()
    model_name = getattr(llm_provider, "model_name", "unknown")
    print(f"LLM Provider: {llm_provider.__class__.__name__} ({model_name})")
    run_all_tests(llm_provider)

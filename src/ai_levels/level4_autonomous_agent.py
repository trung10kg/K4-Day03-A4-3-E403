"""
Level 4: Autonomous agent with simple planning and memory.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import check_prerequisites, search_course_sections, search_courses


class AutonomousGoalAgent:
    def __init__(self, goal: str, max_steps: int = 4):
        self.goal = goal
        self.max_steps = max_steps
        self.memory: list[dict[str, str]] = []

    def execute(self) -> None:
        print(f"=== Autonomous Goal: {self.goal} ===")

        steps = [
            (
                "Tìm các học phần liên quan đến dữ liệu.",
                lambda: search_courses("dữ liệu"),
            ),
            (
                "Kiểm tra điều kiện học DS201.",
                lambda: check_prerequisites("Nhập môn lập trình, Xác suất thống kê", "DS201"),
            ),
            (
                "Tra cứu lớp DS201 còn chỗ trong học kỳ mục tiêu.",
                lambda: search_course_sections("DS201", "Học kỳ 1 2026-2027"),
            ),
        ]

        for step_number, (plan, action) in enumerate(steps[: self.max_steps], start=1):
            print(f"\nStep {step_number}/{self.max_steps}")
            print(f"Planning : {plan}")
            result = action()
            print(f"Execution:\n{result}")
            self.memory.append({"step": str(step_number), "plan": plan, "result": result})

        print("\nGoal Evaluation: Đã có đủ dữ liệu để đề xuất học phần và lớp phù hợp.")


if __name__ == "__main__":
    agent = AutonomousGoalAgent("Lập kế hoạch đăng ký học phần dữ liệu cho học kỳ 1 2026-2027")
    agent.execute()

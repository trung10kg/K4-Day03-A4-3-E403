"""
Level 3: Reactive Agent using Thought -> Action -> Observation.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import check_prerequisites, search_course_sections, search_courses


def reactive_agent_step(user_goal: str) -> None:
    print(f"Goal: {user_goal}")

    print("\nThought 1: Câu hỏi cần dữ liệu học phần, nên tôi sẽ gọi tool tra cứu.")
    print('Action 1 : search_courses("dữ liệu")')
    obs1 = search_courses("dữ liệu")
    print(f"Observation 1:\n{obs1}")

    print("\nThought 2: Sinh viên quan tâm DS201, cần kiểm tra điều kiện tiên quyết.")
    print('Action 2 : check_prerequisites("Nhập môn lập trình, Xác suất thống kê", "DS201")')
    obs2 = check_prerequisites("Nhập môn lập trình, Xác suất thống kê", "DS201")
    print(f"Observation 2:\n{obs2}")

    print("\nThought 3: Đã đủ điều kiện, kiểm tra lớp còn chỗ.")
    print('Action 3 : search_course_sections("DS201", "Học kỳ 1 2026-2027")')
    obs3 = search_course_sections("DS201", "Học kỳ 1 2026-2027")
    print(f"Observation 3:\n{obs3}")

    print(
        "\nFinal Answer: Bạn phù hợp với nhóm học phần dữ liệu. "
        "Với DS201, bạn đã đủ điều kiện nếu đã hoàn thành Nhập môn lập trình "
        "và Xác suất thống kê. Lớp DS201-01 còn chỗ; DS201-02 đã đầy."
    )


if __name__ == "__main__":
    print("=== DEMO LEVEL 3: REACTIVE AGENT ===")
    reactive_agent_step("Tôi muốn học môn dữ liệu và kiểm tra DS201 còn lớp không.")

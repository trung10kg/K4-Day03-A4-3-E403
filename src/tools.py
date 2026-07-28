"""Các tool mô phỏng cho chatbot/agent tư vấn học phần sinh viên."""

import unicodedata


def get_weather(location: str) -> str:
    """Tool cũ của bài mẫu, được giữ lại để tương thích với phần demo hiện có."""
    loc_lower = _normalize(location)
    if "ha noi" in loc_lower:
        return "Thời tiết Hà Nội: 28°C, nắng nhẹ, độ ẩm 65%."
    if any(name in loc_lower for name in ("ho chi minh", "tp.hcm", "hcm")):
        return "Thời tiết TP.HCM: 33°C, nắng nóng, có mây."
    if "da nang" in loc_lower:
        return "Thời tiết Đà Nẵng: 30°C, gió nhẹ, mát mẻ."
    return f"LỖI: Không tìm thấy dữ liệu thời tiết cho địa điểm '{location}'."


def search_flights(origin: str, destination: str) -> str:
    """Tool cũ của bài mẫu, được giữ lại để tương thích với phần demo hiện có."""
    return (
        f"Chuyến bay từ {origin} -> {destination} ngày mai:\n"
        "1. VN123 (08:00) - Giá: 1.500.000 VNĐ (Còn vé)\n"
        "2. VJ456 (14:30) - Giá: 1.200.000 VNĐ (Còn vé)"
    )


# Dữ liệu mô phỏng để demo luồng gọi tool. Khi triển khai thật, thay các hằng
# số này bằng API hoặc cơ sở dữ liệu quản lý đào tạo của trường.
COURSE_CATALOG = {
    "CS101": {
        "name": "Nhập môn lập trình",
        "credits": 3,
        "tags": ("lập trình", "programming", "nền tảng"),
        "prerequisites": (),
    },
    "MA201": {
        "name": "Xác suất thống kê",
        "credits": 3,
        "tags": ("xác suất", "thống kê", "statistics", "phân tích dữ liệu"),
        "prerequisites": (),
    },
    "DS201": {
        "name": "Phân tích dữ liệu",
        "credits": 3,
        "tags": ("dữ liệu", "data analytics", "phân tích dữ liệu", "python"),
        "prerequisites": ("Nhập môn lập trình", "Xác suất thống kê"),
    },
    "DB202": {
        "name": "Cơ sở dữ liệu",
        "credits": 3,
        "tags": ("dữ liệu", "database", "sql"),
        "prerequisites": ("Nhập môn lập trình",),
    },
    "ML301": {
        "name": "Nhập môn học máy",
        "credits": 3,
        "tags": ("học máy", "machine learning", "dữ liệu", "ai"),
        "prerequisites": ("Phân tích dữ liệu",),
    },
}

COURSE_SECTIONS = {
    "DS201": (
        ("DS201-01", "Thứ 2 08:00–10:50", 8),
        ("DS201-02", "Thứ 4 13:00–15:50", 0),
    ),
    "DB202": (
        ("DB202-01", "Thứ 3 08:00–10:50", 12),
        ("DB202-02", "Thứ 6 13:00–15:50", 5),
    ),
    "ML301": (
        ("ML301-01", "Thứ 5 08:00–10:50", 4),
    ),
}


def _normalize(text: str) -> str:
    """Chuẩn hoá chuỗi tiếng Việt để tìm kiếm không phân biệt dấu/chữ hoa."""
    text = unicodedata.normalize("NFD", str(text).casefold())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("đ", "d").strip()


def _find_course(course_name: str):
    """Tìm học phần theo mã hoặc tên; trả về (mã, dữ liệu) hoặc (None, None)."""
    query = _normalize(course_name)
    for code, course in COURSE_CATALOG.items():
        if query in {_normalize(code), _normalize(course["name"])}:
            return code, course
    return None, None


def search_courses(keyword: str) -> str:
    """
    Tìm học phần theo mã, tên hoặc lĩnh vực quan tâm.

    Args:
        keyword: Ví dụ: "phân tích dữ liệu", "SQL", hoặc "DS201".
    """
    query = _normalize(keyword)
    if not query:
        return "LỖI: Vui lòng cung cấp từ khóa, mã hoặc lĩnh vực học phần cần tìm."

    matches = []
    for code, course in COURSE_CATALOG.items():
        searchable = " ".join((code, course["name"], *course["tags"]))
        if query in _normalize(searchable):
            prerequisites = ", ".join(course["prerequisites"]) or "Không có"
            matches.append(
                f"- {code} — {course['name']} ({course['credits']} tín chỉ). "
                f"Tiên quyết: {prerequisites}."
            )

    if not matches:
        return f"Không tìm thấy học phần phù hợp với '{keyword}'."
    return "Các học phần phù hợp:\n" + "\n".join(matches)


def check_prerequisites(completed_courses: str, target_course: str) -> str:
    """
    Kiểm tra sinh viên đã đáp ứng các học phần tiên quyết hay chưa.

    Args:
        completed_courses: Các học phần đã hoàn thành, ngăn cách bằng dấu phẩy.
        target_course: Mã hoặc tên học phần muốn đăng ký.
    """
    code, course = _find_course(target_course)
    if course is None:
        return f"LỖI: Không tìm thấy học phần '{target_course}' để kiểm tra điều kiện."

    completed = {_normalize(item) for item in str(completed_courses).split(",") if item.strip()}
    missing = [
        prerequisite
        for prerequisite in course["prerequisites"]
        if _normalize(prerequisite) not in completed
    ]
    if missing:
        return (
            f"Chưa đủ điều kiện học {code} — {course['name']}. "
            f"Học phần còn thiếu: {', '.join(missing)}."
        )
    return f"Đủ điều kiện học {code} — {course['name']}."


def search_course_sections(course_name: str, semester: str) -> str:
    """
    Tra cứu các lớp học phần và số chỗ còn lại trong một học kỳ.

    Args:
        course_name: Mã hoặc tên học phần.
        semester: Ví dụ: "Học kỳ 1 2026-2027".
    """
    code, course = _find_course(course_name)
    if course is None:
        return f"LỖI: Không tìm thấy học phần '{course_name}'."
    if not str(semester).strip():
        return "LỖI: Vui lòng cung cấp học kỳ cần tra cứu."

    sections = COURSE_SECTIONS.get(code, ())
    if not sections:
        return f"Chưa có lớp mở cho {code} — {course['name']} trong {semester}."

    lines = []
    for section_code, schedule, remaining_seats in sections:
        status = f"còn {remaining_seats} chỗ" if remaining_seats else "đã đầy"
        lines.append(f"- {section_code}: {schedule}; {status}.")
    return f"Lớp {code} — {course['name']} trong {semester}:\n" + "\n".join(lines)


def check_class_availability(course_name: str, semester: str) -> str:
    """Alias rõ nghĩa cho việc kiểm tra lớp còn chỗ của một học phần."""
    return search_course_sections(course_name, semester)


AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "search_flights": search_flights,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "search_course_sections": search_course_sections,
    "check_class_availability": check_class_availability,
}

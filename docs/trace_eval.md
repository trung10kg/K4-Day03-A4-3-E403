# BÁO CÁO ROLE 5 — OBSERVABILITY & EVALUATION

**Chủ đề:** Trợ lý tư vấn khóa học sinh viên  
**Artifact:** `config/test_cases.json`, `src/tools.py`, log chạy Baseline và ReAct Agent

## 1. SCORING MATRIX — Agentic Fit

| Tiêu chí | Câu hỏi đánh giá | Điểm (1–5) | Bằng chứng | Nhận định |
| :--- | :--- | :---: | :--- | :--- |
| **Multi-step Reasoning** | Có cần nhiều bước suy luận không? | **5/5** | Cần kiểm tra môn đã học, điều kiện tiên quyết, rồi tra lớp còn chỗ. | Phù hợp ReAct Agent. |
| **Tool Interaction** | Có cần dữ liệu ngoài kiến thức LLM không? | **5/5** | Danh mục môn, điều kiện và số chỗ lớp phụ thuộc dữ liệu học vụ. | Cần tool tra cứu. |
| **Dynamic Decision** | Kết quả bước trước có quyết định bước sau không? | **4/5** | Chỉ tra lớp nếu sinh viên đủ điều kiện tiên quyết. | Có nhánh quyết định rõ ràng. |
| **Long Horizon** | Quy trình có nhiều bước kéo dài không? | **4/5** | Tư vấn có thể gồm tìm môn, kiểm tra điều kiện và tra lớp. | Cần giới hạn vòng lặp. |
| **TỔNG ĐIỂM FIT** |  | **18/20** |  | **Nên dùng ReAct Agent có tool và guardrail.** |

## 2. Role 5 — Mốc 2: Nhật ký Chatbot Baseline

| Test case | Phản hồi quan sát được từ Baseline | Nhận xét | Kết quả |
| :---: | :--- | :--- | :--- |
| **TC1** | “Để học tốt lập trình, bạn nên luyện code đều đặn, nắm chắc tư duy giải thuật...” | Câu hỏi hỏi về tín chỉ và khối lượng học, nhưng chatbot trả lời về lập trình. Đây là phản hồi lạc đề. | **Không đạt** |
| **TC2** | “Để học tốt lập trình, bạn nên luyện code đều đặn, nắm chắc tư duy giải thuật...” | Liên quan một phần đến kỹ năng lập trình, nhưng bỏ sót thống kê, tư duy phân tích, tiếng Anh và tự học. | **Đạt một phần** |
| **TC3** | “Tôi có thể tư vấn chung, nhưng baseline chatbot không có tool để kiểm chứng dữ liệu học phần, điều kiện tiên quyết hoặc lớp còn chỗ.” | Trung thực về giới hạn dữ liệu; không thể hoàn thành yêu cầu tra cứu. | **An toàn; chưa hoàn thành nhiệm vụ** |
| **TC4** | “Tôi có thể tư vấn chung, nhưng baseline chatbot không có tool để kiểm chứng dữ liệu học phần, điều kiện tiên quyết hoặc lớp còn chỗ.” | Không thể kiểm tra tiên quyết và số chỗ nên không thể giải quyết luồng nhiều bước. | **An toàn; chưa hoàn thành nhiệm vụ** |
| **TC5** | “Tôi có thể tư vấn chung, nhưng baseline chatbot không có tool để kiểm chứng dữ liệu học phần, điều kiện tiên quyết hoặc lớp còn chỗ.” | Không bịa dữ liệu cho mã `XYZ999`, nhưng nên gợi ý kiểm tra lại mã môn. | **An toàn; cần fallback tốt hơn** |

**Kết luận Mốc 2:** Baseline không phù hợp cho truy vấn cần dữ liệu học vụ. Hai câu đơn giản cũng cần cải thiện prompt để tránh trả lời mẫu lạc đề.

## 3. Role 5 — Mốc 3: Trích xuất ReAct Trace

Mục tiêu Mốc 3 là kiểm tra chuỗi `Thought → Action → Observation`, bao gồm đúng tên tool, đúng tham số, đủ bước và kết luận bám dữ liệu Observation.

| Test case | Trace đã quan sát | Đánh giá |
| :---: | :--- | :--- |
| **TC1** | Vòng 1 không có `Action` hợp lệ; hệ thống trả `LỖI: Agent không trả về Action hợp lệ`. Vòng 2 agent dùng chính lỗi này làm Final Answer. | **Không đạt.** Câu đơn giản không cần tool nhưng agent thiếu nhánh trả lời trực tiếp ổn định. |
| **TC2** | `Thought: Cần tìm học phần phù hợp.` → `Action: search_courses["dữ liệu"]` → Observation trả về MA201, DS201, DB202, ML301. | **Tool đúng nhưng chưa tối ưu.** TC2 hỏi kỹ năng nên không cần tool. |
| **TC3** | `Thought: Cần tìm học phần phù hợp.` → `Action: search_courses["SQL"]` → Observation trả về DB202. | **Đạt.** Đúng tool, đúng tham số, kết quả bám câu hỏi. |
| **TC4** | `Action: check_prerequisites["Nhập môn lập trình, Xác suất thống kê", "DS201"]` → Observation: đủ điều kiện học DS201. Agent kết thúc ngay sau đó. | **Chưa đạt.** Thiếu bước `search_course_sections` để trả lời phần lớp còn chỗ. |
| **TC5** | User hỏi `XYZ999`, nhưng agent gọi `search_course_sections["DS201", "Học kỳ 1 2026-2027"]`. | **Không đạt nghiêm trọng.** Action không dùng tham số từ câu hỏi, nên trả dữ liệu sai và không kiểm tra fallback. |

### TC3 — Trace đạt yêu cầu

```text
Thought: Cần tìm học phần phù hợp.
Action: search_courses["SQL"]
Observation: Các học phần phù hợp:
- DB202 — Cơ sở dữ liệu (3 tín chỉ). Tiên quyết: Nhập môn lập trình.

Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: DB202 — Cơ sở dữ liệu phù hợp với SQL; môn có 3 tín chỉ và yêu cầu Nhập môn lập trình.
```

### TC4 — Trace thiếu bước bắt buộc

```text
Thought: Cần kiểm tra điều kiện tiên quyết bằng tool.
Action: check_prerequisites["Nhập môn lập trình, Xác suất thống kê", "DS201"]
Observation: Đủ điều kiện học DS201 — Phân tích dữ liệu.

Final Answer hiện tại: chỉ thông báo đủ điều kiện.
Thiếu Action: search_course_sections["Phân tích dữ liệu", "Học kỳ 1 2026-2027"].
```

### TC5 — Trace sai tham số

```text
User query: Tra các lớp còn chỗ của học phần XYZ999 trong Học kỳ 1 2026-2027.
Action thực tế: search_course_sections["DS201", "Học kỳ 1 2026-2027"]
Observation thực tế: trả về các lớp DS201.

Action đúng: search_course_sections["XYZ999", "Học kỳ 1 2026-2027"]
Observation mong đợi: LỖI: Không tìm thấy học phần 'XYZ999'.
```

## 4. Khuyến nghị sau quan sát Mốc 3

| Vấn đề | Ảnh hưởng | Khuyến nghị |
| :--- | :--- | :--- |
| Thiếu nhánh trả lời trực tiếp | TC1 lỗi parser dù không cần tool. | Role 3 & 4 thêm quy tắc Final Answer cho câu đơn giản. |
| Gọi tool không cần thiết | TC2 tốn vòng lặp và lệch mục tiêu. | Role 3 quy định rõ điều kiện dùng tool. |
| Kết thúc trước khi hoàn thành | TC4 không tra lớp còn chỗ. | Role 3 & 4 kiểm tra mọi yêu cầu con trước Final Answer. |
| Tham số Action không bám user query | TC5 tạo câu trả lời sai, mất edge case. | Role 3 & 4 bắt buộc dùng mã/tên người dùng cung cấp; không thay bằng giá trị mặc định. |

> Guardrail giới hạn `MAX_ITERATIONS = 3` vẫn cần thiết, nhưng không được khiến agent kết thúc trước khi hoàn thành các Action bắt buộc.

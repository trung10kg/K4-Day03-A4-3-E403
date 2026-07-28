"""Giao diện web cục bộ cho Trợ lý tư vấn khóa học sinh viên.

Chạy từ thư mục dự án:
    python src/web_app.py
Sau đó mở http://127.0.0.1:8501
"""

from __future__ import annotations

import argparse
import io
import json
import threading
from contextlib import redirect_stdout
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from app import run_baseline_chatbot, run_react_agent
from providers import get_llm_provider


HOST = "127.0.0.1"
DEFAULT_PORT = 8501
PROVIDER = get_llm_provider()
AGENT_LOCK = threading.Lock()


PAGE = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CourseMate | Trợ lý tư vấn học phần</title>
  <style>
    :root { --navy:#102a43; --blue:#2563eb; --soft:#eef5ff; --ink:#172033; --muted:#64748b; --line:#dbe4f0; --white:#fff; --green:#078a5a; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; color:var(--ink); background:linear-gradient(135deg,#f6f9ff 0%,#eef5ff 100%); }
    .app { min-height:100vh; display:grid; grid-template-columns:300px minmax(0,1fr); }
    aside { padding:32px 24px; background:var(--navy); color:#eff6ff; display:flex; flex-direction:column; gap:28px; }
    .brand { display:flex; align-items:center; gap:12px; font-size:21px; font-weight:800; letter-spacing:-.4px; }
    .brand-mark { width:38px; height:38px; display:grid; place-items:center; border-radius:12px; background:#3b82f6; font-size:20px; }
    .eyebrow { margin:0 0 8px; color:#b9d5ff; font-size:12px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
    aside h2 { margin:0 0 8px; font-size:16px; }
    aside p { margin:0; color:#c7d5e8; line-height:1.55; font-size:14px; }
    .mode { display:grid; gap:10px; }
    .mode button { width:100%; padding:14px; border:1px solid #40617f; border-radius:12px; background:transparent; color:#dcecff; text-align:left; cursor:pointer; transition:.18s ease; }
    .mode button:hover, .mode button.active { background:#1e4971; border-color:#78b4ff; }
    .mode strong, .mode span { display:block; }
    .mode span { margin-top:3px; font-size:12px; color:#b9d5ff; }
    .notice { margin-top:auto; padding:14px; border:1px solid #3b5c7d; border-radius:12px; background:#173955; color:#c7d5e8; font-size:13px; line-height:1.5; }
    main { width:min(940px,100%); margin:0 auto; min-height:100vh; padding:46px 36px 28px; display:flex; flex-direction:column; }
    header { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; margin-bottom:28px; }
    h1 { margin:0; color:#102a43; letter-spacing:-1px; font-size:clamp(27px,4vw,40px); }
    .subtitle { max-width:650px; margin:10px 0 0; color:var(--muted); line-height:1.6; }
    .status { white-space:nowrap; margin-top:5px; padding:8px 12px; border-radius:999px; background:#e8f8f1; color:var(--green); font-size:13px; font-weight:700; }
    .chat { flex:1; display:flex; flex-direction:column; gap:16px; padding:10px 0 24px; overflow-y:auto; }
    .message { display:flex; gap:11px; max-width:820px; }
    .message.user { align-self:flex-end; flex-direction:row-reverse; }
    .avatar { flex:0 0 34px; height:34px; display:grid; place-items:center; border-radius:10px; background:#dceafe; font-size:16px; }
    .user .avatar { background:#d8f5e9; }
    .bubble { padding:14px 16px; border:1px solid var(--line); border-radius:4px 16px 16px; background:var(--white); box-shadow:0 6px 22px rgba(30,64,104,.06); line-height:1.6; white-space:pre-wrap; }
    .user .bubble { border:0; border-radius:16px 4px 16px 16px; background:var(--blue); color:white; }
    .trace { width:100%; margin:2px 0 0 45px; border:1px solid #d8e3f3; border-radius:12px; background:#fbfdff; overflow:hidden; }
    .trace summary { padding:11px 14px; cursor:pointer; color:#31506f; font-weight:700; font-size:13px; }
    .trace pre { max-height:260px; overflow:auto; margin:0; padding:0 14px 14px; color:#35516c; white-space:pre-wrap; font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace; }
    .suggestions { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
    .suggestions button { border:1px solid #cfe0f5; border-radius:999px; padding:8px 12px; background:#f8fbff; color:#31506f; cursor:pointer; font-size:13px; }
    .suggestions button:hover { border-color:#7aa9e9; background:#edf5ff; }
    form { display:flex; gap:12px; padding:12px; border:1px solid #cad9ed; border-radius:18px; background:var(--white); box-shadow:0 10px 28px rgba(30,64,104,.10); }
    textarea { flex:1; min-height:48px; max-height:130px; resize:vertical; border:0; outline:0; padding:9px 4px; color:var(--ink); font:15px/1.45 inherit; }
    #send { align-self:flex-end; border:0; border-radius:12px; padding:12px 18px; background:var(--blue); color:white; font-weight:700; cursor:pointer; }
    #send:disabled { opacity:.55; cursor:wait; }
    .loading .bubble { color:var(--muted); font-style:italic; }
    @media (max-width:720px) { .app { display:block; } aside { padding:20px; } .notice { display:none; } main { padding:28px 18px 20px; } header { display:block; } .status { display:inline-block; } }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand"><span class="brand-mark">🎓</span><span>CourseMate</span></div>
      <section>
        <p class="eyebrow">Chế độ trả lời</p>
        <div class="mode">
          <button class="active" data-mode="react"><strong>ReAct Agent</strong><span>Tra cứu học phần, tiên quyết và lớp mở</span></button>
          <button data-mode="baseline"><strong>Chatbot Baseline</strong><span>Tư vấn chung, không dùng tool</span></button>
        </div>
      </section>
      <section>
        <h2>Agent có thể hỗ trợ</h2>
        <p>• Tìm học phần theo định hướng<br>• Kiểm tra điều kiện tiên quyết<br>• Tra lịch lớp và số chỗ còn lại</p>
      </section>
      <div class="notice">Dữ liệu học phần trong bài lab là dữ liệu mô phỏng. Hãy đối chiếu cổng học vụ trước khi đăng ký chính thức.</div>
    </aside>
    <main>
      <header>
        <div><p class="eyebrow" style="color:#2563eb">VinUni Lab 3</p><h1>Trợ lý tư vấn khóa học</h1><p class="subtitle">Hỏi về kỹ năng, tìm học phần hoặc kiểm tra điều kiện đăng ký. Chọn ReAct Agent khi câu hỏi cần dữ liệu học vụ.</p></div>
        <span class="status" id="mode-label">● ReAct Agent</span>
      </header>
      <section class="chat" id="chat" aria-live="polite">
        <div class="message"><div class="avatar">🎓</div><div class="bubble">Chào bạn! Mình là CourseMate. Bạn muốn tìm học phần, kiểm tra môn tiên quyết hay chọn lớp còn chỗ?</div></div>
      </section>
      <div class="suggestions">
        <button data-question="Em muốn theo hướng phân tích dữ liệu. Em nên rèn những kỹ năng nào?">Tư vấn kỹ năng dữ liệu</button>
        <button data-question="Hãy tìm các học phần liên quan đến dữ liệu hoặc SQL mà em có thể tham khảo.">Tìm môn dữ liệu / SQL</button>
        <button data-question="Em đã hoàn thành Nhập môn lập trình và Xác suất thống kê. Hãy kiểm tra em có đủ điều kiện học Phân tích dữ liệu không, rồi tra các lớp còn chỗ trong Học kỳ 1 2026-2027.">Kiểm tra tiên quyết</button>
      </div>
      <form id="chat-form"><textarea id="question" placeholder="Nhập câu hỏi của bạn..." required></textarea><button id="send" type="submit">Gửi</button></form>
    </main>
  </div>
  <script>
    const chat = document.getElementById('chat');
    const form = document.getElementById('chat-form');
    const question = document.getElementById('question');
    const send = document.getElementById('send');
    const modeLabel = document.getElementById('mode-label');
    let mode = 'react';

    function addMessage(text, who, trace = '') {
      const row = document.createElement('div'); row.className = `message ${who}`;
      const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.textContent = who === 'user' ? '🧑‍🎓' : '🎓';
      const bubble = document.createElement('div'); bubble.className = 'bubble'; bubble.textContent = text;
      row.append(avatar, bubble); chat.appendChild(row);
      if (trace) { const details = document.createElement('details'); details.className = 'trace'; const summary = document.createElement('summary'); summary.textContent = 'Xem trace xử lý'; const pre = document.createElement('pre'); pre.textContent = trace; details.append(summary, pre); chat.appendChild(details); }
      chat.scrollTop = chat.scrollHeight;
      return row;
    }

    document.querySelectorAll('.mode button').forEach(button => button.addEventListener('click', () => {
      mode = button.dataset.mode; document.querySelectorAll('.mode button').forEach(item => item.classList.toggle('active', item === button));
      modeLabel.textContent = mode === 'react' ? '● ReAct Agent' : '● Chatbot Baseline';
    }));
    document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => { question.value = button.dataset.question; question.focus(); }));

    form.addEventListener('submit', async (event) => {
      event.preventDefault(); const text = question.value.trim(); if (!text) return;
      addMessage(text, 'user'); question.value = ''; send.disabled = true;
      const loading = addMessage('Đang suy nghĩ...', 'assistant'); loading.classList.add('loading');
      try {
        const response = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:text, mode}) });
        const data = await response.json(); loading.remove();
        addMessage(data.answer || 'Mình chưa thể tạo phản hồi.', 'assistant', data.trace || '');
      } catch (error) { loading.remove(); addMessage('Không thể kết nối tới máy chủ. Vui lòng thử lại.', 'assistant'); }
      finally { send.disabled = false; question.focus(); }
    });
  </script>
</body>
</html>"""


def ask_agent(question: str, mode: str) -> dict[str, str]:
    """Run an existing agent function and return its answer plus console trace."""

    output = io.StringIO()
    with AGENT_LOCK, redirect_stdout(output):
        if mode == "baseline":
            answer = run_baseline_chatbot(question, PROVIDER)
        else:
            answer = run_react_agent(question, PROVIDER)
    return {"answer": answer, "trace": output.getvalue().strip()}


class ChatHandler(BaseHTTPRequestHandler):
    """Serve the interface and the same-origin JSON chat endpoint."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in {"/", "/index.html"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Không tìm thấy trang.")
            return
        self._send(HTTPStatus.OK, PAGE.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Không tìm thấy API.")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload: dict[str, Any] = json.loads(self.rfile.read(size).decode("utf-8"))
            question = str(payload.get("question", "")).strip()
            mode = str(payload.get("mode", "react"))
            if not question:
                raise ValueError("Vui lòng nhập câu hỏi.")
            if mode not in {"baseline", "react"}:
                raise ValueError("Chế độ không hợp lệ.")
            self._send_json(HTTPStatus.OK, ask_agent(question, mode))
        except (ValueError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"answer": str(error), "trace": ""})
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"answer": "Có lỗi khi xử lý câu hỏi. Vui lòng thử lại.", "trace": ""})

    def log_message(self, _format: str, *_args: object) -> None:
        """Keep normal browser requests from cluttering the demo terminal."""

    def _send_json(self, status: HTTPStatus, payload: dict[str, str]) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CourseMate web interface.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Local port (default: 8501).")
    args = parser.parse_args()

    server = ThreadingHTTPServer((HOST, args.port), ChatHandler)
    print(f"CourseMate đang chạy tại http://{HOST}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng CourseMate.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

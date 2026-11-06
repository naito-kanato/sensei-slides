"""review_record.py：レビューを別の担当がしたかを、会話の記録（Claude Code・Codex の形を真似たもの）で確かめる。"""
import json
import os
import re

import time
from datetime import datetime, timedelta, timezone

import review_record as rr

NOW = time.time()


def iso(sec=0.0):
    """今から sec 秒あとの時刻（記録の形）。"""
    return (datetime.fromtimestamp(NOW, timezone.utc) + timedelta(seconds=sec)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def _work(tmp_path):
    w = tmp_path / "proj" / "_work" / "重力波の初観測"
    (w / "render").mkdir(parents=True)
    (w / "outline.md").write_text("# 構成案\n", encoding="utf-8")
    (w / "outline_review.md").write_text("判定\n", encoding="utf-8")
    (w / "review.md").write_text("## 判定\n", encoding="utf-8")
    return w


def _claude_dir(work):
    key = re.sub(r"[^A-Za-z0-9]", "-", str((work.parents[1]).resolve()))
    return rr.claude_home() / "projects" / key


def _use(tool, path, model="model-x", ts=None):
    return {"type": "assistant", "timestamp": ts or iso(),
            "message": {"model": model, "content": [{"type": "tool_use", "name": tool, "input": {"file_path": str(path)}}]}}


def test_no_records_is_unknown(tmp_path):
    w = _work(tmp_path)
    mark, item, msg = rr.check(w, "final")
    assert mark == "△" and "見つからない" in msg


def test_claude_subagent_review_passes(tmp_path):
    w = _work(tmp_path)
    d = _claude_dir(w)
    _write(d / "s1.jsonl", [_use("Write", w / "review.md")])
    _write(d / "s1" / "subagents" / "agent-a1.jsonl",
           [_use("Read", w / "render" / "slide-01.png", model="model-big"), _use("Read", w / "outline.md", model="model-small")])
    future = NOW + 60   # 記録の直後をレビューの終わりとみなす
    assert rr.check(w, "final", until=future)[0] == "✔"
    m = rr.check(w, "outline", until=future)
    assert m[0] == "✔" and "model-big" in m[2] and "Claude Code" in m[2]


def test_main_only_review_fails(tmp_path):
    """メインだけが画像を開いてレビューを書いた（担当の記録が無い）→ ✘。"""
    w = _work(tmp_path)
    d = _claude_dir(w)
    _write(d / "s1.jsonl", [_use("Read", w / "render" / "slide-01.png"), _use("Write", w / "review.md")])
    mark, _, msg = rr.check(w, "final", until=NOW + 60)
    assert mark == "✘" and "メインが自分で" in msg


def test_subagent_outside_window_does_not_count(tmp_path):
    w = _work(tmp_path)
    d = _claude_dir(w)
    _write(d / "s1.jsonl", [_use("Write", w / "review.md")])
    _write(d / "s1" / "subagents" / "agent-a1.jsonl", [_use("Read", w / "render" / "slide-01.png", ts=iso(-40 * 86400))])
    assert rr.check(w, "final", until=NOW + 60)[0] == "✘"


def test_codex_subagent_skips_forked_history(tmp_path):
    """Codex の担当の記録は、起動時点までのメインの会話の写しで始まる。写しの中の操作は担当の操作に数えない。"""
    w = _work(tmp_path)
    root = rr.codex_home() / "sessions" / "2026" / "01" / "01"
    cwd = str(w.parents[1])
    _write(root / "rollout-main.jsonl", [
        {"type": "session_meta", "timestamp": iso(), "payload": {"thread_source": "user", "cwd": cwd, "timestamp": iso()}},
        {"type": "response_item", "timestamp": iso(1), "payload": {"type": "function_call", "name": "exec", "arguments": f"Get-Content '{w / 'outline.md'}'"}}])
    sub = [{"type": "session_meta", "timestamp": iso(600), "payload": {"thread_source": "subagent", "timestamp": iso(600)}},
           # 写し（起動から1秒以内）
           {"type": "response_item", "timestamp": iso(600.3), "payload": {"type": "custom_tool_call", "input": f"view_image('{w / 'render' / 'slide-01.png'}')"}}]
    _write(root / "rollout-sub.jsonl", sub)
    until = NOW + 3600
    assert rr.check(w, "final", until=until)[0] == "✘"
    sub += [{"type": "turn_context", "timestamp": iso(605), "payload": {"model": "gpt-x"}},
            {"type": "response_item", "timestamp": iso(606), "payload": {"type": "custom_tool_call", "input": f"view_image('{w / 'render' / 'slide-01.png'}')"}}]
    _write(root / "rollout-sub.jsonl", sub)
    mark, _, msg = rr.check(w, "final", until=until)
    assert mark == "✔" and "Codex" in msg and "gpt-x" in msg


def test_guardian_review_is_not_a_reviewer(tmp_path):
    w = _work(tmp_path)
    root = rr.codex_home() / "sessions"
    _write(root / "rollout-g.jsonl", [
        {"type": "session_meta", "timestamp": iso(), "payload": {"thread_source": "guardian_review", "timestamp": iso()}},
        {"type": "response_item", "timestamp": iso(5), "payload": {"type": "custom_tool_call", "input": f"view_image('{w / 'render' / 'a.png'}')"}}])
    assert rr.check(w, "final", until=NOW + 60)[0] == "△"


def test_same_folder_name_elsewhere_does_not_count(tmp_path):
    """別の場所にある同じ名前のフォルダ（スキルのコピーの examples/zemi など）を開いても、この作業フォルダのレビューに数えない。"""
    w = _work(tmp_path)
    other = tmp_path / "copy" / "_work" / w.name
    d = _claude_dir(w)
    _write(d / "s1.jsonl", [_use("Write", w / "review.md")])
    _write(d / "s1" / "subagents" / "agent-a1.jsonl", [_use("Read", other / "render" / "slide-01.png")])
    assert rr.check(w, "final", until=NOW + 60)[0] == "✘"


def test_session_started_outside_the_work_folder(tmp_path):
    """作業フォルダの外（別のプロジェクトのフォルダ）で始めた会話でも、絶対パスで開いていれば拾う。"""
    w = _work(tmp_path)
    d = rr.claude_home() / "projects" / "C--somewhere-else"
    _write(d / "s1.jsonl", [_use("Write", w / "review.md")])
    _write(d / "s1" / "subagents" / "agent-a1.jsonl", [_use("Read", w / "render" / "slide-01.png", model="model-big")])
    assert rr.check(w, "final", until=NOW + 60)[0] == "✔"

"""使用量を抑える部品：guide.py（節だけ出す）・make_deck.py（組む→検査を1回で。描画は試験では省く）・少なすぎる本文と原稿の検査。"""
import subprocess
import sys
from pathlib import Path

import check_layout
import check_notes
import guide

ROOT = Path(__file__).resolve().parents[1]


def test_guide_prints_only_the_section(capsys):
    assert guide.main(["course", "4"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("### 4.") and "### 5." not in out
    full = (ROOT / "references" / "course.md").read_text(encoding="utf-8")
    assert len(out) < 0.6 * len(full)                      # 丸ごと読むより短い


def test_guide_lists_headings(capsys):
    assert guide.main(["skill"]) == 0
    assert "使用量を抑える進め方" in capsys.readouterr().out


def test_make_deck_builds_and_reports_briefly(built):
    w = built / "examples" / "course" / "_work" / "AI活用講座_01"
    r = subprocess.run([sys.executable, "-X", "utf8", str(built / "scripts" / "make_deck.py"), str(w), "--no-render"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("組んだ：") and len(r.stdout.splitlines()) <= 6
    import build_log
    assert len(build_log.load(w)) >= 1                     # 組むたびに記録が1行増える


def test_thin_body_is_flagged():
    W, H = 960, 540
    items = [{"slide": 1, "name": "TextBox 3", "text": "表面加熱 → 中心加熱に遅れ", "size": 20, "ph": None}]
    assert check_layout.content_chars(items) < check_layout.TEXT_MIN_CHARS
    items.append({"slide": 1, "name": "場合分け", "text": "熱板 120〜220℃：表面の焼き色。中心 55〜85℃：硬さと厚さ。厚さ 20 mm の牛肉で比べた研究。焼き色は約 140℃ から", "size": 18, "ph": None})
    assert check_layout.content_chars(items) >= check_layout.TEXT_MIN_CHARS   # 囲みの中の文字も数える


def test_short_notes_per_slide_are_flagged(tmp_path):
    plan = ("## 2. 話の順番\n\n| # | ●見出し | 青帯（結論） | 図で見せるもの | 役割 |\n|---|---|---|---|---|\n"
            "| 1 | 表紙 | — | — | 表紙 |\n| 2 | 熱の通り方 | 表面から熱が入る | 断面の図 | 本文 |\n")
    (tmp_path / "memo.md").write_text(plan, encoding="utf-8")
    (tmp_path / "notes.md").write_text("## 1\n始めます。\n\n## 2\n熱は表面から入ります。\n", encoding="utf-8")
    got = {item: m for m, item, _ in check_notes.check(tmp_path)}
    assert got.get("1枚あたりの原稿") == "△"


def test_build_log_counts_redone_slides(tmp_path):
    import json
    import build_log
    recs = [{"sig": ["a", "b", "c"], "error": 2, "x": 1},
            {"sig": ["a", "B", "c"], "error": 0, "x": 0},          # ここで検査が通る
            {"sig": ["a", "B", "C", "d"], "error": 0, "x": 0}]     # 完成後のレビューのあと 3枚目を直し 4枚目を足した
    (tmp_path / build_log.LOG).write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    s = build_log.summary(tmp_path)
    assert s["runs"] == 3 and s["since_first"] == [2, 3, 4] and s["clean_run"] == 2 and s["after_clean"] == [3, 4]
    assert "3/4" in build_log.line(tmp_path)


def test_check_output_folds_ok_lines(capsys):
    """検査の出力：✘・△ は1行ずつ、✔ は1行にまとめる（--all で全部）。"""
    import report
    res = [("✔", "枚数", "12枚"), ("△", "図", "2枚目が文だけ"), ("✔", "出典", "全部ある")]
    report.show(res)
    out = capsys.readouterr().out.splitlines()
    assert out == ["△ 図：2枚目が文だけ", "✔ 2項目：枚数・出典"]
    report.show(res, full=True)
    assert len(capsys.readouterr().out.splitlines()) == 3


def test_skill_md_points_to_tools_sections():
    """担当向けの節（道具・コマンドの書き方・PowerPoint の決まり）は references/tools.md に置き、SKILL.md は短く保つ。"""
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    tools = (ROOT / "references" / "tools.md").read_text(encoding="utf-8")
    assert "## コマンドの書き方" in tools and "## PowerPoint の決まり" in tools and "## コマンドの書き方" not in skill
    assert "guide.py tools" in skill and len(skill) < 10000


def test_ask_does_not_double_arrow():
    from zemi import Deck
    d = Deck()
    s = d.slide("T", summary="S")
    s.ask("本当か？", "⇒ 名前だけでは不十分")
    texts = [sh.text_frame.text for sh in s.slide.shapes if sh.has_text_frame and sh.name == "答え"]
    assert texts == ["⇒ 名前だけでは不十分"]


def test_arrow_with_negative_size_is_refused():
    """大きさがマイナスの矢印があると PowerPoint がファイルごと開けない（LibreOffice に代わり、検査の数値が変わる）。"""
    import pytest
    from zemi import Deck
    s = Deck().slide("T", summary="S")
    with pytest.raises(ValueError):
        s.flow(["A", "B", "C"], x=0.7, y=2, w=2.4, h=1.2, gap=0.12, direction="right")


def test_make_deck_stops_at_the_cap(tmp_path, capsys):
    """make_deck は仕上げ4回・レビュー後の直し2回で止まる（--over はユーザーが許したときだけ）。"""
    import json
    import os
    import time
    import make_deck
    (tmp_path / "build.py").write_text("", encoding="utf-8")
    log = tmp_path / "build_log.jsonl"
    log.write_text("\n".join(json.dumps({"t": "2026-11-08 10:00:0%d" % i, "sig": []}) for i in range(4)), encoding="utf-8")
    assert make_deck.main([str(tmp_path)]) == 1 and "上限" in capsys.readouterr().out
    rv = tmp_path / "review.md"
    rv.write_text("判定", encoding="utf-8")
    t = time.mktime(time.strptime("2026-11-08 10:00:05", "%Y-%m-%d %H:%M:%S"))
    os.utime(rv, (t, t))
    assert make_deck.run_budget(tmp_path) == ("完成後のレビューのあとの直し", 0, 2)


def test_libreoffice_gap_shift():
    import check_layout
    assert check_layout.LO_GAP_SHIFT >= 3.9   # 2つのデッキで実測した PowerPoint との差の最小


def test_role_launch_cap_and_option(tmp_path):
    """担当の起動は役ごとに上限（道具・モデルによらない）。依頼文の読み直しは数えない。オプションで多め・なし。"""
    import json
    import budget
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    assert budget.check_role(w, "仕上げ役") is None            # 1回目
    assert budget.check_role(w, "仕上げ役") is None            # 15分以内の読み直し
    log = w / budget.LOG
    rs = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    rs[-1]["ts"] -= 3600
    log.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rs) + "\n", encoding="utf-8")
    (w / "build.py").write_text("x", encoding="utf-8")         # 1回目の担当が働いた
    assert "上限" in budget.check_role(w, "仕上げ役")           # 2回目の起動は止まる
    assert budget.check_role(w, "仕上げ役", over=True) is None  # ユーザーが許したとき
    (w / "memo.md").write_text("## 1. この回のゴールと前提\n\n- 回数の上限：多め\n- 使用量の上限：15%\n", encoding="utf-8")
    assert budget.cap(w, 4) == 8 and budget.percent_limit(w) == 15
    (w / "memo.md").write_text("## 1. この回のゴールと前提\n\n- 回数の上限：なし\n", encoding="utf-8")
    assert budget.cap(w, 4) is None and budget.percent_limit(w) == budget.DEFAULT_PERCENT


def test_usage_by_window():
    """使用量は枠ごと（5時間・週・月）。同時に動く担当のずれた値を足しすぎない。リセットをまたいでも数える。"""
    import budget
    month = [(1, 43200, 10), (2, 43200, 12), (3, 43200, 11.5), (4, 43200, 15)]          # ずれた値が混じる
    five = [(1, 300, 70), (2, 300, 95), (3, 300, 5), (4, 300, 20)]                      # 途中で5時間の枠がリセット
    u = budget.used_by_window(month + five)
    assert u["月"] == 5 and u["5時間"] == 40
    assert budget.window_name(10080) == "週"


def test_percent_limits_per_window(tmp_path):
    import budget
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    assert budget.percent_limits(w) == budget.DEFAULT_PERCENTS
    (w / "memo.md").write_text("## 1. この回のゴールと前提\n\n- 使用量の上限：月10%・5時間80%・週なし\n", encoding="utf-8")
    assert budget.percent_limits(w) == {"5時間": 80.0, "週": None, "月": 10.0}


def test_token_caps_stop_and_resume(tmp_path):
    """トークンの上限は道具ごと。超えたら止まり、ユーザーの許可1回ごとに同じ量だけ足して再開できる。"""
    import budget
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    assert budget.token_caps(w) == budget.TOKEN_CAPS
    used = {"Codex": 2_600_000}
    assert "上限" in budget.check_tokens(w, used=used)
    budget.allow_tokens(w, "Codex")
    assert budget.check_tokens(w, used=used) is None          # 上限が 500万に
    assert "上限" in budget.check_tokens(w, used={"Codex": 5_100_000})
    (w / "memo.md").write_text("## 1. この回のゴールと前提\n\n- トークンの上限：Codex 100万・Claude Code なし\n", encoding="utf-8")
    caps = budget.token_caps(w)
    assert caps["Codex"] == 1_000_000 and caps["Claude Code"] is None and caps["Antigravity"] == budget.TOKEN_CAPS["Antigravity"]
    assert budget.weighted({"input": 10, "cache_write": 5, "cache_read": 100, "output": 3}) == 28


def test_idle_launch_is_not_counted(tmp_path):
    """メインが依頼文を確かめただけ・起動が途中で止まった（作業フォルダに何も書かれていない）なら、次の起動と同じ1回とみなす。"""
    import json
    import time
    import budget
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    (w / "memo.md").write_text("x", encoding="utf-8")
    old = time.time() - 7200
    import os
    os.utime(w / "memo.md", (old, old))
    (w / budget.LOG).write_text(json.dumps({"t": "", "ts": old + 10, "role": "仕上げの直しの担当", "part": ""}) + "\n", encoding="utf-8")
    assert budget.record(w, "仕上げの直しの担当") is False          # 2時間あいても、何も書かれていなければ同じ1回
    (w / "build.py").write_text("x", encoding="utf-8")              # 担当が働いたあとなら数える
    assert budget.record(w, "仕上げの直しの担当") is True


def test_post_review_runs_survive_review_edit(tmp_path):
    """直しの担当が review.md に書き足しても、レビューのあとの make_deck の回数が数え直しにならない。"""
    import json
    import time
    import budget
    import make_deck
    t0 = time.time() - 600
    (tmp_path / budget.LOG).write_text(json.dumps({"t": "", "ts": t0, "role": "完成後のレビュー担当", "part": ""}) + "\n", encoding="utf-8")
    fmt = lambda s: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s))   # noqa: E731
    (tmp_path / "build_log.jsonl").write_text("\n".join(json.dumps({"t": fmt(t), "sig": []}) for t in (t0 - 60, t0 + 60, t0 + 120)), encoding="utf-8")
    (tmp_path / "review.md").write_text("判定\n## 採否と直した点\n", encoding="utf-8")   # 今書き足した
    assert make_deck.run_budget(tmp_path)[:2] == ("完成後のレビューのあとの直し", 2)


def test_final_check_run_is_free_once(tmp_path, capsys):
    """上限のあと、確かめるだけの1回（--final）は数えない。段階ごとに1回だけ。"""
    import json
    import make_deck
    (tmp_path / "build.py").write_text("", encoding="utf-8")
    recs = [{"t": "2026-11-08 10:00:0%d" % i, "sig": []} for i in range(4)]
    (tmp_path / "build_log.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    assert make_deck.run_budget(tmp_path)[1] == 4 and not make_deck.final_used(tmp_path, "仕上げ")
    recs.append({"t": "2026-11-08 10:00:09", "sig": [], "final": True})
    (tmp_path / "build_log.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    assert make_deck.run_budget(tmp_path)[1] == 4 and make_deck.final_used(tmp_path, "仕上げ")
    assert make_deck.main([str(tmp_path), "--final"]) == 1 and "1回だけ" in capsys.readouterr().out


def test_role_token_caps(tmp_path, monkeypatch):
    """担当ごとのトークンの上限：役を依頼文の頭で見分け、段（大・中・小）の割合で止める。許可で1回分増える。"""
    import budget
    import run_record
    w = tmp_path / "_work" / "試し_01"
    w.mkdir(parents=True)
    conv = tmp_path / "agent-abc.jsonl"
    conv.write_text('{"x": "あなたは sensei-slides スキルの「仕上げ役」です（講座）"}\n', encoding="utf-8")
    assert run_record.role_of(conv) == "仕上げ役"
    row = {"tool": "Codex", "kind": "担当", "name": "/root/finish", "file": str(conv), "role": "仕上げ役",
           "input": 100_000, "cache_read": 5_000_000, "cache_write": 0, "output": 50_000}   # 約65万 ＞ 250万×25%
    over = budget.role_over(w, [row])
    assert over and over[0][0] == "仕上げ役" and round(over[0][5]) == 625_000
    assert "--allow-role agent-abc" in budget.role_message(over)
    budget.allow_role_tokens(w, "agent-abc")
    assert budget.role_over(w, [row]) == []                                  # 許可で上限が1回分増える
    small = dict(row, role="数字を探す担当", file=str(tmp_path / "other.jsonl"))
    assert budget.role_over(w, [small])[0][1] == "小"                        # 小の段（250万×8%）
    main = dict(row, kind="メイン", role=None)
    assert budget.role_over(w, [main]) == []                                 # メインは全体の上限だけで見る


def test_solo_main_is_stopped(tmp_path):
    """担当を起動せずに（brief.py を通らずに）メインが作っていたら止める。見本や _work の外は見ない。"""
    import budget
    w = tmp_path / "_work" / "試し_01"
    w.mkdir(parents=True)
    (w / "memo.md").write_text("## 1. ゴール\n", encoding="utf-8")
    assert budget.solo_problem(w).startswith("✘ 担当を1人も起動していない")
    budget.record(w, "設計の担当")
    assert budget.solo_problem(w) is None
    assert "仕上げ役" in budget.solo_problem(w, "仕上げ役|仕上げの直しの担当")   # 仕上げの段で、仕上げ役の依頼文を受け取っていない
    budget.record(w, "仕上げ役")
    assert budget.solo_problem(w, "仕上げ役|仕上げの直しの担当") is None
    other = tmp_path / "examples" / "zemi"
    other.mkdir(parents=True)
    (other / "outline.md").write_text("## 構成\n", encoding="utf-8")
    assert budget.solo_problem(other) is None                              # _work の外（見本など）は見ない

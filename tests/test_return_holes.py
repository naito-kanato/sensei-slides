"""推論距離の担当が設計の担当に戻す穴（review の「## 設計に戻す穴」）。next_step が節を読んで案内する。"""
import os
import time

import next_step


def write(p, text, t):
    p.write_text(text, encoding="utf-8")
    os.utime(p, (t, t))


def test_holes_are_read_until_the_plan_is_newer(tmp_path):
    review, plan = tmp_path / "memo_review.md", tmp_path / "memo.md"
    now = time.time()
    write(plan, "# 設計メモ", now - 100)
    write(review, "## 推論距離\n\n- [3] ...\n\n## 設計に戻す穴\n\n- [5] 事実：揚力の式の係数\n- [8] 筋：答えの枚の前に1枚\n", now - 50)
    assert len(next_step.returned_holes(review, plan)) == 2
    write(plan, "# 設計メモ（直した）", now)                      # 設計の担当が直した
    assert next_step.returned_holes(review, plan) == []
    assert len(next_step.returned_holes(review, plan, pending=False)) == 2   # 戻した回だったこと（✘ の行き先）は残る


def test_no_section_or_none_means_no_holes(tmp_path):
    review, plan = tmp_path / "memo_review.md", tmp_path / "memo.md"
    write(plan, "x", time.time())
    write(review, "## 推論距離\n\n- [3] ...\n", time.time())
    assert next_step.returned_holes(review, plan) == []
    write(review, "## 推論距離\n\n## 設計に戻す穴\n\n- なし\n", time.time())
    assert next_step.returned_holes(review, plan) == []

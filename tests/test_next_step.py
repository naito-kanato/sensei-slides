"""next_step.py：作業フォルダのファイルから、済んだ手順と次の手順を決める。"""
import next_step


def test_empty_work_folder_starts_with_the_outline(tmp_path):
    w = tmp_path / "_work" / "論文"
    w.mkdir(parents=True)
    steps, nxt = next_step.steps_for(w)
    assert "軽量の設計の担当" in nxt   # 既定（軽さ：標準）は担当2人
    import budget
    budget.set_lightness(w, "念入り")   # 念入りを選んだ回は、構成案から
    steps, nxt = next_step.steps_for(w)
    assert nxt.startswith("手順2")


def test_course_folder_points_to_the_first_memo(tmp_path):
    c = tmp_path / "焼き肉講座"
    c.mkdir()
    (c / "00_README.md").write_text("# 焼き肉講座\n\n## 全体の地図\n", encoding="utf-8")
    lines, nxt = next_step.course_next(c)
    assert "第1回" in nxt and "_work/焼き肉講座_01/memo.md" in nxt
    assert "地図に OK" in nxt   # 回数が分からない（全2回以上かもしれない）講座は、地図を見せる
    one = tmp_path / "一回" / "焼き肉講座"
    one.mkdir(parents=True)
    (one / "00_README.md").write_text("# 焼き肉講座（全1回）\n\n## 全体の地図\n\n| 回 | 題 |\n|---|---|\n| 1 | はじめに |\n", encoding="utf-8")
    _, nxt = next_step.course_next(one)
    assert "地図はユーザーに見せずに進む" in nxt and "地図に OK" not in nxt   # 全1回の講座は、地図を見せない


def test_example_course_reports_each_step(built):
    w = built / "examples" / "course" / "_work" / "AI活用講座_01"
    steps, nxt = next_step.steps_for(w)
    names = [s for _, s, _ in steps]
    assert any("設計メモの確認" in n for n in names) and any("スライド" in n for n in names)
    assert nxt.startswith(("手順5", "手順5b", "手順6", "手順7"))   # 組み終えたあと：描画・レビュー・原稿のページ・渡す前の確認のどれか


def test_old_title_deck_is_not_a_new_lesson(tmp_path):
    """題名を変える前の古い版の pptx が残っていても、作った回は1つと数える。一式が別の _work の下にあっても見つける。"""
    root = tmp_path / "_work" / "試し"
    c = root / "焼き肉講座"
    c.mkdir(parents=True)
    (c / "00_README.md").write_text("# 焼き肉講座\n\n## 全体の地図\n", encoding="utf-8")
    for name in ("01_古い題名_スライド.pptx", "01_新しい題名_スライド.pptx"):
        (c / name).write_bytes(b"")
    w = root / "_work" / "焼き肉講座_01"
    w.mkdir(parents=True)
    lines, nxt = next_step.course_next(c)
    assert "第2回" in nxt and "作った回 1" in lines[0]


def test_course_lesson_starts_with_finding_numbers(tmp_path):
    """講座の回は、数字を探す担当 → 設計の担当の順（設計メモはデータを見てから）。"""
    w = tmp_path / "_work" / "焼き肉講座_01"
    w.mkdir(parents=True)
    import budget
    budget.set_lightness(w, "念入り")   # 念入りの回の流れ（既定の標準は、設計の担当が数字も探す）
    _, nxt = next_step.steps_for(w)
    assert "数字を探す担当" in nxt
    (w / "data_1.md").write_text("## データ：x\n", encoding="utf-8")
    _, nxt = next_step.steps_for(w)
    assert "設計の担当" in nxt
    c = tmp_path / "別" / "焼き肉講座"   # まだ回の作業フォルダが無い講座
    c.mkdir(parents=True)
    (c / "00_README.md").write_text("# 焼き肉講座\n\n## 学習者とゴール\n\n- 軽さ：念入り\n\n## 全体の地図\n", encoding="utf-8")
    assert "数字を探す担当" in next_step.course_next(c)[1]


def test_presentation_without_data_goes_back_only_before_build(tmp_path, root):
    """発表：data_1.md が無ければ構成案の段では ✘ で手順2へ。組み始めたあと（build.py がある）は戻さない。"""
    import re
    import shutil
    w = tmp_path / "_work" / "ゼミ"
    w.mkdir(parents=True)
    for f in ("outline.md", "outline_review.md"):
        shutil.copy(root / "examples" / "zemi" / f, w / f)
    p = w / "outline.md"
    p.write_text(re.sub(r"## 3b\. データ.*?(?=^## )", "", p.read_text(encoding="utf-8"), flags=re.S | re.M), encoding="utf-8")
    _, nxt = next_step.steps_for(w)
    assert nxt.startswith("手順2") and "check_outline" in nxt
    (w / "build.py").write_text("", encoding="utf-8")
    _, nxt = next_step.steps_for(w)
    assert not nxt.startswith("手順2")


def test_final_review_asking_for_fixes_comes_before_check_done(tmp_path):
    import os
    import next_step
    review, pptx = tmp_path / "review.md", tmp_path / "x_スライド.pptx"
    pptx.write_bytes(b"x")
    review.write_text("- 判定: 「直してから渡す」\n", encoding="utf-8")
    t = pptx.stat().st_mtime
    os.utime(review, (t + 5, t + 5))
    assert next_step.needs_final_fix(review, pptx)            # レビューのあと作り直していない
    os.utime(pptx, (t + 10, t + 10))
    assert not next_step.needs_final_fix(review, pptx)        # 直したあと
    review.write_text("- 判定: 「このまま渡してよい」\n", encoding="utf-8")
    os.utime(review, (t + 20, t + 20))
    assert not next_step.needs_final_fix(review, pptx)
    # 組み直したあとに review.md へ採否を書き足しても、直し済み（英語の試しで、手順9から進まなかった）
    review.write_text("- 判定: 直してから渡す\n\n## 採否と直した点\n\n- 必ず直す点 1〜4：全部採った\n", encoding="utf-8")
    os.utime(review, (t + 30, t + 30))
    assert not next_step.needs_final_fix(review, pptx)
    review.write_text("- 判定: 直してから渡す\n\n## 採否と直した点\n\n", encoding="utf-8")   # 見出しだけで中身が無いのは、まだ
    os.utime(review, (t + 40, t + 40))
    assert next_step.needs_final_fix(review, pptx)


def test_start_gives_the_main_everything_once(capsys):
    """メインが最初に1回：道具の読み替え・最初の質問・設定の一覧・次の1手（guide.py agents・course 1・slide_profile を別に呼ばない）。"""
    assert next_step.main(["--start", "講座", "--set", "聞き手のテーマへの詳しさ=初学者"]) == 0
    out = capsys.readouterr().out
    assert "Claude Code：" in out and "sensei-slides-worker" in out
    assert "① 詳しさ" in out and "| 聞き手のテーマへの詳しさ | 初学者 |" in out
    assert "brief.py 地図の担当" in out and "sleep" in out
    assert len(out.encode("utf-8")) < 27000
    assert next_step.main(["--start", "発表"]) == 0
    assert "brief.py 軽量の設計の担当" in capsys.readouterr().out


def test_course_folder_gives_the_lesson_step_when_in_progress(tmp_path, monkeypatch):
    """途中の回があれば、講座フォルダの next_step がその回の次の1手まで出す（メインがもう1回呼ばずに済む）。"""
    monkeypatch.chdir(tmp_path)
    c = tmp_path / "焼き肉講座"
    c.mkdir()
    (c / "00_README.md").write_text("# 焼き肉講座（全1回）\n\n## 全体の地図\n\n| 回 | 題 |\n|---|---|\n| 1 | はじめに |\n", encoding="utf-8")
    (tmp_path / "_work" / "焼き肉講座_01").mkdir(parents=True)
    _, nxt = next_step.course_next(c)
    assert nxt.startswith("焼き肉講座_01 の途中：") and "軽量の設計の担当" in nxt and "_work/焼き肉講座_01" in nxt

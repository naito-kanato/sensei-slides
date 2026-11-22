"""next_step.py：作業フォルダのファイルから、済んだ手順と次の手順を決める。"""
import next_step


def test_empty_work_folder_starts_with_the_outline(tmp_path):
    w = tmp_path / "_work" / "論文"
    w.mkdir(parents=True)
    steps, nxt = next_step.steps_for(w)
    assert "軽量の設計の担当" in nxt   # 講座も発表も担当2人
    import json
    import budget
    assert budget.careful_note(w) is None
    (w / budget.LOG).write_text(json.dumps({"t": "", "ts": 0, "type": "set_lightness", "value": "念入り"}, ensure_ascii=False) + "\n",
                                encoding="utf-8")   # 前の版で念入りを記録した作業フォルダ：標準として読み、1行知らせる
    steps, nxt = next_step.steps_for(w)
    assert "軽量の設計の担当" in nxt and "念入りは無くなった" in budget.careful_note(w)
    assert budget.main([str(w), "--set-lightness", "念入り"]) == 0 and budget.light(w)


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


def test_example_course_reports_each_step(built, tmp_path):
    import shutil
    shutil.copytree(built / "examples" / "course", tmp_path / "course")
    readme = tmp_path / "course" / "AI活用講座" / "00_README.md"   # 前の版で念入りにした講座も、担当2人の手順の一覧で見る
    readme.write_text(readme.read_text(encoding="utf-8").replace("- 軽さ：標準", "- 軽さ：念入り"), encoding="utf-8")
    w = tmp_path / "course" / "_work" / "AI活用講座_01"
    steps, nxt = next_step.steps_for(w)
    names = [s for _, s, _ in steps]
    assert any("設計（軽量）" in n for n in names) and any("制作（軽量）" in n for n in names)
    import budget
    assert budget.careful_note(w) and budget.careful_note(readme.parent)


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


def test_course_lesson_starts_with_the_light_designer(tmp_path):
    """講座の回は、軽量の設計の担当が数字も探す（前の版で念入りにした講座も同じ）。"""
    w = tmp_path / "_work" / "焼き肉講座_01"
    w.mkdir(parents=True)
    _, nxt = next_step.steps_for(w)
    assert "軽量の設計の担当" in nxt and "数字を探す担当" not in nxt
    c = tmp_path / "別" / "焼き肉講座"   # まだ回の作業フォルダが無い講座
    c.mkdir(parents=True)
    (c / "00_README.md").write_text("# 焼き肉講座\n\n## 学習者とゴール\n\n- 軽さ：念入り\n\n## 全体の地図\n", encoding="utf-8")
    nxt = next_step.course_next(c)[1]
    assert "軽量の設計の担当" in nxt and "数字を探す担当" not in nxt


def test_presentation_without_data_goes_back_to_the_designer(tmp_path, root):
    """発表：data_1.md が無ければ、設計の担当に続けて頼む（前の版で念入りにした構成案も同じ）。"""
    import re
    import shutil
    w = tmp_path / "_work" / "ゼミ"
    w.mkdir(parents=True)
    for f in ("outline.md", "outline_review.md"):
        shutil.copy(root / "examples" / "zemi" / f, w / f)
    p = w / "outline.md"
    p.write_text(re.sub(r"## 3b\. データ.*?(?=^## )", "", p.read_text(encoding="utf-8"), flags=re.S | re.M)
                 .replace("| 軽さ | 標準 |", "| 軽さ | 念入り |"), encoding="utf-8")   # 前の版の念入りの構成案
    _, nxt = next_step.steps_for(w)
    assert "data_1.md" in nxt and "軽量の設計の担当を新しく起動" in nxt   # 念入りの作業フォルダには、まだ軽量の設計の担当がいない
    import brief
    brief.build("軽量の設計の担当", str(w), kind="発表", count=True)   # 起動を記録する
    _, nxt = next_step.steps_for(w)
    assert "data_1.md" in nxt and "設計の担当に続けて頼む" in nxt


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

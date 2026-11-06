"""next_step.py：作業フォルダのファイルから、済んだ手順と次の手順を決める。"""
import next_step


def test_empty_work_folder_starts_with_the_outline(tmp_path):
    w = tmp_path / "_work" / "論文"
    w.mkdir(parents=True)
    steps, nxt = next_step.steps_for(w)
    assert nxt.startswith("手順2")


def test_course_folder_points_to_the_first_memo(tmp_path):
    c = tmp_path / "焼き肉講座"
    c.mkdir()
    (c / "00_README.md").write_text("# 焼き肉講座\n\n## 全体の地図\n", encoding="utf-8")
    lines, nxt = next_step.course_next(c)
    assert "第1回" in nxt and "_work/焼き肉講座_01/memo.md" in nxt


def test_example_course_reports_each_step(built):
    w = built / "examples" / "course" / "_work" / "AI活用講座_01"
    steps, nxt = next_step.steps_for(w)
    names = [s for _, s, _ in steps]
    assert any("設計メモの確認" in n for n in names) and any("スライド" in n for n in names)
    assert nxt.startswith(("手順5", "手順5b", "手順6", "手順7"))   # 組み終えたあと：描画・レビュー・原稿のページ・渡す前の確認のどれか

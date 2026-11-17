"""オプション「軽さ：軽量」：担当2人（設計・制作）で作る流れ。"""
from pathlib import Path

import brief
import budget
import next_step


def _course(tmp_path, light=True):
    (tmp_path / "X講座").mkdir()
    (tmp_path / "X講座" / "00_README.md").write_text(
        "# X講座\n\n## 学習者とゴール\n\n- 学習者：初学者\n" + ("- 軽さ：軽量\n" if light else "") + "\n## 地図\n\n| 回 | 題 |\n|---|---|\n| 1 | はじめに |\n",
        encoding="utf-8")
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    return w


def test_light_is_read_from_the_course_readme(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    assert budget.light(_course(a))
    assert not budget.light(_course(b, light=False))


def test_next_step_sends_the_light_design_role_first(tmp_path):
    w = _course(tmp_path)
    _, nxt = next_step.steps_for(w)
    assert "軽量の設計の担当" in nxt and "数字を探す" not in nxt.split("：")[0]


def test_light_briefs_are_whole(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    w = _course(tmp_path)
    (w / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    d = brief.build("軽量の設計の担当", str(w), count=False)
    own = d.split("\n---\n# 手順書の節")[0]
    assert "{" not in own and "[講座]" not in own and "[節]" not in own
    assert "① **数字**" in d and "facts.py split はしない" in d and "split --n" not in d
    assert "4a. 流れと設計メモの中身" in d                     # 設計の担当と同じ節を写す
    m = brief.build("軽量の制作の担当", str(w), count=False)
    assert "scaffold.py" in m and "--try all" in m and "3回まで" in m and "## 5. 描画して確認する" in m


def test_light_make_deck_cap(tmp_path):
    import make_deck
    w = _course(tmp_path)
    (w / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    assert make_deck.run_budget(w)[2] == budget.LIGHT_MAKE_DECK

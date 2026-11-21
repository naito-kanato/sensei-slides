"""依頼文に手順書の節を写す（brief.py の [節] の行）。担当が guide.py を呼ぶ回数を減らす。"""
import re
from pathlib import Path

import brief
import guide

ROOT = Path(__file__).resolve().parents[1]


def test_every_embed_line_points_to_a_section():
    """雛形の [節] の行が指す節が、どれも手順書にある（節の名前を変えたときに切れないように）。"""
    bad = []
    for f in sorted((ROOT / "assets" / "briefs").glob("*.md")):
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^(?:\[発表\]|\[講座\])?\[節\](.*)$", line)
            if not m:
                continue
            for grp in m.group(1).split("／"):
                w = grp.split()
                for k in w[1:]:
                    if guide.section(w[0], k) is None:
                        bad.append(f"{f.name}: {w[0]} {k}")
    assert not bad, bad


def _work(tmp_path, kind):
    w = tmp_path / "_work" / ("X講座_01" if kind == "講座" else "論文")
    w.mkdir(parents=True)
    if kind == "講座":
        (w / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    return w


def test_finishing_brief_carries_the_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    t = brief.build("仕上げ役", str(_work(tmp_path, "講座")), count=False)
    assert "# 手順書の節" in t and "## 5. 描画して確認する" in t and "## 6. 原稿HTMLを作る" in t
    assert "[節]" not in t
    assert t.rstrip().endswith("10行までで返す。")   # 締めの一言は写した節のあと


def test_design_brief_carries_its_kind_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    course = brief.build("設計の担当", str(_work(tmp_path, "講座")), count=False)
    talk = brief.build("設計の担当", str(_work(tmp_path, "発表")), kind="発表", count=False)
    assert "4a. 設計メモの中身" in course and "4a. 設計メモの中身" not in talk
    assert "## 1. 筋の表" in course and "## 1. 筋の表" in talk
    assert course.count("## 1b. 図の種類の選び方") == 1


def test_first_design_role_makes_the_work_folder(tmp_path, monkeypatch):
    # 地図の担当は作業フォルダを作らない。回の最初の担当（設計）が、無ければ作ってから回数を数える
    monkeypatch.chdir(tmp_path)
    (tmp_path / "テスト講座").mkdir()
    for role in ("軽量の設計の担当", "設計の担当"):
        work = tmp_path / "_work" / f"テスト講座_0{1 if role == '設計の担当' else 2}"
        t = brief.build(role, str(work), count=True)
        assert work.is_dir() and t

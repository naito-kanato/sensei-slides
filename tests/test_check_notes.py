"""読み上げ原稿の確認（check_notes.py）：手当てで原稿に回した中身・1文の長さ・中身の無いつなぎ・発表時間との釣り合い。"""
import check_notes

PLAN = """## オプション

| 項目 | 値 |
|---|---|
| 発表時間 | {mins}分 |

## 引っかかりへの手当て

- [2] 用語の穴「四重極モーメント」→ 原稿で「質量の分布、正確には四重極モーメントが時間とともに変わる」と、先に平易な言い方を置く
- [3] 用語の穴「SN 比」→ 初出の本文に括弧で「（信号と雑音の比）」
- [4] 論理の穴「周波数の上昇 ⇒ 合体」→ 原稿で「2つの天体が重力波を出しながら近づく」と1文
"""


def _work(tmp_path, notes, mins=1):
    (tmp_path / "outline.md").write_text(PLAN.format(mins=mins), encoding="utf-8")
    (tmp_path / "notes.md").write_text(notes, encoding="utf-8")
    return tmp_path


def marks(res):
    return {item: m for m, item, _ in res}


def test_care_items_take_only_lines_sent_to_the_notes():
    items = {n: (say, terms) for n, say, terms, _ in check_notes.care_items(PLAN.format(mins=1))}
    assert set(items) == {2, 4}                       # [3] は本文での手当て
    assert items[2] == (["質量の分布、正確には四重極モーメントが時間とともに変わる"], ["四重極モーメント"])


def test_paraphrased_care_passes_and_missing_care_fails(tmp_path):
    ok = ("## 2\n質量の分布、正確には四重極モーメントと呼ぶ量が、時間とともに変わると生まれます。\n\n"
          "## 4\n2つの天体が重力波を出しながら、互いに近づいていきます。\n")
    assert marks(check_notes.check(_work(tmp_path, ok)))["原稿の手当て"] == "✔"
    bad = "## 2\n重力波は時空のひずみです。\n\n## 4\n周波数が上がります。\n"
    res = check_notes.check(_work(tmp_path, bad))
    assert marks(res)["原稿の手当て"] == "✘"
    msg = next(m for mk, i, m in res if i == "原稿の手当て")
    assert "[2]" in msg and "[4]" in msg


def test_long_sentence_and_empty_link_are_flagged(tmp_path):
    long = "あ" * 95 + "。"
    notes = f"## 2\n四重極モーメントが時間とともに変わる質量の分布です。{long}\n\n## 4\n2つの天体が重力波を出しながら近づきます。では次に。\n"
    got = marks(check_notes.check(_work(tmp_path, notes)))
    assert got["原稿の1文の長さ"] == "△" and got["原稿のつなぎ"] == "△"


def test_length_is_compared_with_the_talk_time(tmp_path):
    notes = "## 2\n四重極モーメントが時間とともに変わる質量の分布です。\n\n## 4\n2つの天体が重力波を出しながら近づきます。\n"
    assert marks(check_notes.check(_work(tmp_path, notes, mins=20)))["原稿の長さ"] == "△"   # 20分に数十字は少なすぎる

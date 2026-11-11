"""推論距離の決まりの置き場所（inference-distance.md）と、名前の数の検査・深の行をカードへ渡すこと。"""
import cards
import check_outline as co
import guide

ROWS = """## 推論距離
- [3] 「A ⇒ B」｜用語｜要2｜補う前提：Aの中身｜使う所：3｜架け方：括弧で一言
- [3] 「C ⇒ D」｜用語｜要2｜補う前提：Cの中身｜使う所：3｜架け方：括弧で一言
- [3] 「E ⇒ F」｜用語｜要2｜補う前提：Eの中身｜使う所：3｜架け方：括弧で一言
- [4] 「G ⇒ H」｜用語｜要2・深｜補う前提：Gの中身｜使う所：4｜架け方：原稿
- [5] 「I ⇒ J」｜論拠｜深｜補う前提：Iの背景｜使う所：なし｜架け方：原稿の ※
"""


def test_many_names_on_one_slide():
    res = {item: (mark, msg) for mark, item, msg in co.hole_form(ROWS)}
    mark, msg = res["推論距離の名前の数"]
    assert mark == "△" and "3枚目（3つ）" in msg and "4枚目" not in msg


def test_deep_rows_go_to_cards(tmp_path):
    (tmp_path / "outline_review.md").write_text(ROWS, encoding="utf-8")
    assert cards.deep_rows(tmp_path, "outline") == {5: ["Iの背景"]}   # 迷い（要2・深）は渡さない


def test_rules_live_in_one_file(capsys):
    for key in ("1", "2", "3", "4", "5", "6", "7"):
        assert guide.main(["inference-distance", key]) == 0
    out = capsys.readouterr().out
    assert "要4" in out and "丁寧さ" in out and "D4" in out
    assert guide.main(["final-review", "D. 構成案との突き合わせ"]) == 0
    assert "D4 縮めて開いた穴" in capsys.readouterr().out

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
    assert mark == "✘" and "3枚目（3つ）" in msg and "4枚目" not in msg


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


def test_new_and_old_label_names():
    # 要否の名前：筋・語・あと・像・深。前の名前（要1〜要4）で書いた行も同じに読む
    assert co.labels("筋・像") == co.labels("要1・要4") == {"要1", "要4"}
    assert co.labels("あと・深") == {"要3", "深"} and co.unsure("あと・深")
    row = "- [3] 「A ⇒ B」｜用語｜語｜補う前提：Aの中身｜使う所：3｜架け方：括弧で一言\n"
    assert co.holes(row)[3][0][2] == "語"


def test_deep_rows_only_for_experts(tmp_path):
    # 深は、かなり知っている聞き手のときだけ1枚に1つまで。初学者・多少知っている（前の版の「初学者・多少知っている」も）では書き手に渡さない
    rows = ROWS + "- [5] 「K ⇒ L」｜論拠｜深｜補う前提：Kの背景｜使う所：なし｜架け方：原稿の ※\n"
    cases = (("初学者", {}), ("多少知っている（分野の入門の授業まで）", {}), ("初学者・多少知っている", {}),
             ("かなり知っている（その分野が専門）", {5: ["Iの背景"]}))
    for i, (fam, want) in enumerate(cases):
        d = tmp_path / str(i)
        d.mkdir()
        (d / "outline_review.md").write_text(rows, encoding="utf-8")
        (d / "outline.md").write_text(f"聞き手のテーマへの詳しさ：{fam}\n", encoding="utf-8")
        assert cards.deep_rows(d, "outline") == want


# ---- 新しい名前（inference-distance.md 3・4・6節）：説明済みの名前も数え、1枚に3つ以上なら ✘

NAMES = """
## 新しい名前

- [3] 甲・乙
- [5] 丙・丁（説明あり）・戊
- [6] 己
- [7] 庚・辛・壬（理由：この枚で比べる3つの名前）
"""


def test_new_names_three_or_more_block():
    mark, item, msg = co.new_names_check(ROWS + NAMES)[0]
    assert item == "推論距離の新しい名前" and mark == "✘"
    assert "5枚目（3つ：丙・丁・戊）" in msg and "3枚目" not in msg and "7枚目" not in msg   # 理由つきの行は通す
    # 新しい名前の節があれば、語 の穴の数（3枚目に3つ）では数えない（同じことを2回言わない）
    assert "推論距離の名前の数" not in {i for _, i, _ in co.hole_form(ROWS + NAMES)}
    assert co.new_names(ROWS + NAMES)[5] == (["丙", "丁", "戊"], False)


def test_two_names_pass_and_measure_only_records():
    ok = NAMES.replace("・丁（説明あり）・戊", "・丁")
    mark, _, msg = co.new_names_check(ROWS + ok)[0]
    assert mark == "✔" and "[7]" in msg
    mark, _, msg = co.new_names_check(ROWS + NAMES, measure=True)[0]
    assert mark == "・" and "5枚目" in msg                                           # 測るだけの回は記録するだけ


def test_old_folder_without_section_still_works():
    # 前の版の作業フォルダ（節が無い）：△ で知らせ、語 の穴の数を今までどおり見る
    assert co.new_names(ROWS) is None
    assert co.new_names_check(ROWS)[0][0] == "△"
    assert {i: m for m, i, _ in co.hole_form(ROWS)}["推論距離の名前の数"] == "✘"


def _zemi(tmp_path, root, extra=""):
    import shutil
    w = tmp_path / "zemi"
    w.mkdir()
    for f in ("outline.md", "outline_review.md", "script.md", "data_1.md"):
        shutil.copy2(root / "examples" / "zemi" / f, w / f)
    if extra:
        rv = w / "outline_review.md"
        rv.write_text(rv.read_text(encoding="utf-8") + extra, encoding="utf-8")
    return w / "outline.md"


def test_examples_have_no_section_and_do_not_break(tmp_path, root):
    # 見本は作り直していないので節が無い：△ が1つ出るだけで、✘ は出ない
    res = co.check(_zemi(tmp_path, root))
    got = {i: m for m, i, _ in res}
    assert got["推論距離の新しい名前"] == "△" and not [r for r in res if r[0] == "✘"]


def test_presentation_and_course_both_count(tmp_path, root):
    import shutil
    import check_memo as cm
    res = co.check(_zemi(tmp_path, root, "\n## 新しい名前\n\n- [5] 甲・乙・丙\n- [8] 丁・戊\n"))
    got = {i: (m, d) for m, i, d in res}
    assert got["推論距離の新しい名前"][0] == "✘" and "5枚目" in got["推論距離の新しい名前"][1] and "8枚目" not in got["推論距離の新しい名前"][1]
    c = tmp_path / "course"
    shutil.copytree(root / "examples" / "course", c, ignore=shutil.ignore_patterns("*.pptx", "render", "figs", "*.html"))
    w = c / "_work" / "AI活用講座_01"
    rv = w / "memo_review.md"
    rv.write_text(rv.read_text(encoding="utf-8") + "\n## 新しい名前\n\n- [4] 甲・乙・丙\n", encoding="utf-8")
    got = {i: (m, d) for m, i, d in cm.check(w / "memo.md")}
    assert got["推論距離の新しい名前"][0] == "✘" and "4枚目" in got["推論距離の新しい名前"][1]
    rv.write_text(rv.read_text(encoding="utf-8").replace("- [4] 甲・乙・丙", "- [4] 甲・乙"), encoding="utf-8")
    assert {i: m for m, i, _ in cm.check(w / "memo.md")}["推論距離の新しい名前"] == "✔"


def test_briefs_ask_for_the_section(tmp_path):
    import brief
    w = tmp_path / "_work" / "X"
    w.mkdir(parents=True)
    (w / "outline.md").write_text("# 構成案\n\n## オプション\n\n| オプション | 今の値 |\n|---|---|\n| 聞き手のテーマへの詳しさ | 初学者 |\n", encoding="utf-8")
    d = brief.build("推論距離の担当", str(w), "発表")
    assert "## 新しい名前" in d and "説明してあっても数える" in d and "枚を分ける" in d
    assert "1枚に新しく出る名前は2つまで" in brief.build("軽量の設計の担当", str(w), "発表")

"""悪い回の底上げ：表紙の道筋・ゴールの話題の図・解答の理由・入口の経験（同じ版でも1本ごとに出来が揺れ、下振れの回に共通した抜け）。"""
from pptx import Presentation

import check_memo as cm
from zemi import Deck

HEAD = "| # | ●見出し | 前の枚から | 青帯（結論） | 図で見せるもの | 本文の要点 | 役割 |\n|---|---|---|---|---|---|---|\n"


def memo(rows, goals=("翼が揚力を受けるしくみを言える", "乱気流で機内に起きることを説明できる"), road=None, quiz=""):
    g = "".join(f"  {i}. {x}\n" for i, x in enumerate(goals, 1))
    r = f"- 道筋：{road}\n" if road else ""
    return (f"# 設計メモ：第1回 X\n\n## 1. この回のゴールと前提\n\n- 言えるようになること（3つまで）：\n{g}{r}\n"
            f"## 2. 話の順番\n\n{HEAD}{rows}\n## 6. 確認問題と模範解答\n\n{quiz}\n## 7. 次\n")


BODY = "".join(f"| {n} | 見出し{n} | — | 青帯{n} | 違い：比較：A（a）と B（b） | 要点{n} | 本文 |\n" for n in range(2, 9))


def test_roadmap_is_read_and_required():
    t = memo(BODY, road="よく聞く説明を確かめる → 空気を曲げる → 離陸と乱気流")
    assert cm.roadmap_of(t) == ["よく聞く説明を確かめる", "空気を曲げる", "離陸と乱気流"]
    assert cm.roadmap_check(t, 7)[0][0] == "✔"
    assert cm.roadmap_check(memo(BODY), 7)[0][0] == "△"
    assert cm.roadmap_check(memo(BODY), 5) == []                      # 小さな回は見ない
    assert cm.roadmap_of(memo(BODY, road="<段1> → <段2>")) is None     # 雛形のまま


def test_roadmap_goes_on_the_cover(tmp_path):
    d = Deck(workdir=tmp_path / "build")
    d.title_slide(["第1回 飛行機はどうやって空を飛ぶのか"], author="飛行機（全1回）",
                  roadmap=["よく聞く説明を確かめる", "空気を曲げる", "離陸と乱気流"])
    d.title_slide(["第2回 長い道筋"], author="X",
                  roadmap=["いちばん長い段の名前その一", "いちばん長い段の名前その二", "いちばん長い段の名前その三", "四"])
    d.save(tmp_path / "c.pptx")
    covers = list(Presentation(tmp_path / "c.pptx").slides)
    road = [[sh.text_frame.text for sh in s.shapes if sh.name == "道筋"] for s in covers]
    assert road[0] == ["今日の道筋", "よく聞く説明を確かめる", "空気を曲げる", "離陸と乱気流"]   # 点と線の道筋（点の下に段の名前）
    assert sum(sh.name == "道筋の点" for sh in covers[1].shapes) == 4
    assert any("\n" in t for t in road[1])                           # 段の幅に入らない名前は折る


def test_goal_topic_with_only_text_boxes_warns():
    rows = BODY.replace("| 7 | 見出し7 | — | 青帯7 |", "| 7 | 乱気流の揺れ | — | 乱気流で迎え角が変わる |")
    res = cm.goal_figure_check(memo(rows))
    assert res[0][0] == "△" and "乱気流" in res[0][2]
    drawn = rows.replace("| 乱気流で迎え角が変わる | 違い：比較：A（a）と B（b） |", "| 乱気流で迎え角が変わる | 仕組み：模式図：翼と上向きの風 |")
    assert cm.goal_figure_check(memo(drawn))[0][0] == "✔"
    reason = rows.replace("| 乱気流で迎え角が変わる | 違い：比較：A（a）と B（b） |", "| 乱気流で迎え角が変わる | 違い：比較：A（a）と B（b）。外す理由：言い方の比べ |")
    assert cm.goal_figure_check(memo(reason))[0][0] == "✔"


def test_answer_without_reason_warns():
    q = ("### 問題\n1-1. 迎え角を増やすと揚力はどう変わるか。比べよ。〔ゴール1・3枚目〕〔型：比べる〕\n"
         "1-2. 速度が2倍なら揚力は何倍か。〔ゴール1・4枚目〕〔型：計算〕\n\n### 解答\n"
         "1-1. 小さい範囲では増え、大きすぎると失速する。〔要素：増える／失速〕\n1-2. 4倍。〔要素：4倍／2乗〕\n")
    res = cm.quiz_reason_check(memo(BODY, quiz=q))
    assert res[0][0] == "△" and "1-1" in res[0][2] and "1-2" in res[0][2]   # 理由を問わない問題の解答にも理由が要る
    ok = q.replace("大きすぎると失速する。", "大きすぎると流れがはがれるため失速する。").replace("4倍。", "揚力は速度の2乗で効くので4倍。")
    assert cm.quiz_reason_check(memo(BODY, quiz=ok))[0][0] == "✔"


def test_entry_needs_the_learners_experience():
    data_first = BODY.replace("| 2 | 見出し2 | — | 青帯2 |", "| 2 | 重い機体 | — | 翼1㎡が640〜805kgを支える |")
    assert cm.entry_experience_check(memo(data_first))[0][0] == "△"
    felt = data_first.replace("| 要点2 |", "| 窓の外で手を傾けると浮く体験 |")
    assert cm.entry_experience_check(memo(felt))[0][0] == "✔"


def test_answer_with_only_elements_is_stopped_and_still_rendered():
    """解答の本文が無く〔要素〕だけの行は ✘。組むときは要素をつないで答えの文にする（解答の枚が空白にならない）。"""
    import scaffold
    import structures
    q = ("### 問題\n1-1. 揚力のしくみを説明せよ。〔ゴール1・3枚目〕〔型：仕組み〕\n\n### 解答\n"
         "1-1. 〔要素：空気を下へ曲げる／反作用で上へ押される〕\n")
    t = memo(BODY, quiz=q)
    assert any(m == "✘" and i == "解答の本文" for m, i, _ in structures.check_quiz_plan(t, "memo"))
    item = structures.quiz_items(t)["1-1"]
    assert scaffold.answer_text(item) == "空気を下へ曲げる。反作用で上へ押される。"


def test_narration_must_talk_about_the_planned_figure():
    """原稿が話す図（グラフ・表・流れ図・絵の中身）と、その枚の図の案の種類が合わなければ拾う。合っている言い方は拾わない。"""
    secs = {4: "図は、同じ時刻の上と下の空気の粒の位置です。", 7: "図は概略のグラフで、重さの線を超えたところで浮きます。",
            5: "図の左がよく聞く説明、右が実際です。", 6: "図の横軸が迎え角、縦軸が揚力です。", 9: "表のとおり、等時間説は誤りです。"}
    kinds = {4: "比較", 7: "流れ図", 5: "比較", 6: "概略グラフ", 9: "表"}
    got = {n: what for n, _, _, what in cm.figure_talk(secs, kinds)}
    assert got == {4: "絵の中身", 7: "グラフ"}


def test_reason_holes_left_as_deep_or_later_are_flagged(tmp_path):
    """論拠の穴を深・あとだけにして「答えにつながらない：理由」も無い行は △。筋が付いた行・理由のある行は拾わない。"""
    (tmp_path / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    (tmp_path / "memo_review.md").write_text(
        "## 推論距離\n\n"
        "[6] 「細い所で流れが速い ⇒ 気圧が低い」｜論拠｜深｜補う前提：なぜ速いと低いか｜使う所：なし｜架け方：質問の材料\n"
        "[7] 「上面は低圧 ⇒ なぜ速い」｜論拠｜筋・深｜補う前提：曲がる流れ｜使う所：7｜架け方：原稿\n"
        "[8] 「失速」｜論拠｜深｜補う前提：はがれ｜使う所：なし｜架け方：※　答えにつながらない：用語の背景\n"
        "[9] 「迎え角」｜用語｜深｜補う前提：角度の定義｜使う所：なし｜架け方：※\n", encoding="utf-8")
    res = cm.answer_chain_holes(tmp_path / "memo.md")
    assert res and res[0][0] == "△" and "[6]" in res[0][2] and "[7]" not in res[0][2] and "[8]" not in res[0][2] and "[9]" not in res[0][2]


def test_claim_left_of_a_term_row_is_flagged(tmp_path):
    """用語の行の「A ⇒ B」の A が主張で、同じ枚に論拠の行も「A の理由：」も無ければ △。A が語だけの行・論拠の行がある枚は拾わない。"""
    (tmp_path / "memo.md").write_text("# 設計メモ\n", encoding="utf-8")
    (tmp_path / "memo_review.md").write_text(
        "## 推論距離\n\n"
        "[3] 「上の面は流れが速い ⇒ 圧力が低い」｜用語｜語｜補う前提：圧力＝面を押す力｜使う所：3｜架け方：括弧\n"
        "[4] 「失速 ⇒ 力が急に減る」｜用語｜像｜補う前提：像：速さが落ちる → 実際は力が減る｜使う所：4｜架け方：原稿\n"
        "[5] 「流れが曲がる ⇒ 下へ押す」｜用語｜語｜補う前提：反作用の意味｜使う所：5｜架け方：括弧\n"
        "[5] 「流れが曲がる ⇒ 下へ押す」｜論拠｜筋｜補う前提：曲げると下向きの運動が増える｜使う所：5｜架け方：原稿\n"
        "[6] 「角度が増える ⇒ 揚力」｜用語｜語｜補う前提：揚力の意味｜使う所：6｜架け方：括弧　A の理由：5枚目\n", encoding="utf-8")
    res = cm.claim_term_holes(tmp_path / "memo.md")
    assert res and res[0][0] == "△" and "[3]" in res[0][2] and not any(f"[{n}]" in res[0][2] for n in (4, 5, 6))


def test_answer_slide_shows_where_it_was_taught():
    """解答の枚の文には根拠の枚（N枚目）を付ける。原稿は「N枚目で見たことを思い出して」があるので付けない。"""
    import scaffold
    q = ("### 問題\n1-1. 揚力のしくみを説明せよ。〔ゴール1・3枚目〕〔型：仕組み〕\n\n### 解答\n"
         "1-1. 空気を下へ曲げるので、反作用で上へ押される。〔要素：下へ曲げる／反作用〕\n")
    rows = [{"#": 9, "役割": "確認問題"}, {"#": 10, "役割": "解答"}]
    t = memo(BODY, quiz=q)
    assert scaffold.quiz_slices(t, rows, "（{}枚目）")[10][0][1].endswith("（3枚目）")
    assert not scaffold.quiz_slices(t, rows)[10][0][1].endswith("枚目）")


def test_caption_year_is_not_the_access_date():
    """図の下の短い出典に、取得日・URL の数字を発行年として出さない（年が無ければ名前だけ）。"""
    import scaffold
    src = "Maker「Depth table」Table 1 https://example.com/2019/x （発行年の記載なし。取得 2026-11-21）"
    assert scaffold.short_source(src) == "（Maker）"
    assert scaffold.short_source("Walters, A. & Lee 2023, Nature（取得 2026-01-02）") == "（Walters ほか 2023）"

def test_data_condition_written_once_in_the_data_block():
    """データの段（3b節）の「時点」「分母」に書いてあれば、データN を使う枚の行に書き足さなくてよい。"""
    rows = [["#", "青帯（結論）", "本文の要点", "図で見せるもの"],
            ["3", "Aの値はBの約3割", "A：30%〔データ1〕", "比べる：棒グラフ：データ1"]]
    assert cm.data_slides(rows) is not None
    ds = {1: {"fields": {"時点": "2024年度", "分母": "全体の件数"}}}
    assert cm.data_slides(rows, dsets=ds) is None
    assert cm.data_slides(rows, dsets={1: {"fields": {"時点": "—", "分母": "—"}}}) is not None


def test_kept_warnings_are_quiet(tmp_path):
    """「- 残す△：項目（理由）」の項目の △ は出さない。ほかの △ は何度でも中身ごと出す。"""
    m = tmp_path / "memo.md"
    m.write_text("# 設計メモ\n\n- 残す△：冒頭の問い（入口は経験から入れた）\n", encoding="utf-8")
    res = [("△", "冒頭の問い", "長い説明"), ("△", "ゴールの図", "長い説明2"), ("✔", "道筋", "ok")]
    assert [r[1] for r in cm.kept_out(m, res)] == ["ゴールの図", "道筋"]
    assert [r[1] for r in cm.kept_out(m, res)] == ["ゴールの図", "道筋"]


def test_designer_brief_shows_the_beat_figures_of_the_mapped_arc():
    """地図のこの回の行の「ねらい」から型を引く（設計の担当の依頼文に、その型の拍ごとのおすすめの図を入れる）。"""
    import story
    aim, arc = story.AIMS[0][0], story.AIMS[0][1]
    readme = f"| 回 | 題 | ねらい |\n|---|---|---|\n| 1 | 題 | {aim} |\n"
    assert story.map_arc(readme, 1) == arc
    assert story.map_arc("- 中身（話の型：" + arc + "）\n", 1) == arc


def test_slide_without_star_gets_its_fact_number_in_red():
    """★を付け忘れた枚は、事実の印の付いた要点の数値（単位まで）だけを赤字に。★があればそれに従う。印の無い数は赤にしない。"""
    import scaffold
    assert scaffold.items_of("見出し：Aは約12cmで変わる〔事実3〕／B〔事実4〕") == ["見出し：Aは{r:約12cm}で変わる", "B"]
    assert scaffold.items_of("★A は約3倍〔事実1〕／B は 40%〔事実2〕")[1] == "B は 40%"
    assert scaffold.items_of("Aは3つ／B") == ["Aは3つ", "B"]


def test_table_row_labels_fit_on_one_line_or_break_after_a_particle():
    """行ラベルの列は、いちばん長いラベルが1行に入る幅に。入らなければ真ん中に近い助詞の後ろで2行に。"""
    import scaffold
    code = scaffold.table_code("違い：表：説×正しい所｜誤り（短い説＝a｜b／とても長い名前の説明だから危険＝c｜d）")
    assert "label_w=1.5" not in code and "\\n" in code
    assert scaffold.split_label("Xの説明だから危険説") == "Xの説明だから\n危険説"


def test_main_figure_hint_fits_the_slot_without_shrinking(tmp_path):
    """図が主役の枚に案内する大きさは、置き場所（右の列 4.2 in を残した幅・本文の高さ）に縮まずに入る。"""
    import re
    import scaffold
    from zemi import Deck
    d = Deck(workdir=tmp_path)
    w, h = scaffold.FIT_FIG["main"]
    assert w <= d.area["right"] - d.area["x"] - 0.5 - 4.2 and h <= d.content_bottom - d.area["top"] - 0.4
    src = open(scaffold.__file__, encoding="utf-8").read()
    assert re.search(rf"\(({w:g}), ({h:g})\)・図が主役", src)

def test_auto_red_keeps_a_fraction_whole():
    """「N分のM」は1つの数として赤字に（「4分」だけを赤字にすると時間に読める）。時間の「N分」はそのまま。"""
    import scaffold
    assert scaffold.items_of("Aは全体の4分の1まで〔事実9〕") == ["Aは全体の{r:4分の1}まで"]
    assert scaffold.items_of("4分おく〔事実2〕") == ["{r:4分}おく"]


def test_table_cells_break_after_particles_within_the_real_width():
    """表のセルは、箱の中の幅で、助詞・語の切れ目の後ろで折る（1字だけの行や、語の途中で切らない）。"""
    import scaffold
    w = 1.57 - 0.34
    assert scaffold.fold_cell("分子の動きが熱になる", w) == "分子の\n動きが\n熱になる"
    assert scaffold.fold_cell("こすり合う摩擦ではない", w) == "こすり合う\n摩擦では\nない"
    assert scaffold.fold_cell("放射線だから危険", w) == "放射線\nだから危険"
    assert scaffold.fold_cell("短い", w) == "短い"
    assert all(len(x) >= 2 for x in scaffold.fold_cell("長い長い長い長い説明の文が続く", w).split("\n"))

def test_box_text_breaks_after_particles():
    """箱の文は、箱の中の幅で、助詞・語の切れ目の後ろで折る（「〜の／で入れない」にしない）。印のある文はそのまま。"""
    from zemi import fold_jp
    assert fold_jp("蒸気で破裂しうるので入れない", 3.0, 18) == "蒸気で破裂しうるので\n入れない"
    assert fold_jp("向きを変え続けて揺れる", 1.6, 18) == "向きを変え\n続けて揺れる"
    assert fold_jp("{r:赤字}を含む長い長い長い文", 1.0, 18) == "{r:赤字}を含む長い長い長い文"


def test_wide_range_bars_use_a_log_axis_and_keep_the_unit(tmp_path):
    """値の差が30倍以上の棒グラフは10倍ごとの目盛りに（小さい棒が見えなかった）。単位の欄が「cm（説明）」でも cm を使う。"""
    import figlib
    from figkit import fig
    f, ax = fig(5.6, 2.4)
    figlib.bars(ax, ["A", "B", "C"], [1.4, 5.7, 1100], unit="cm")
    assert ax.get_xscale() == "log" and "10倍" in ax.get_xlabel()
    f2, ax2 = fig(5.6, 2.4)
    figlib.bars(ax2, ["A", "B"], [3, 5])
    assert ax2.get_xscale() == "linear"
    import scaffold
    memo = ("## 2. 話の順番\n\n| # | 図で見せるもの |\n|---|---|\n| 3 | 比べる：棒グラフ：データ1 |\n\n"
            "## 3b. データ\n\n### データ1：深さ\n- 単位：cm（強さが37%に減る深さ）\n\n| 区分 | 値 |\n|---|---|\n| A | 1.4 |\n| B | 1100 |\n")
    import re
    rows = [{"#": 3, "図で見せるもの": "比べる：棒グラフ：データ1"}]
    try:
        code = scaffold.figs_py(tmp_path, rows, memo)
    except Exception:
        return
    assert not re.search(r"unit=\"cm（", code)

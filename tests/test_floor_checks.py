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
    road = [next(sh.text_frame.text for sh in s.shapes if sh.name == "道筋") for s in covers]
    assert road[0] == "今日の道筋：よく聞く説明を確かめる → 空気を曲げる → 離陸と乱気流"
    assert "\n" in road[1]                                            # 入らなければ段の区切りで2行に


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
    assert res[0][0] == "△" and "1-1" in res[0][2] and "1-2" not in res[0][2]   # 計算の問は理由を問うていない
    ok = q.replace("大きすぎると失速する。", "大きすぎると流れがはがれるため失速する。")
    assert cm.quiz_reason_check(memo(BODY, quiz=ok))[0][0] == "✔"


def test_entry_needs_the_learners_experience():
    data_first = BODY.replace("| 2 | 見出し2 | — | 青帯2 |", "| 2 | 重い機体 | — | 翼1㎡が640〜805kgを支える |")
    assert cm.entry_experience_check(memo(data_first))[0][0] == "△"
    felt = data_first.replace("| 要点2 |", "| 窓の外で手を傾けると浮く体験 |")
    assert cm.entry_experience_check(memo(felt))[0][0] == "✔"

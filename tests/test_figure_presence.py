"""図が無い・図が小さい・図の下が空いている・中身が具体的でない、を見つける。

以前の試験で、どの確認も通ったのに、文だけの枚、大きな枠に細い線1本の図、「〜を確認」の言い換えばかりの本文が並んだ。
"""
import json
import shutil

import check_layout as cl
import check_memo as cm

W, H = 960, 540


def box(name, left, top, width, height, text="", size=20, ph=None, type_=17):
    return {"slide": 1, "name": name, "type": type_, "left": left, "top": top, "width": width, "height": height,
            "ph": ph, "text": text, "tl": left + 5, "tt": top + 3, "tw": width - 10, "th": height - 6,
            "lines": max(1, text.count("\r") + 1), "paras": max(1, text.count("\r") + 1), "size": size}


def layout(tmp_path, capsys, *figs):
    shapes = [box("Title 1", 40, 20, 600, 60, "例：停止距離", size=44, ph=cl.PH_TITLE, type_=14),
              box("見出し", 60, 90, 400, 40, "●停止距離の中身", size=24),
              box("TextBox 3", 72, 150, 380, 220, "空走距離：認知から\r制動距離：効いてから")] + list(figs)
    f = tmp_path / "shapes.json"
    f.write_text(json.dumps({"slideWidth": W, "slideHeight": H, "slides": 1, "shapes": shapes}, ensure_ascii=False), encoding="utf-8")
    cl.main(str(f))
    return capsys.readouterr().out


def test_text_only_slide_is_flagged(tmp_path, capsys):
    assert "図が無い" in layout(tmp_path, capsys)


def test_small_figure_is_flagged(tmp_path, capsys):
    out = layout(tmp_path, capsys, box("Rounded Rectangle 4", 560, 160, 120, 50, "空走", type_=cl.MSO_AUTOSHAPE),
                 box("Rounded Rectangle 5", 700, 160, 120, 50, "制動", type_=cl.MSO_AUTOSHAPE))
    assert "図が小さい" in out and "図が無い" not in out


def test_large_figure_passes_but_empty_space_below_is_flagged(tmp_path, capsys):
    out = layout(tmp_path, capsys, box("図", 540, 140, 360, 130, type_=cl.MSO_PICTURE))   # 9% だが、下端 3.75in で帯まで 3in 空く
    assert "図が小さい" not in out
    assert "図の下が空いている" in out
    out = layout(tmp_path, capsys, box("図", 540, 140, 360, 280, type_=cl.MSO_PICTURE))
    assert "図の下が空いている" not in out and "図が小さい" not in out


def test_memo_without_a_figure_plan_is_blocked(root, tmp_path):
    memo = tmp_path / "memo.md"
    shutil.copy2(root / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md", memo)
    t = memo.read_text(encoding="utf-8")
    t = t.replace("| 7 | テーマ | 実在しない文献の割合の棒（2本） | Walters & Wilder (2023) |", "| 7 | テーマ | なし | — |")
    memo.write_text(t, encoding="utf-8")
    m = {item: (mark, msg) for mark, item, msg in cm.check(memo)}
    assert m["図の無いスライド"][0] == "✘" and "7" in m["図の無いスライド"][1]
    assert cm.main([str(memo)]) == 1


def test_concreteness():
    head = ["#", "●見出し", "青帯（結論）", "図で見せるもの", "本文の要点", "ノートへ"]
    rows = [head, ["1", "表紙", "—", "—", "—", ""]] + [
        [str(i), f"話{i}", "安全を確認して進める", "概念図", "第1回の姿勢／周囲を確認／急な操作を避ける", ""] for i in range(2, 8)]
    assert cm.concreteness(rows)[0] == "△"          # 「第1回」は数値に数えない
    rows += [[str(i), f"話{i}", "雨では約2倍", "停止距離の棒（60km/h で 44m）", "例：濡れた路面", ""] for i in range(8, 15)]
    assert cm.concreteness(rows)[0] == "✔"          # 13枚中7枚

"""図の下書き（figdraft.py）：描く前に「何に気づかせる図か」を決め、模式図が箱と矢印だけにならないようにする。"""
import shutil

import figdraft

FIGS = '''
def f_next():
    """気づく：上位1つの候補が大半"""
    f, ax = fig()
    ax.barh([0, 1], [0.6, 0.1])
    save(f, OUT / "s02.png")


def f_tokens():
    """実物：トークンの箱の列
    気づく：1文が5個に分かれる
    配置：左から右へ
    ラベル：トークン"""
    f, ax = blank()
    box(ax, 0, 0, 1, 1, "明日")
    save(f, OUT / "s03.png")


def f_temp():
    """温度ごとの確率"""
    f, ax = fig()
    ax.bar([0, 1], [1, 2])
    save(f, OUT / "s06.png")
'''


def _work(tmp_path, root):
    w = tmp_path / "_work" / "AI活用講座_01"
    w.mkdir(parents=True)
    shutil.copy(root / "examples" / "course" / "_work" / "AI活用講座_01" / "memo.md", w / "memo.md")
    return w


def test_template_per_drawn_figure(tmp_path, root, capsys):
    w = _work(tmp_path, root)
    assert figdraft.main([str(w)]) == 0
    out = capsys.readouterr().out
    assert "### 3枚目" in out and "実物：" in out and "配置：" in out      # 模式図は4行
    assert "### 2枚目" in out and "気づく：" in out                        # グラフは「気づく」
    assert "### 4枚目" not in out                                         # 流れ図（PowerPoint の部品）は描かないので出さない


def test_graph_draft_takes_the_data_surprise():
    text = ("## 3b. データ\n\n### データ1：自己評価と中間結果\n- 驚き：自己評価は8割が S・A、中間は半分が B・C\n"
            "- 単位：％\n| 項目 | 値 |\n|---|---|\n| a | 1 |\n| b | 2 |\n\n## 4. 決め事\n")
    t = figdraft.template(5, "棒グラフ", "比べる：棒グラフ：データ1", text)
    assert "気づく：自己評価は8割が S・A" in t


def test_check_drafts_and_box_only_schematics(tmp_path, root):
    w = _work(tmp_path, root)
    assert figdraft.check(w)[0][0] == "・"                                 # figs.py がまだ無い
    (w / "figs.py").write_text(FIGS, encoding="utf-8")
    res = figdraft.check(w)
    msgs = {m: [x for mm, _, x in res if mm == m] for m in ("✘", "△", "✔")}
    assert any("6枚目" in x and "気づく" in x for x in msgs["✘"])          # グラフに「気づく」が無い
    assert any("7枚目" in x for x in msgs["△"])                           # 描く関数が無い
    assert "2枚目" in msgs["✔"][0] and "3枚目" in msgs["✔"][0]            # トークンの箱は箱そのものが実物
    (w / "figs.py").write_text(FIGS.replace("実物：トークンの箱の列", "実物：原子の並び"), encoding="utf-8")
    assert any("3枚目" in x and "箱と矢印" in x for _, _, x in figdraft.check(w))

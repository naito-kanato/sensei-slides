"""図の文字の大きさとラベルの数の検査（figkit.lint）。"""
import figkit


def labeled_figure(n, size):
    f, ax = figkit.fig(5.0, 3.6)
    for k in range(n):
        ax.text(0.1, 0.1 * k, f"ラベル{k}番目", fontsize=size)
    ax.tick_params(labelsize=14)
    return f


def test_good_figure_passes(capsys):
    assert figkit.lint(labeled_figure(3, 14), "ok.png") is False
    assert "WARN" not in capsys.readouterr().out


def test_small_text_is_warned(capsys):
    assert figkit.lint(labeled_figure(2, 11), "small.png") is True
    assert "13pt 未満" in capsys.readouterr().out


def test_too_many_labels_are_warned(capsys):
    assert figkit.lint(labeled_figure(figkit.MAX_LABELS + 1, 14), "many.png") is True
    assert "ラベルが" in capsys.readouterr().out


def test_save_writes_png(tmp_path):
    out = tmp_path / "figs" / "a.png"
    figkit.save(labeled_figure(1, 14), out)
    assert out.exists() and out.stat().st_size > 0


def test_text_on_box_edge_is_warned(capsys):
    """箱より長い文字は、箱の縁にかかるので WARN（以前の講座の「ドライヤー」「漏電を検知」）"""
    f, ax = figkit.blank(5.0, 2.0)
    figkit.box(ax, 0.5, 0.5, 1.0, 0.6, "漏電を検知する装置", fs=16)
    assert figkit.lint(f, "edge.png") is True
    assert "枠の縁・線にかかっている" in capsys.readouterr().out


def test_text_on_line_is_warned():
    """弧や線の上に置いたラベルは WARN（以前の講座の「フード」）"""
    f, ax = figkit.blank(5.0, 2.0)
    ax.plot([0.5, 4.5], [1.0, 1.0], color=figkit.COL.ink)
    ax.text(2.5, 1.0, "フード", ha="center", va="center", fontsize=16)
    assert any("フード" in h for h in figkit.text_on_lines(f))


def test_text_with_room_passes():
    """箱に余裕がある文字、矢印から離れた文字は当たりにしない"""
    f, ax = figkit.blank(5.0, 2.4)
    figkit.box(ax, 0.5, 0.4, 1.6, 0.7, "の", fs=16)
    figkit.arrow(ax, (3.5, 1.9), (3.5, 1.3))
    ax.text(1.3, 1.9, "明日の天気", ha="center", va="center", fontsize=16)
    assert figkit.text_on_lines(f) == []


def test_box_with_head_indents_body():
    """見出し＋説明の箱：説明の各行を全角1字下げ、左揃え。"""
    import figkit
    f, ax = figkit.blank(3, 2)
    figkit.box(ax, 0.2, 0.2, 2.5, 1.5, text="説明の1行\n2行目", head="見出し")
    t = [x for x in ax.texts if "見出し" in x.get_text()][0]
    assert t.get_text() == "見出し\n　説明の1行\n　2行目" and t.get_ha() == "left"

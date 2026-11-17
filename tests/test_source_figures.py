"""資料の図（論文・教科書の図の切り出し）と、言語に合わせたファイルの名前。英語の見本の作り直しで見つけた所。"""
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import brief
import check_layout as cl
import figdraft
import language as LG


def text_image(px: int, w=1000, h=600) -> bytes:
    """数字の行を何行か書いた画像（文字の高さ px）。"""
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default(size=px)
    except TypeError:   # 古い Pillow
        font = ImageFont.load_default()
    for k in range(4):
        d.text((40, 40 + k * int(px * 2.2)), "10 20 30 40 50 60 70 80", fill="black", font=font)
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


def test_text_size_is_measured_from_the_image():
    """記録の無い図（資料の図）の文字の大きさを画像から測る。置く高さ 6 in・画像 600px なら 1px＝0.72pt。"""
    big = cl.glyph_pt(text_image(34), 6.0)     # 字の大きさ 34px ≒ 24pt
    small = cl.glyph_pt(text_image(14), 6.0)   # 14px ≒ 10pt
    assert big is not None and 17 <= big <= 30
    assert small is not None and small < cl.RASTER_FONT_MIN


def test_source_figures_are_cropped_by_the_figure_role(tmp_path):
    work = tmp_path / "_work" / "X"
    (work / "figs").mkdir(parents=True)
    (work / "outline.md").write_text(
        "## 構成\n\n| # | ●見出し | 図で見せるもの |\n|---|---|---|\n| 7 | 光の強め方 | 実物：資料の図：Fig. 3(a) の光学配置 |\n", encoding="utf-8")
    src = figdraft.sourced({7: "実物：資料の図：Fig. 3(a) の光学配置", 5: "仕組み：模式図：干渉計"})
    assert list(src) == [7]
    assert "pdf_pages.py crop" in figdraft.crop_lines(work, src) and "s07.png" in figdraft.crop_lines(work, src)
    res = figdraft.check_sources(work, src)
    assert res[0][0] == "✘" and "まだ無い" in res[0][2]
    (work / "figs" / "s07.png").write_bytes(text_image(14))
    assert "出典の行が無い" in figdraft.check_sources(work, src)[0][2]
    (work / "figs" / "sources.md").write_text("- s07.png ← Abbott et al. PRL 116 p.3 Fig. 3(a)\n", encoding="utf-8")
    mark, _, msg = figdraft.check_sources(work, src)[0]
    assert mark == "△" and "切り出し直す" in msg          # 幅 5.5 in に置くと文字が小さい
    (work / "figs" / "s07.png").write_bytes(text_image(40))
    assert figdraft.check_sources(work, src)[0][0] == "✔"
    text = brief.build("図の担当", str(work), "発表")
    assert "切り出す" in text and "s.oval" in text


def test_presenter_notes_in_english_are_caught():
    for t in ("ΔL ≈ 1/400 of a proton (my estimate)", "≈ 71 (our rough calculation)", "(not in the paper)",
              "about 3 km per M⊙ (back-of-the-envelope estimate)", "(estimated by the presenter)"):
        assert cl.SOURCE_NOTE.search(t), t
    assert not cl.SOURCE_NOTE.search("(presenter's interpretation)") and not cl.SOURCE_NOTE.search("(schematic)")


def test_file_names_follow_the_language(tmp_path):
    assert LG.suffix("slides", "英語") == "_slides" and LG.suffix("script", None) == "_原稿"
    assert LG.sibling(Path("A_slides.pptx"), "slides", "script").name == "A_script.html"
    assert LG.sibling(Path("A_スライド.pptx"), "slides", "script").name == "A_原稿.html"
    assert LG.sibling(Path("A_script.html"), "script", "slides").name == "A_slides.pptx"
    assert LG.strip_suffix("01_X_slides", "slides") == "01_X"
    import scaffold
    work = tmp_path / "_work" / "Waves"
    work.mkdir(parents=True)
    (work / "outline.md").write_text("## オプション\n\n| オプション | 今の値 |\n|---|---|\n| 言語 | 英語 |\n", encoding="utf-8")
    assert 'Waves_slides.pptx"' in scaffold.build_py(work, "outline", "T", [])
    import notes_html
    page = notes_html.build_html("Deck", [("T", "H", "", "Hi.")], [""], lang="英語")
    assert "_comments.json'" in page and "_コメント.json'" not in page


def test_roles_do_not_go_over_the_limits_and_paths_are_quoted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    work = tmp_path / "_work" / "X"
    work.mkdir(parents=True)
    (work / "outline.md").write_text("## オプション\n", encoding="utf-8")
    text = brief.build("仕上げの直しの担当", str(work), "発表")
    assert "`--over` を付けて越えない" in text
    assert "python {skill}/scripts" not in "".join(p.read_text(encoding="utf-8") for p in Path(brief.BRIEFS).glob("*.md"))


def test_check_done_takes_a_work_folder(tmp_path, capsys):
    import check_done
    work = tmp_path / "_work" / "X"
    work.mkdir(parents=True)
    assert check_done.main([str(work)]) == 1
    assert "見つからない" in capsys.readouterr().out

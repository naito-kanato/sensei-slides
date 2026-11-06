"""手持ちのスライドの分析（analyze_template.py）と、それを使うテンプレート作り（make_template.py）。"""
import json
import shutil

import analyze_template as at
import make_template as mt


def value(res, item):
    return next(r["値"] for r in res["rows"] if r["項目"] == item)


def deck_in(built, structure):
    """テンプレートの見本（ゼミの見本の4枚）を、指定の構造で組んだ pptx（分析の試しに使う）"""
    import subprocess
    import sys
    work = built / "examples" / "template"
    out = work / f"{structure}_テンプレートの見本_スライド.pptx"
    if not out.exists():
        r = subprocess.run([sys.executable, "-X", "utf8", "build.py", structure], cwd=work, capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr
    return out


def test_band_deck_is_read_right(built):
    res = at.analyze(deck_in(built, "下の帯"))     # 下の帯の構造で組んだもの（●見出し・左の縦棒・下の帯）
    assert len(res["rows"]) >= 40
    assert value(res, "見出しの印").startswith("「●」")
    assert "左の縦棒" in value(res, "タイトルの飾り")
    assert value(res, "強調の色") == "FF0000"
    assert res["style"]["colors"]["BULLET"] == "005AFF" and res["style"]["colors"].get("PALE", "DCE9F7") == "DCE9F7"
    assert all(r.get("目安") is not None for r in res["rows"])


def test_simple_template_deck_is_read_right(built):
    res = at.analyze(deck_in(built, "上の帯"))
    assert res["style"]["colors"]["BULLET"] == "E8772E" and res["style"].get("band_align") == "l"
    assert "上の全幅の帯" in value(res, "タイトルの飾り")


def test_make_template_writes_three_files(built, tmp_path):
    folder = tmp_path / "スライドテンプレート"
    folder.mkdir()
    shutil.copy2(deck_in(built, "下の帯"), folder / "研究室.pptx")
    mt.from_folder(str(tmp_path), name="研究室")
    for f in ("研究室_テンプレート.pptx", "研究室_テンプレート.json", "研究室_テンプレートの分析.md"):
        assert (folder / f).exists(), f
    assert json.loads((folder / "研究室_テンプレート.json").read_text(encoding="utf-8"))["colors"]["BULLET"] == "005AFF"
    reg = folder / "テンプレート一覧.md"                 # 共通のプロフィールではなく、テンプレートのフォルダの一覧に追加する
    assert "### 研究室" in reg.read_text(encoding="utf-8")
    import slide_profile as sp
    assert "研究室" in sp.load_profile(tmp_path).get("テンプレート", {})


def test_heading_mark_follows_the_template(tmp_path):
    """見た目の設定の heading_mark（■ など）で見出しの印が変わり、原稿のページの見出しからは外れる"""
    import notes_html as nh
    import slide_profile as sp
    from pptx import Presentation
    from zemi import Deck
    src = sp.deck_options({}, name="上の帯")["template"]
    tpl = tmp_path / "四角.pptx"
    shutil.copy2(src, tpl)
    (tmp_path / "四角.json").write_text(json.dumps({"heading_mark": "■", "colors": {"BULLET": "2E7D32"}}), encoding="utf-8")
    d = Deck(template=tpl, workdir=tmp_path / "build")
    s = d.slide("見出し", summary="まとめ"); s.heading("四角の見出し")
    d.save(tmp_path / "out.pptx")
    prs = Presentation(tmp_path / "out.pptx")
    head = next(sh for sh in prs.slides[0].shapes if sh.name == "見出し").text_frame.text
    assert head.startswith("■") and nh.slide_texts(prs)[0][1] == "四角の見出し"
    Deck(workdir=tmp_path / "build")            # 既定に戻す（ほかのテストに色を残さない）

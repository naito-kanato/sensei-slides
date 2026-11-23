"""表紙の点と線の道筋と、本文の枚の上の進み具合（段の名前と同じタイトルの枚）。構成案の「- 道筋：」の検査。
見本のゼミで、問いはあっても答えまでの道筋が画面に無く、採点者2人が減点した（講座の英語版は各枚の上に段が出ていて2人とも満点）。"""
from pathlib import Path

from pptx.enum.text import PP_ALIGN  # noqa: F401  （pptx が入っていることの確かめ）

ROOT = Path(__file__).resolve().parents[1]
STEPS = ["背景（どれだけ小さいか）", "解析手法（どう見分けるか）", "結果（偶然でないか）"]


def test_cover_strip_and_breadcrumb(tmp_path):
    from zemi import Deck
    import notes_html as nh
    deck = Deck(workdir=tmp_path / "build")
    deck.title_slide(["題"], roadmap=STEPS)
    s = deck.slide("解析手法", summary="結論の一文")
    s.heading("見出し")
    s2 = deck.slide("まとめでない別の題", summary="結論")
    out = tmp_path / "d.pptx"
    deck.save(out)
    from pptx import Presentation
    prs = Presentation(out)
    names = [sh.name for sh in prs.slides[0].shapes]
    assert names.count("道筋の点") == 3 and "道筋の線" in names
    texts = " ".join(sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame)
    assert "解析手法" in texts and "どう見分けるか" in texts and "（" not in texts
    title = nh.slide_texts(prs)[1][0]
    assert title.startswith("背景 › 解析手法 › 結果")
    ph = next(p for p in prs.slides[1].placeholders if p.placeholder_format.type == 1)
    runs = {r.text: r for r in ph.text_frame.paragraphs[0].runs}
    assert runs["解析手法"].font.bold and not runs["背景"].font.bold
    assert "›" not in nh.slide_texts(prs)[2][0]          # 段の名前でない題の枚は、いつもの小見出し


def test_outline_roadmap_check(tmp_path):
    import check_outline
    import re
    full = (ROOT / "examples" / "zemi" / "outline.md").read_text(encoding="utf-8")
    got = {i: (m, t) for m, i, t in check_outline.check(_write(tmp_path / "full" / "outline.md", full))}
    assert got["道筋"][0] == "✔"                                    # 見本には道筋の行がある
    src = re.sub(r"^- 道筋：.*\n", "", full, flags=re.M)             # 道筋の行を外して見る
    p = tmp_path / "outline.md"
    p.write_text(src, encoding="utf-8")
    got = {i: (m, t) for m, i, t in check_outline.check(p)}
    assert got["道筋"][0] == "△" and "- 道筋：" in got["道筋"][1]
    p.write_text(src.replace("## 話の筋", "- 道筋：背景（a）→ 検出器（b）→ 観測（c）\n\n## 話の筋", 1), encoding="utf-8")
    got = {i: (m, t) for m, i, t in check_outline.check(p)}
    assert got["道筋"][0] == "△" and "探索" in got["道筋"][1]      # 段に無いタイトルの枚には進み具合が出ない


def _write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p

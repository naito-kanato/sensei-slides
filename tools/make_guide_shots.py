"""使い方のページの、原稿のページのコメント機能の画面（docs/guide/*.jpg）を、今の見本の原稿のページから撮り直す。
見本を組み直したら（make_deck.py のあと）これを走らせる。Edge（と playwright）を使う。

    python tools/make_guide_shots.py
    python tools/make_guide_shots.py --en   # 英語版（docs/guide/en-*.jpg。英語の見本の原稿のページから、コメントも英語で）

撮るもの：
  comment-text.jpg   原稿の文章を選んでコメントを書いているところ（発表の見本）
  comment-slide.jpg  スライドを点線で囲んでコメントを書いているところ（発表の見本）
  comment-list.jpg   コメントの一覧（発表の見本。上の2つを保存したあと）
  answer.jpg         確認問題に答えを書いているところ（講座の見本）
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ZEMI = next((ROOT / "examples" / "zemi").glob("*_原稿.html"))
COURSE = next((ROOT / "examples" / "course" / "AI活用講座").glob("*_原稿.html"))
OUT = ROOT / "docs" / "guide"
VIEW = {"width": 1360, "height": 600}
SLIDE = 11          # 発表の見本で写す枚（図があり、原稿が長い枚。論文の Fig. 4 の枚）
EN_SLIDE = 12       # 英語版の発表の見本で写す枚（論文の Fig. 4 の枚）
QA_SLIDE = 15       # 講座の見本の確認問題（1-4〜1-6）の枚
EN_QA_SLIDE = 16    # 英語版の講座の見本の確認問題（1-4〜1-6）の枚
QA = "1-5"
TEXTS = {"ja": ("この図の縦軸は何の数？", "ここはなぜそう言えるの？", "題名・著者・DOI で検索して原文を開き、中身が同じかを確かめる。見つからなければ使わない。"),
         "en": ("What is the vertical axis of this figure?", "Why can we say this?",
                "Search by title, author and DOI, open the original and check it says the same. If it cannot be found, do not use it.")}


PREFIX = ""


def shot(page, name):
    name = PREFIX + name
    page.screenshot(path=str(OUT / name), type="jpeg", quality=88)
    print("saved", (OUT / name).relative_to(ROOT))


def goto(page, html: Path, n: int):
    print("open", html.name, flush=True)
    page.goto(html.as_uri() + f"#s{n}")
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_timeout(400)
    page.evaluate(f"document.getElementById('s{n}').scrollIntoView({{block:'start'}})")
    page.wait_for_timeout(300)


def main():
    global PREFIX, SLIDE, QA_SLIDE
    en = "--en" in sys.argv
    PREFIX = "en-" if en else ""
    SLIDE = EN_SLIDE if en else SLIDE
    QA_SLIDE = EN_QA_SLIDE if en else QA_SLIDE
    zemi = next((ROOT / "examples" / "zemi_en").glob("*_script.html")) if en else ZEMI
    course = next((ROOT / "examples" / "course_en" / "AI_Literacy").glob("*_script.html")) if en else COURSE
    t_slide, t_text, t_answer = TEXTS["en" if en else "ja"]
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        page = b.new_page(viewport=VIEW, device_scale_factor=1)
        page.set_default_timeout(20000)

        # 発表の見本：スライドを囲む → 原稿の文章を選ぶ → 一覧
        goto(page, zemi, SLIDE)
        page.keyboard.press("c")
        page.wait_for_timeout(200)
        img = page.locator(f"#s{SLIDE} .shot img").first
        if img.bounding_box()["y"] + img.bounding_box()["height"] > VIEW["height"]:   # 英語版では絵がその枚の頭より下にあり、画面の外に残った
            page.evaluate(f"window.scrollBy(0, document.querySelector('#s{SLIDE} .shot img').getBoundingClientRect().top - 90)")
            page.wait_for_timeout(300)
        fig = img.bounding_box()
        x0, y0 = fig["x"] + fig["width"] * 0.58, fig["y"] + fig["height"] * 0.30
        page.mouse.move(x0, y0)
        page.mouse.down()
        page.mouse.move(x0 + fig["width"] * 0.3, y0 + fig["height"] * 0.5, steps=8)
        page.mouse.up()
        page.wait_for_timeout(300)
        page.locator("#cm-pop textarea").fill(t_slide)
        shot(page, "comment-slide.jpg")
        page.keyboard.press("Control+Enter")
        page.wait_for_timeout(300)

        # 原稿の文章を選ぶ（2段落目の頭の約20字）
        page.evaluate(f"""() => {{
          const ps=[...document.querySelectorAll('#s{SLIDE} .notes p')].filter(p=>p.textContent.trim().length>30);
          const p=ps[Math.min(1,ps.length-1)], t=p.firstChild;
          const tx=t.textContent, cut={'50' if en else '20'};   // 英語は語の切れ目まで（20字だと語の途中で切れた）
          const end=tx.length<=cut?tx.length:({'true' if en else 'false'}?Math.max(tx.lastIndexOf(' ',cut),10):cut);
          const r=document.createRange(); r.setStart(t,0); r.setEnd(t,end);
          const s=getSelection(); s.removeAllRanges(); s.addRange(r);
          const b=r.getBoundingClientRect();
          p.dispatchEvent(new MouseEvent('mouseup',{{bubbles:true,clientX:b.right,clientY:b.bottom}}));
        }}""")
        page.wait_for_timeout(400)
        page.locator("#cm-pop textarea").fill(t_text)
        shot(page, "comment-text.jpg")
        page.keyboard.press("Control+Enter")
        page.wait_for_timeout(300)
        page.keyboard.press("Escape")
        page.locator("#cm-open").click()
        page.wait_for_timeout(400)
        shot(page, "comment-list.jpg")

        # 講座の見本：確認問題に答える
        page.set_viewport_size({"width": 1360, "height": 1000})
        goto(page, course, QA_SLIDE)
        page.add_style_tag(content="header{display:none!important}")   # 上の固定の帯が問題の枚に重なるので、この1枚では隠す
        page.evaluate(f"window.scrollTo(0, document.getElementById('s{QA_SLIDE}').getBoundingClientRect().top + window.scrollY - 10)")
        page.wait_for_timeout(200)
        page.locator(f"#s{QA_SLIDE} .qa-btn", has_text=QA).first.click()
        page.wait_for_timeout(400)
        page.locator("#cm-pop textarea").fill(t_answer)
        sec = page.locator(f"#s{QA_SLIDE}").bounding_box()
        pop = page.locator("#cm-pop").bounding_box()
        top, bottom = max(0, sec["y"] - 10), min(1000, max(sec["y"] + sec["height"], pop["y"] + pop["height"]) + 10)
        page.screenshot(path=str(OUT / f"{PREFIX}answer.jpg"), type="jpeg", quality=88,
                        clip={"x": 0, "y": top, "width": 1360, "height": bottom - top})
        print("saved", (OUT / f"{PREFIX}answer.jpg").relative_to(ROOT))
        try:
            b.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

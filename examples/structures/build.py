"""型の見本：本文の形と図解の型の部品を、1枚ずつ使って見せる（references/structures.md）。題材はゼミの見本と同じ重力波の初観測。

    python figs.py                     # 説明のための図（shift_before・shift_after）を figs/ に
    python build.py                    # 型の見本_スライド.pptx（テンプレート1。全部の型）
    python build.py テンプレート3      # ほかの構造で数枚：テンプレート3_型の見本_スライド.pptx（3〜7 も同じ）
    python build.py テンプレート2 深緑  # 構造と色を指定：テンプレート2_深緑_型の見本_スライド.pptx

図はゼミの見本（examples/zemi/figs）と、このフォルダの figs/ のものを使う。shift_before・shift_after は説明のための例（実在の測定ではない）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from slide_profile import deck_options, load_profile  # noqa: E402
from zemi import Deck  # noqa: E402

ZFIG = HERE.parent / "zemi" / "figs"
FIG = HERE / "figs"
NAME = sys.argv[1] if len(sys.argv) > 1 else "テンプレート1"
COLOR = sys.argv[2] if len(sys.argv) > 2 else None
OUT = HERE / ("型の見本_スライド.pptx" if NAME == "テンプレート1" and not COLOR else f"{NAME}{'_' + COLOR if COLOR else ''}_型の見本_スライド.pptx")
T = "型の見本：重力波の初観測"

deck = Deck(workdir=HERE / "build", **deck_options(load_profile(HERE), name=NAME, color=COLOR))
A = deck.area   # 構造ごとの本文の場所（x・top・fig_x など。テンプレートの .json の area）
deck.title_slide(["型の見本", "本文の形と図解の部品"], author="sensei-slides")
R = 12.65   # 図の右端（ページの右の余白 0.4 in の内側）


def zfig(s, name, y):
    """ゼミの見本の図を、本文の右に描いた幅のまま置く（ゼミの見本の図は結論ヘッダーの本文の場所に合わせて幅 5.6〜6 in で描いてある）。
    柱の構造では右の白い所の fig_x から。本文の下端・右端に入らなければ縮める。"""
    from PIL import Image
    path = ZFIG / name
    with Image.open(path) as im:
        w, h = im.size[0] / im.info["dpi"][0], im.size[1] / im.info["dpi"][0]
    col = "text_right" in A
    tr = max([b.right for kind, b in s.boxes if kind != "image" and deck.header_bottom - 0.2 < b.y < deck.content_bottom] + [A["x"]])
    x0 = A["fig_x"] if col else tr + 0.6
    k = min(1.0, (deck.content_bottom - 0.35 - y) / h, (R - x0) / w)
    w, h = w * k, h * k
    x = x0 if col else min(tr + max(0.6, (R - w - tr) / 2), R - w)
    return s.image(path, x=x, y=y, w=w, h=h)


def full():
    # ---- 本文の形
    s = deck.slide(T, summary="前提 ⇒ 帰結：説明のあと、結果を赤字の一言で")
    s.heading("前提 ⇒ 帰結（s.lead）")
    s.at(1.0, 1.95)
    s.lead(["1916年 アインシュタインが予言", "時空のひずみが光速で伝わる横波"], "直接の観測はなし")
    s.lead(["連星パルサーの公転周期の減少", "予言どおりの減り方（1993年 ノーベル賞）"], "間接的には確認")
    b = zfig(s, "strain.png", y=2.3)
    s.caption(b, "（概略）")

    s = deck.slide(T, summary="ラベル＋説明：名前を小見出しにして、説明を字下げ")
    s.heading("ラベル＋説明（s.block）")
    s.at(1.0, 1.95)
    s.block("マイケルソン干渉計：", ["2本の腕（4 km）の長さの差を", "レーザーの干渉で測る", "ひずみ 10^{-21} の変化まで"])
    s.block("2か所で同時に観測：", ["ハンフォードとリビングストン", "約 3000 km 離れた2台", "到着の時間差 約 7 ms"], then="雑音と区別")
    zfig(s, "michelson.png", y=1.9)

    s = deck.slide(T, summary="横の矢印で展開：左に条件、右に結果")
    s.heading("横の矢印で展開（s.develop）")
    s.at(1.0, 2.0)
    s.develop(("ひずみ：", ["1.0 × 10^{-21}"]), "腕 4 km の長さの変化\n{r:約 4 × 10^{-18} m}")
    s.develop("2つの検出器で\n同じ波形", "{r:装置の雑音では}\n{r:説明できない}")
    s.develop("周波数 35 Hz", "250 Hz まで\n約 0.2 s で上昇")
    zfig(s, "timeshift.png", y=1.9)

    s = deck.slide(T, summary="条件の場合分け：条件を太字、説明を字下げして灰色の囲みに")
    s.heading("条件の場合分け（s.cases）")
    s.cases([("合体の前（インスパイラル）", "周波数が 35 Hz から 250 Hz へ\n約 0.2 s で8周期"),
             ("合体", "振幅が最大（ひずみ 1.0 × 10^{-21}）"),
             ("合体の後（リングダウン）", "1つのブラックホール（太陽の62倍）\nの減衰振動")], x=1.0, y=1.95)
    zfig(s, "timeshift.png", y=1.9)

    s = deck.slide(T, summary="問い → 答え：別の説明を1つずつ確かめる")
    s.heading("問い → 答え（s.ask）")
    s.at(1.0, 1.95)
    s.ask("装置の雑音ではないのか？", "2か所で同じ波形、時間差 約 7 ms")
    s.ask("偶然の一致ではないのか？", "{r:有意度 5.1σ 以上}\n誤報は 20万年に1回未満")
    s.ask("信号は十分に強いのか？", "SN比 24（2台を合わせた値）")
    zfig(s, "scale.png", y=2.1)

    s = deck.slide(T, summary="番号の手順：解析・試料作成・測定の順番")
    s.heading("番号の手順（s.numbered）")
    s.numbered(["2か所のデータの雑音を白色化\n（周波数ごとの雑音で規格化）", "理論の波形と照合\n（マッチドフィルタ・SN比 24）",
                "時間をずらして\n偶然の一致の頻度を評価"], x=1.0, y=1.95)
    zfig(s, "power.png", y=1.85)

    s = deck.slide(T, summary="初の直接観測から、連星ブラックホールの存在を確認")
    s.heading("縦の矢印で結論へ（s.lead_down）")
    s.lead_down("太陽の36倍と29倍のブラックホールが合体\n約13億光年先からの重力波を初めて直接観測",
                "連星ブラックホールの存在と、一般相対論の予言を確認", x=1.0, y=2.1)

    # ---- 図解の型
    deck.section(2, "図解の型", lead="カード・ツリー・前後・2つ並べた図・吹き出し")

    s = deck.slide(T, summary="並列カード：同格の要素を同じ大きさの箱に")
    s.heading("並列カード（s.cards row）")
    s.cards([("質量", "36 と 29 → 合体後 62\n（太陽の質量の倍数）"), ("距離", "約 13億光年\n（410 Mpc）"),
             ("放射されたエネルギー", "太陽の質量の約 3 倍\nを重力波で放出")], y=2.1, size=20)

    s = deck.slide(T, summary="段違いの順序：段階を階段状にずらし、細い矢印で")
    s.heading("段違いの順序（s.cards steps）")
    s.cards([("連星", "2つのブラックホール"), ("接近", "公転しながら近づく"), ("合体", "重力波を放射"), ("観測", "約13億年後\n2015年9月14日")],
            layout="steps", y=1.9)

    s = deck.slide(T, summary="循環：繰り返す段階を4枚で回す")
    s.heading("循環（s.cards cycle）")
    s.cards([("観測", "データを集める"), ("雑音の解析", "雑音の源を調べる"), ("装置の改良", "雑音を下げる"), ("感度の向上", "次の観測へ")],
            layout="cycle", y=1.9, x=2.2, w=8.9)

    s = deck.slide(T, summary="ツリー：分類・階層を枝分かれで")
    s.heading("ツリー（s.tree）")
    s.tree("重力波の源", [("連星の合体", "ブラックホール・中性子星"), ("超新星爆発", "星の重力崩壊"),
                        ("回転する中性子星", "連続した波"), ("背景の重力波", "初期宇宙")], y=2.1, child_w=6.0)

    s = deck.slide(T, summary="前後：従来と改善を並べ、差を1つの数で")
    s.heading("前後（s.before_after）")
    s.before_after(("初期の検出器", ["2002〜2010年の観測", "重力波は見つからず"]),
                   ("改良した検出器", ["2015年から観測", "2015年9月14日に検出"]), value="感度 約 3 倍", y=2.0)

    s = deck.slide(T, summary="2つ並べた図：条件の違う2つを並べ、下に数値")
    s.heading("2つ並べた図（s.pair）")
    s.pair(FIG / "shift_before.png", FIG / "shift_after.png", labels=["ずらす前", "時刻をずらした後"],
           values=["2台がそろう", "そろわない"], y=1.85, caption="（説明のための例）")

    s = deck.slide(T, summary="吹き出し：図の注目点から、解釈を引き出す")
    s.heading("図への吹き出し（s.callout）")
    s.at(1.0, 1.95)
    s.lead(["ふだんは打ち消し合って暗い", "腕の長さの差が変わると", "干渉の明暗が変わる"], "光の強さで長さの差を測る")
    b = zfig(s, "michelson.png", y=1.85)
    k = b.w / 4.95   # 光検出器の位置は、幅 4.95 in の図で測った値を幅に比例させる
    s.callout((b.x + 1.65 * k, b.y + 3.4 * k), (b.x - 1.6, b.y + 3.2 * k), "ここで明暗を測る")

    deck.build_up(T, "項目を1つずつ足す（deck.build_up）",
                  ["1. 重力波を初めて直接観測", "2. 連星ブラックホールの合体", "3. 一般相対論の予言を確認"],
                  summary="漸進表示：今の項目だけ濃く、前の項目は灰色に", figure=ZFIG / "strain.png", fig_x=6.4)


def skeleton():
    # ほかの構造で数枚。summary が構造ごとの結論の置き場（下の帯・囲み・結論の一文・副題・柱の下）に入る
    s = deck.slide("背景", summary="重力波は予言から100年、直接の観測がなかった")
    s.heading("重力波")
    s.lead(["1916年に予言", "時空のひずみの横波"], "直接の観測はなし")     # 柱の構造でも入る短い句（1行14字まで）
    zfig(s, "strain.png", y=A["top"] + 0.3)   # 図は本文の右に（柱の構造では fig_x から）

    s = deck.slide("研究の目的", summary="2台の干渉計で、波そのものをとらえる")   # 目的の枚も、要約の一文を結論の置き場に
    s.heading("問題から目的へ")
    col = "text_right" in A          # 柱のある構造では、縦の矢印の塊は右の白い所に
    s.lead_down("間接的な証拠だけ\n直接とらえた人はいない", "離れた2台の干渉計で同時に測る",
                x=A["fig_x"] + 0.2 if col else None, y=A["top"] + 0.1 if not col else 1.2,
                w=(A["right"] - A["fig_x"] - 0.2) if col else None)

    s = deck.slide("結果", summary="時刻をずらすと、2台の一致は消える")
    s.heading("時刻ずらしの前後")
    s.pair(FIG / "shift_before.png", FIG / "shift_after.png", labels=["ずらす前", "時刻をずらした後"],
           values=["2台がそろう", "そろわない"], caption="（説明のための例）")


if NAME == "テンプレート1" and not COLOR:
    full()
else:
    skeleton()
deck.save(OUT, title=T)

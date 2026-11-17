"""担当への依頼文を、雛形（assets/briefs/<担当>.md）から作る（SKILL.md「手順と担当」）。

メインは依頼文を自分で書かない。担当を起動するときの依頼は次の1行だけにする：
    「`python <skill>/scripts/brief.py <担当> <work>` を走らせ、出た依頼のとおりに進める」
（<work> は作業フォルダ。地図の担当だけは講座名。ユーザーの答えがあれば、その下に「ユーザーの答え：…」と続ける）

    python <skill>/scripts/brief.py --list                       # 担当の一覧
    python <skill>/scripts/brief.py 仕上げ役 _work/〇〇講座_01
    python <skill>/scripts/brief.py 裏取りの担当 _work/X講座_01 --n 2
    python <skill>/scripts/brief.py 地図の担当 X講座 --note "学習者：…／回数：3"
    python <skill>/scripts/brief.py 制作役 _work/X講座_01 --part 1/2   # 本文が8枚以上なら2人（next_step が言う）と、図の担当（brief.py 図の担当 <work>。自分で描く図が8枚以上なら --part 1/2・2/2 の2人）
    python <skill>/scripts/brief.py 仕上げ役 _work/X講座_01 --over      # 回数の上限を超えて起動する（ユーザーが許したときだけ）

依頼文を出すたびに、その担当の起動を1回と数える（budget.py。上限なら依頼文を出さずに ✘ で止まる）。
メインが中身を確かめるだけなら --peek（数えない）。
直しの担当の依頼文を出すとき（--peek でないとき）は、直す前の memo.md・outline.md を <work>/memo_直す前.md・outline_直す前.md に写す（もうあれば上書きしない）。担当を起動したあと作業フォルダに何も書かれていなければ、次の起動と同じ1回とみなす。

雛形の書き方：{skill}・{work}・{course}・{plan_name}・{review_name}・{n} を埋める。
`[節] steps 5 6 ／ tools コマンドの書き方` の行は、その手順書の節（guide.py と同じ切り方）を依頼文の終わりに写す
（担当が guide.py を呼ぶ回数を減らす。呼ぶたびに、それまでの会話をまるごと読み直すため）。行の頭が [発表] か [講座] の行は、
その種類のときだけ残す。[直す] の行は推論距離を直す回だけ、[測る] の行は「推論距離：測るだけ」の回だけ残す（種類の印のあとに付けてよい）。全部の担当に共通の頭（ユーザーに質問しない・scripts の中身を読まない・作業フォルダの置き場所）と、
終わりの「10行までで返す」は、このスクリプトが足す。作業フォルダが講座フォルダの中にあるなど、置き場所が違えば ✘ で止める。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SKILL = Path(__file__).resolve().parents[1]
BRIEFS = SKILL / "assets" / "briefs"
NO_WORK = ("地図の担当",)
SPLIT_AT = 8   # カードがこの枚数以上なら、制作役を前半と後半の2人に分ける（1つの会話が長くなると、呼び出しごとに読み直す量が増える）


def card_numbers(work: Path) -> list[int]:
    d = Path(work) / "cards"
    return sorted(int(p.stem) for p in d.glob("[0-9][0-9].md")) if d.is_dir() else []


def halves(nums: list[int]) -> list[list[int]]:
    if len(nums) < SPLIT_AT:
        return [nums]
    k = -(-len(nums) // 2)
    return [nums[:k], nums[k:]]

HEAD = """あなたは sensei-slides スキルの「{role}」です（{kind}）。ユーザーには質問しません（聞きたい所は、返答の「迷った所」に書く）。
作業ディレクトリ：{cwd}（コマンドはここから `python "{skill}/scripts/<名前>.py" ...`（空白のあるパスは引用符で囲む）。作業ディレクトリに .venv があれば、その python で）
作業フォルダ：{work}（作業ディレクトリ直下の `_work/` の中。講座フォルダ・発表フォルダの中に作らない）
SKILL.md と references/*.md は丸ごと読まない（この依頼（終わりに写した手順書の節を含む）と、指定された `guide.py` の節で足りる。足りないときだけ `guide.py <名前>` で見出しを見て、その節だけ）。scripts の中身（.py）は読まない。使い方は guide.py と各スクリプト・検査の出力にある。日本語を含む使い捨てのスクリプトは、作業フォルダの外の一時フォルダに書く。
呼び出しの回数が使用量を決める（呼ぶたびに、それまでの会話をまるごと読み直すため）。前の結果を見なくても決められることは、1回の呼び出しにまとめる（例：作業の始めに要るファイルは、まとめて開く）。結果を見てから決めることだけを、次の呼び出しに回す。
回数・トークンの上限で止まったら、`--over` を付けて越えない（越えるかはユーザーが決める）。そこで止めて、残った所を返答に書く。
ただし、書いたあとの検査は、書いた次の呼び出しで行う（同じ呼び出しに入れない）。make_deck は、ほかのコマンドとつなげずに単独で。書いたものを目で読み直すのは要らない（確かめるのは検査のスクリプトで）。
"""
TAIL = "\n終えたら、「返すもの」だけを10行までで返す。"


def roles():
    return sorted(p.stem for p in BRIEFS.glob("*.md"))


def kind_of(work: Path, given: str | None) -> str:
    if given:
        return "講座" if "講" in given else "発表"
    if (work / "memo.md").exists() or re.search(r"_\d{2}$", work.name):
        return "講座"
    return "発表"


def rel(p: Path) -> str:
    try:
        return Path(os.path.relpath(p, Path.cwd())).as_posix()
    except ValueError:
        return p.as_posix()


def keep_before_fix(plan: Path) -> Path | None:
    """直しの担当を起動する前の設計メモ・構成案を <work>/<memo|outline>_直す前.md に写す（あとで、直す前と後の穴を比べられるように）。
    もうあれば上書きしない（2回目の起動では、最初の直しの前の版を残す）。"""
    plan = Path(plan)
    copy = plan.with_name(f"{plan.stem}_直す前.md")
    if not plan.exists() or copy.exists():
        return None
    copy.write_bytes(plan.read_bytes())
    return copy


# 日本語でないデッキ（設定の「言語」）のときに、依頼の終わりに足す行。{lang} はその言語の名前
LANG_COMMON = ("**出力の言語：{lang}**。スライド・原稿（notes.md）・確認問題と解答の文は{lang}で書く。"
               "構成案・設計メモの説明、手当ての書き方、返答は日本語のままでよい。")
LANG_NOTES = {
    "設計の担当": "表のタイトル・●見出し・青帯（結論）・本文の要点の列と、確認問題・解答の文は{lang}で書く（そのままスライドに載る）。"
                 "表紙の行の「第N回」も {lang} で（英語なら Lecture N: …）。手当ての「原稿で「…」」の「…」と、用語の穴の語も{lang}で。数値・出典は元のまま。字数の目安は全角に直した幅（半角の字・空白は0.5）",
    "軽量の設計の担当": "表のタイトル・●見出し・青帯（結論）・本文の要点の列と、確認問題・解答の文は{lang}で書く（そのままスライドに載る）。"
                       "表紙の行の「第N回」も {lang} で（英語なら Lecture N: …）。数値・出典は元のまま。字数の目安は全角に直した幅（半角の字・空白は0.5）。引用する原文は元の言語のまま",
    "軽量の制作の担当": "書き方の読み替えは `cards/00_共通.md` の「## 言語」の節。図の中の文字も{lang}。スライドと原稿は{lang}で、日本語の文字を残さない",
    "直しの担当": "直す行のうち、スライドに載る列（タイトル・●見出し・青帯・本文の要点）と確認問題の文は{lang}で書く",
    "制作役": "書き方の読み替えは `cards/00_共通.md` の「## 言語」の節（字数は全角に直した幅、本文は短い句、原稿は話し言葉の{lang}）",
    "図の担当": "図の中の文字（軸・目盛りの単位・ラベル・凡例）は{lang}で書く。数値と記号はそのまま",
    "仕上げ役": "スライドと原稿は{lang}。check_layout は全角に直した幅で数え、文末の記号で終わる行を「文の形の行」として出す（短い句に直す）。"
               "日本語の文字が残っていないかも見る",
    "仕上げの直しの担当": "スライドと原稿は{lang}。直した所も{lang}で書き、日本語の文字を残さない",
    "レビュー担当": "スライドに載る列（タイトル・●見出し・青帯・本文の要点）と確認問題は{lang}で書いてある。{lang}として自然か・意味が元の事実と同じかも見る。指摘は日本語で書く",
    "完成後のレビュー担当": "スライドと原稿は{lang}で書いてある。{lang}として自然か、日本語が残っていないか、訳で意味が強まっていないかも見る。指摘は日本語で書く",
    "地図の担当": "講座の README の「学習者とゴール」に `- 言語：{lang}` の行を書く（各回の設計メモに写す）。各回の題は{lang}で",
    "数字を探す担当": "集める表の説明は日本語でよい。引用する原文は元の言語のまま",
    "裏取りの担当": "表の確かめは日本語でよい。引用する原文は元の言語のまま",
}


def plan_language(plan, note: str = "", readme=None) -> str:
    """構成案・設計メモの設定の「言語」→ 講座の README の「- 言語：…」（設計メモがまだ無い設計の担当・数字を探す担当）
    → ユーザーの答えの「言語：…」（地図の担当）。無ければ日本語。
    英語の試しで、設計の担当の依頼に言語の行が入らなかった（memo.md ができる前で、README を見ていなかった）。"""
    import language as LG
    from slide_profile import read_options
    if plan is not None and Path(plan).exists():
        v = read_options(Path(plan).read_text(encoding="utf-8")).get("言語")
        if v:
            return LG.lang_name(v)
    if readme is not None and Path(readme).exists():
        m = re.search(r"^-\s*言語\s*[:：]\s*(.+?)\s*$", Path(readme).read_text(encoding="utf-8"), re.M)
        if m:
            return LG.lang_name(m.group(1))
    m = re.search(r"言語\s*[:：]\s*([^\s／/、,。]+)", note or "")
    return LG.lang_name(m.group(1)) if m else LG.DEFAULT


def embed(specs) -> str:
    """[節] の行（「steps 5 6 ／ tools コマンドの書き方」）→ 写す節の本文。同じ節は1回だけ。"""
    import guide
    out, seen = [], set()
    for spec in specs:
        for grp in re.split(r"[／]", spec):
            w = grp.split()
            for k in w[1:]:
                if (w[0], k) in seen:
                    continue
                seen.add((w[0], k))
                t = guide.section(w[0], k)
                if t is None:
                    raise SystemExit(f"✘ 雛形の [節] の「{w[0]} {k}」が手順書に無い")
                out.append(t)
    if not out:
        return ""
    return ("\n\n---\n# 手順書の節（ここに写した。同じ節を guide.py で読み直さない。ほかの節が要るときだけ guide.py で）\n\n"
            + "\n\n".join(out))


def build(role: str, target: str, kind: str | None = None, n: str = "1", note: str = "", part: str = "",
          over: bool = False, count: bool = False) -> str:
    path = BRIEFS / f"{role}.md"
    if not path.exists():
        raise SystemExit(f"✘ 担当「{role}」の雛形が無い。使える担当：{'・'.join(roles())}")
    if role in NO_WORK:
        course, work, k = target, Path("_work") / f"{target}_0N", "講座"
    else:
        work = Path(target).resolve()
        k = kind_of(work, kind)
        course = re.sub(r"_\d{2}$", "", work.name)
        if k == "講座" and work.parents[1].name == course:
            raise SystemExit(f"✘ _work/ が講座フォルダ {course}/ の中にある。作業ディレクトリ直下（{course}/ と並ぶ所）の _work/{work.name}/ に移してから")
        if work.parent.name != "_work":
            raise SystemExit(f"✘ 作業フォルダ {target} が _work/ の直下に無い（作業ディレクトリ直下の _work/<名前>/ に置く）")
        if role == "数字を探す担当":
            work.mkdir(parents=True, exist_ok=True)   # 設計の前に動く最初の担当（作業フォルダはまだ無い）
        if count:   # 回数の予算（budget.py）：上限なら依頼文を出さずに止める
            import budget
            msg = budget.check_tokens(work, over) or budget.check_role(work, role, part or (n if role in ("裏取りの担当", "数字を探す担当") else ""), over)
            if msg:
                raise SystemExit(msg)
        work = Path(rel(work))
    plan_name = "memo.md" if k == "講座" else "outline.md"
    review_name = "memo_review.md" if k == "講座" else "outline_review.md"
    other = "[発表]" if k == "講座" else "[講座]"
    mine = "[講座]" if k == "講座" else "[発表]"
    k_part, n_part = (int(x) for x in part.split("/")) if part else (1, 1)
    plan = (Path(target) / plan_name) if role not in NO_WORK else None
    if role == "直しの担当" and count and plan is not None:
        keep_before_fix(plan)
    from slide_profile import measure_only
    measure = bool(plan and plan.exists() and measure_only(plan.read_text(encoding="utf-8")))
    lines, specs = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(other):
            continue
        if line.startswith("[図]"):
            if n_part > 1:   # 制作役が2人のときは、図は図の担当が描く
                continue
            line = line[3:]
        if line.startswith("[戻す]"):
            if n_part != 1:
                continue
            line = line[4:]
        line = line[len(mine):] if line.startswith(mine) else line
        if line.startswith("[直す]") or line.startswith("[測る]"):   # 推論距離：直す回と、測るだけの回（inference-distance.md 8節）
            if line.startswith("[測る]") != measure:
                continue
            line = line[4:]
        if line.startswith("[節]"):
            specs.append(line[3:].strip())
            continue
        lines.append(line)
    cards, part_note = "カード全部", ""
    if role == "制作役" and role not in NO_WORK:
        nums = card_numbers(Path(target))
        hs = halves(nums) if n_part > 1 else [nums]
        mine_n = hs[k_part - 1] if k_part <= len(hs) else []
        if mine_n:
            cards = "・".join(f"{x:02d}.md" for x in mine_n)
        if n_part > 1:
            part_note = (f"制作役は {n_part} 人で、あなたは {k_part} 人目（{'前半' if k_part == 1 else '後半'}の枚。図は図の担当が同時に描いている）。"
                         "ほかの人の枚・parts は読まない・書かない。merge は仕上げ役が最初にする")
    figfile, figpart = f"{Path(work).as_posix()}/figs.py", ""
    if role == "図の担当" and n_part > 1:   # 図の担当が2人：figs_1.py・figs_2.py に半分ずつ。figs.py は2つを動かすだけ
        import figdraft
        figdraft.ensure_runner(Path(target))
        mine_f = figdraft.part_of(figdraft.drawn(figdraft.plan_cells(Path(target))[1]), part)
        figfile, figpart = f"{Path(work).as_posix()}/figs_{k_part}.py", f" --part {part}"
        part_note = (f"図の担当は {n_part} 人で、あなたは {k_part} 人目。描くのは {'・'.join(f'{x}枚目' for x in mine_f) or '（無し）'} の図だけ"
                     f"（`{figfile}` に書き、作業フォルダで `python figs_{k_part}.py` を走らせて描く。figs.py は2人分を動かすだけなので書き換えない）。"
                     "ほかの人の図・figs_N.py は読まない・書かない")
    vals = {"skill": rel(SKILL), "work": Path(work).as_posix(), "course": course, "plan_name": plan_name,
            "review_name": review_name, "n": n, "role": role, "kind": k, "cwd": Path.cwd().as_posix(),
            "cards": cards, "part_note": part_note, "figfile": figfile, "figpart": figpart}
    text = HEAD.format(**vals) + "\n" + "\n".join(lines).format(**vals)
    readme = (Path(target).resolve().parents[1] / course / "00_README.md") if role not in NO_WORK and k == "講座" else None
    lang = plan_language(plan, note, readme)
    import language as LG
    if not LG.is_japanese(lang):
        text += "\n" + LANG_COMMON.format(lang=lang) + ("\n" + LANG_NOTES[role].format(lang=lang) if role in LANG_NOTES else "")
    if note:
        text += "\n\nユーザーの答え・メインからの補足：" + note
    return text + embed(specs) + TAIL


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--list":
        print("担当：" + "・".join(roles()))
        return 0
    if len(a) < 2:
        print("使い方：brief.py <担当> <作業フォルダ>（地図の担当は講座名）")
        return 2
    opt = lambda k, d="": a[a.index(k) + 1] if k in a else d   # noqa: E731
    print(build(a[0], a[1], opt("--kind") or None, opt("--n", "1"), opt("--note"), opt("--part"), "--over" in a,
                count="--peek" not in a))
    return 0


if __name__ == "__main__":
    sys.exit(main())

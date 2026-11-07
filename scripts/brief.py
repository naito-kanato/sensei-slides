"""担当への依頼文を、雛形（assets/briefs/<担当>.md）から作る（SKILL.md「役割を分ける」）。

メインは依頼文を自分で書かない。担当を起動するときの依頼は次の1行だけにする：
    「`python <skill>/scripts/brief.py <担当> <work>` を走らせ、出た依頼のとおりに進める」
（<work> は作業フォルダ。地図の担当だけは講座名。ユーザーの答えがあれば、その下に「ユーザーの答え：…」と続ける）

    python <skill>/scripts/brief.py --list                       # 担当の一覧
    python <skill>/scripts/brief.py 仕上げ役 _work/病院機能評価講座_01
    python <skill>/scripts/brief.py 裏取りの担当 _work/X講座_01 --n 2
    python <skill>/scripts/brief.py 地図の担当 X講座 --note "学習者：…／回数：3"

雛形の書き方：{skill}・{work}・{course}・{plan_name}・{review_name}・{n} を埋める。行の頭が [発表] か [講座] の行は、
その種類のときだけ残す。全部の担当に共通の頭（ユーザーに質問しない・scripts の中身を読まない・作業フォルダの置き場所）と、
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

HEAD = """あなたは sensei-slides スキルの「{role}」です（{kind}）。ユーザーには質問しません（聞きたい所は、返答の「迷った所」に書く）。
作業ディレクトリ：{cwd}（コマンドはここから `python {skill}/scripts/<名前>.py ...`。作業ディレクトリに .venv があれば、その python で）
作業フォルダ：{work}（作業ディレクトリ直下の `_work/` の中。講座フォルダ・発表フォルダの中に作らない）
scripts の中身（.py）は読まない。使い方は guide.py と各スクリプト・検査の出力にある。日本語を含む使い捨てのスクリプトは、作業フォルダの外の一時フォルダに書く。
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


def build(role: str, target: str, kind: str | None = None, n: str = "1", note: str = "") -> str:
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
        work = Path(rel(work))
    plan_name = "memo.md" if k == "講座" else "outline.md"
    review_name = "memo_review.md" if k == "講座" else "outline_review.md"
    other = "[発表]" if k == "講座" else "[講座]"
    mine = "[講座]" if k == "講座" else "[発表]"
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(other):
            continue
        lines.append(line[len(mine):] if line.startswith(mine) else line)
    vals = {"skill": rel(SKILL), "work": Path(work).as_posix(), "course": course, "plan_name": plan_name,
            "review_name": review_name, "n": n, "role": role, "kind": k, "cwd": Path.cwd().as_posix()}
    text = HEAD.format(**vals) + "\n" + "\n".join(lines).format(**vals)
    if note:
        text += "\n\nユーザーの答え・メインからの補足：" + note
    return text + TAIL


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
    print(build(a[0], a[1], opt("--kind") or None, opt("--n", "1"), opt("--note")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

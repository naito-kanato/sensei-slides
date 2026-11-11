"""図の下書き：自分で描く図（模式図・グラフ）を、コードを書く前に短い文で決め、描いたあと1回だけ見て肉付けする。

    python <skill>/scripts/figdraft.py <work>            # 描く図ごとの下書きの雛形（グラフはデータの「驚き」入り）を出す
    python <skill>/scripts/figdraft.py <work> --check    # figs.py の図の関数に下書きがあるか、模式図が箱と矢印だけでないか
    （図の担当が2人のときは、どちらにも --part 1/2・--part 2/2 を付ける。自分の分の枚だけを出し・確かめる。図は figs_1.py・figs_2.py に描く）

図の関数（figs.py の def f_…）の説明（docstring）の頭に、次の行を書いてから描く：

    模式図：実物：<描く物（原子の並び・容器と液面・光路など。箱に文字を入れた物ではなく実物）>
            気づく：<見た人が気づく1点（左は規則的・右は乱れている、など）>
            配置：<左右で比べる・前後・断面・斜めから など>
            ラベル：<名詞だけ、3つまで>
    グラフ：気づく：<目立たせる差（データの「驚き」）。その棒・点を強調の色にし、引き出し線で一言>

弱いモデルの模式図が箱と矢印と名札だけになるのは、何に気づかせる図かを決めずにコードから書き始めるため。
描いたら figgrid.py の一覧を1回だけ見て、下書きと比べて足りない所（比べの相手・強調の色・引き出し線）を直す（見るのは1回まで）。
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEP = "\x1f"   # 構成の表の「図で見せる」と、図の案の表の「何をどう描く」の区切り
GRAPH_KINDS = ("棒グラフ", "折れ線", "概略グラフ", "帯グラフ", "年表")
SCHEMATIC_KEYS = ("実物", "気づく", "配置", "ラベル")
GRAPH_KEYS = ("気づく",)
# 模式図の関数で、これだけしか呼んでいなければ「箱と矢印だけ」（実物を描く線・点・図形が無い）
PLAIN_CALLS = {"blank", "save", "box", "arrow", "callout", "text", "annotate", "set_xlim", "set_ylim",
               "noticks", "axis", "set_axis_off", "Path", "print", "range", "enumerate", "zip", "len", "dict", "list"}


def plan_cells(work: Path):
    """(kind, {スライド番号: 図の案}, 設計メモの本文)。講座は「図の案」の表と、構成の表の「図で見せる」列を合わせる。"""
    import figplan
    import structures
    work = Path(work)
    kind = "memo" if (work / "memo.md").exists() else "outline"
    p = work / ("memo.md" if kind == "memo" else "outline.md")
    if not p.exists():
        return kind, {}, ""
    text = p.read_text(encoding="utf-8")
    cells = dict(figplan.plan_from_text(text, kind) or {})
    if kind == "memo":
        rows = structures._plan_table(text, "memo") or []
        i_fig = next((k for k, h in enumerate(rows[0]) if "図で見せる" in h), None) if rows else None
        for r in rows[1:] if i_fig is not None else []:
            if r and r[0].strip().isdigit() and len(r) > i_fig and r[i_fig].strip() not in ("", "—", "-"):
                n = int(r[0])
                if r[i_fig] not in cells.get(n, ""):
                    cells[n] = (r[i_fig] + SEP + cells[n]) if n in cells else r[i_fig]
    return kind, cells, text


def drawn(cells: dict) -> dict:
    """自分で描く図の枚だけ：{番号: (種類, 図の案)}。種類は「模式図」かグラフの名前。"""
    import figplan
    out = {}
    for n, c in sorted(cells.items()):
        parts = [x for x in c.split(SEP) if x.strip()]
        lead = next((x for x in parts if figplan.parse_fig(x)[0]), parts[0] if parts else "")   # 「目的：種類：中身」の形を優先
        if figplan.pptx_part(lead) is not None:
            continue
        _, k = figplan.parse_fig(lead)
        if k == "模式図" or k in GRAPH_KINDS:
            out[n] = (k, " ／ ".join(x.strip() for x in parts))
    return out


def template(n: int, kind: str, cell: str, text: str) -> str:
    """1枚の下書きの雛形（docstring の頭に書く行）。"""
    import data
    lines = [f"### {n}枚目（figs/s{n:02d}.png）：{cell}"]
    if kind == "模式図":
        lines += ["    実物：（描く物。箱に文字を入れた物ではなく、原子・粒子・容器・光路・装置の形）",
                  "    気づく：（見た人が気づく1点。比べるなら、比べの相手も同じ図に描く）",
                  "    配置：（左右で比べる／前後／断面／斜めから）",
                  "    ラベル：（名詞だけ、3つまで）"]
    else:
        ds = data.datasets(text)
        surprise = [ds[d]["fields"].get("驚き", "") for d in data.refs(cell) if d in ds]
        lines.append(f"    気づく：{surprise[0] if surprise and surprise[0] else '（目立たせる差。その棒・点を強調の色にし、引き出し線で一言）'}")
        if surprise:
            lines.append("    （データの「驚き」をそのまま下書きにした。その差の棒・点を強調の色にし、引き出し線で一言。ほかは灰色）")
    return "\n".join(lines)


def _text_of(node) -> str:
    """文字列と f 文字列（f"s{7:02d}.png" など、中身が定数のもの）を文字にする。変数の所は {}。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = ""
        for v in node.values:
            if isinstance(v, ast.Constant):
                out += str(v.value)
            elif isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Constant):
                spec = "".join(x.value for x in getattr(v.format_spec, "values", []) if isinstance(x, ast.Constant))
                try:
                    out += format(v.value.value, spec)
                except (ValueError, TypeError):
                    out += "{}"
            else:
                out += "{}"
        return out
    return ""


def all_functions(figs: Path) -> list:
    """figs.py の図の関数 [(関数名, docstring, 呼んだ名前の集合, 枚の番号の集合)]。番号は関数の中の「sNN」の文字列（と関数名）から。"""
    if not figs.exists():
        return []
    try:
        tree = ast.parse(figs.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    out = []
    for fn in [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name.startswith("f_")]:
        strs = " ".join(_text_of(c) for c in ast.walk(fn) if isinstance(c, (ast.Constant, ast.JoinedStr)))
        nums = {int(m) for m in re.findall(r"(?<![A-Za-z0-9])s(\d{2})(?:_[a-z])?(?:\.png)?", strs + " " + fn.name)}
        calls = set()
        for c in ast.walk(fn):
            if isinstance(c, ast.Call):
                f = c.func
                calls.add(f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else "")
        out.append((fn.name, ast.get_docstring(fn) or "", calls - {""}, nums))
    return out


def functions(figs: Path) -> dict:
    """figs.py の {スライド番号: [(関数名, docstring, 呼んだ名前の集合)]}。"""
    out: dict[int, list] = {}
    for name, doc, calls, nums in all_functions(figs):
        for n in nums:
            out.setdefault(n, []).append((name, doc, calls))
    return out


def has_key(doc: str, key: str) -> bool:
    return re.search(rf"(?m)^\s*{key}\s*[：:]\s*\S", doc) is not None or re.search(rf"{key}\s*[：:]\s*[^（(\s]", doc) is not None


FIG_SPLIT_AT = 8   # 自分で描く図がこの枚数以上で、制作役が2人なら、図の担当も2人（figs_1.py・figs_2.py）。
# 論文から作った講座の試しで、制作役2人は6分で書き終えたのに、図の担当1人が15枚を13分かけて描き、制作の段が図を待っていた
RUNNER = '''"""図の担当が2人で描いた figs_1.py・figs_2.py を順に動かす（brief.py が置いた。図を直すときは figs_N.py を直す）。"""
import runpy
from pathlib import Path

for p in sorted(Path(__file__).resolve().parent.glob("figs_[0-9].py")):
    runpy.run_path(str(p), run_name="__main__")
'''


def fig_files(work: Path) -> list:
    """図を描くスクリプト：figs.py と、図の担当が2人のときの figs_1.py・figs_2.py（あるものだけ）。"""
    work = Path(work)
    return [p for p in [work / "figs.py", *sorted(work.glob("figs_[0-9].py"))] if p.exists()]


def part_of(nums, part: str) -> list:
    """図の枚の番号を、part（"1/2"）の分だけ。前から順に、なるべく同じ数に分ける。"""
    k, n = (int(x) for x in part.split("/"))
    ns = sorted(nums)
    size = -(-len(ns) // n)
    return ns[(k - 1) * size:k * size]


def ensure_runner(work: Path) -> None:
    """図の担当が2人のとき、figs.py を、figs_1.py・figs_2.py を動かすだけのものにする（無ければ置く）。"""
    f = Path(work) / "figs.py"
    if not f.exists():
        f.write_text(RUNNER, encoding="utf-8")


def check(work: Path, part: str = "") -> list:
    work = Path(work)
    _, cells, _ = plan_cells(work)
    want = drawn(cells)
    if part:
        mine = set(part_of(want, part))
        want = {n: v for n, v in want.items() if n in mine}
    if not want:
        return [("・", "図の下書き", "自分で描く模式図・グラフの枚が図の案に無い")]
    files = fig_files(work)
    every = [x for f in files for x in all_functions(f)]
    if not every:
        return [("・", "図の下書き", "figs.py に図の関数（def f_…）がまだ無い（描いたら確かめる）")]
    fns: dict[int, list] = {}
    for f in files:
        for n, v in functions(f).items():
            fns.setdefault(n, []).extend(v)
    res, ok = [], []
    # 番号の読めない関数（ファイル名を変数で組んでいる など）も、少なくとも「気づく」の行は見る
    for name, doc, _, nums in every:
        if not nums and not has_key(doc, "気づく"):
            res.append(("✘", "図の下書き", f"{name}：説明に「気づく」の行が無い（`python <skill>/scripts/figdraft.py <work>` の雛形を埋める。"
                        "保存の名前は OUT / \"sNN.png\" と番号を書くと、どの枚の図か確かめられる）"))
    for n, (kind, _) in want.items():
        if n not in fns:
            res.append(("△", "図の下書き", f"{n}枚目（{kind}）：figs/s{n:02d}.png を書く図の関数が figs.py に見つからない（保存の名前に s{n:02d} を書く）"))
            continue
        name, doc, calls = fns[n][0]
        keys = SCHEMATIC_KEYS if kind == "模式図" else GRAPH_KEYS
        miss = [k for k in keys if not has_key(doc, k)]
        if miss:
            res.append(("✘", "図の下書き", f"{n}枚目 {name}（{kind}）：説明に「{'・'.join(miss)}」の行が無い"
                        f"（`python <skill>/scripts/figdraft.py <work>` の雛形を埋めてから描き直す）"))
            continue
        thing = re.search(r"実物\s*[：:]\s*(.*)", doc)
        if kind == "模式図" and not (calls - PLAIN_CALLS) and "箱" not in (thing.group(1) if thing else ""):   # 箱そのものが実物（トークンの箱など）なら除く
            res.append(("△", "図の下書き", f"{n}枚目 {name}：箱と矢印と文字だけの模式図。下書きの「実物」"
                        "（粒子・容器・光路など）を、線・点・図形（plot・particles・draw_disks・cylinder・Rectangle など）で描く"))
            continue
        ok.append(n)
    if ok:
        res.append(("✔", "図の下書き", "・".join(f"{n}枚目" for n in ok)))
    return res


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 0
    work = Path(argv[0])
    part = argv[argv.index("--part") + 1] if "--part" in argv and argv.index("--part") + 1 < len(argv) else ""
    if "--check" in argv:
        import report
        res = check(work, part)
        report.show(res, "--all" in argv)
        return 1 if any(m == "✘" for m, _, _ in res) else 0
    _, cells, text = plan_cells(work)
    want = drawn(cells)
    if part:
        mine = set(part_of(want, part))
        want = {n: v for n, v in want.items() if n in mine}
    if not want:
        print("自分で描く模式図・グラフの枚は、図の案に無い")
        return 0
    print("図の関数（def f_…）の説明の頭に、次の行を埋めて書いてから描く。描いたら figgrid.py の一覧を1回だけ見て、下書きと比べて直す。\n")
    print("\n\n".join(template(n, k, c, text) for n, (k, c) in want.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""手持ちのスライド(.pptx)からスライドを全て取り除き、マスター/レイアウト/テーマだけを残したテンプレートを作る。

同梱のテンプレート（assets/templates/ の テンプレート1〜8。名前を言わなければ テンプレート1）は変えない。
別のテンプレートを使いたくなったら、名前を付けて**追加**する（使うときに名前で選ぶ）。

使い方（ふつうはこちら）:
    python make_template.py --from-folder [作業フォルダ] [--name 名前] [--source 元のファイル名]
      作業フォルダ（スライドを作るフォルダの一番上）の「スライドテンプレート」フォルダに置いた pptx
      （--source が無ければいちばん新しいもの）から「スライドテンプレート/<名前>_テンプレート.pptx」を作り、
      同じフォルダの「テンプレート一覧.md」に「### <名前>」として追加する（名前の既定は元のファイル名）。
      同じ名前がすでにあれば作り直して上書きする。既定のテンプレートは変えない。
      元のスライドを analyze_template.py で分析し、同じフォルダに次の2つも作る：
        <名前>_テンプレート.json   見た目の設定（色・見出しの印・まとめの帯の寄せ）。zemi.py がテンプレートと一緒に読む
        <名前>_テンプレートの分析.md  分析の表（48項目と、研究発表の手引きの目安）。ユーザーに見せる

ファイルを直接指定するとき:
    python make_template.py <元のスライド.pptx> <出力 template.pptx>

テンプレートのデザインを変えたくなったら、PowerPoint で元のデッキのスライドマスターを編集してから作り直せばよい。
"""
import sys
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zemi import SLIDE_H, SLIDE_W, band_placeholder_idx, pick_layouts  # noqa: E402
import slide_profile  # noqa: E402
import analyze_template  # noqa: E402

DROP_RELTYPES = ("changesInfo", "revisionInfo")  # 編集履歴は削除したスライドを参照しているので捨てる
FOLDER = slide_profile.TEMPLATE_FOLDER
SUFFIX = "_テンプレート.pptx"


def strip_slides(src, dst):
    prs = Presentation(src)
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        prs.part.drop_rel(sldId.rId)
        sldIdLst.remove(sldId)
    for rId, rel in list(prs.part.rels.items()):
        if rel.reltype.endswith(DROP_RELTYPES):
            prs.part.drop_rel(rId)
    prs.save(dst)
    return Presentation(dst)


def report(prs):
    """選ばれるレイアウトと青帯の枠の有無、大きさを返す（テンプレート一覧に書く値）。"""
    lc, lt = pick_layouts(prs)
    band = band_placeholder_idx(lc, prs.slide_height)
    w, h = prs.slide_width / 914400, prs.slide_height / 914400
    return {"本文のレイアウト": lc.name, "表紙のレイアウト": lt.name,
            "青帯の枠": "あり" if band is not None else "なし（zemi が同じ位置に青帯を描く）",
            "大きさ": f"{w:.2f}×{h:.2f} in" + ("" if abs(w - SLIDE_W) < 0.05 and abs(h - SLIDE_H) < 0.05 else "（16:9 でない。部品の位置がずれる）")}


def set_profile_entry(path, section, sub, values):
    """一覧のファイルの `## section` の中の `### sub` を values の `- 項目: 値` で置き換える（無ければ節の末尾に足す。節もファイルも無ければ作る）。"""
    if not Path(path).exists():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("# 追加したテンプレート\n\n頼むときに「テンプレートは〇〇で」と名前で選ぶ（make_template.py が書く）。\n\n## テンプレート\n",
                              encoding="utf-8")
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == f"## {section}")
    except StopIteration:
        lines += ["", f"## {section}"]
        start = len(lines) - 1
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    block = [f"### {sub}"] + [f"- {k}: {v}" for k, v in values.items()]
    s = next((i for i in range(start + 1, end) if lines[i].strip() == f"### {sub}"), None)
    if s is not None:   # 同じ名前があれば置き換える
        e = next((i for i in range(s + 1, end) if lines[i].startswith("### ")), end)
        while e > s + 1 and not lines[e - 1].strip():
            e -= 1
        lines[s:e] = block
    else:               # 無ければ節の末尾に足す
        last = max((i for i in range(start + 1, end) if lines[i].strip()), default=start)
        lines[last + 1:last + 1] = [""] + block
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def from_folder(start=None, name=None, source=None):
    base = Path(start or Path.cwd()).resolve()
    folder = next((d / FOLDER for d in [base, *base.parents] if (d / FOLDER).is_dir()), base / FOLDER)
    prof = folder / slide_profile.REGISTRY
    srcs = sorted((p for p in folder.glob("*.pptx") if not p.name.endswith(SUFFIX) and not p.name.startswith("~$")),
                  key=lambda p: p.stat().st_mtime, reverse=True) if folder.exists() else []
    if source:
        srcs = [p for p in srcs if p.name == source]
    if not srcs:
        folder.mkdir(exist_ok=True)
        sys.exit(f"テンプレートにしたい pptx を {folder} に置いてから、もう一度実行する" + (f"（{source} が無い）" if source else ""))
    src = srcs[0]
    name = name or src.stem
    dst = folder / f"{name}{SUFFIX}"
    prs = strip_slides(src, dst)
    info = report(prs)
    import io
    import json
    from contextlib import redirect_stdout
    res = analyze_template.analyze(src)
    dst.with_suffix(".json").write_text(json.dumps(res["style"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    buf = io.StringIO()
    with redirect_stdout(buf):
        analyze_template.print_report(res)
    md = folder / f"{name}_テンプレートの分析.md"
    md.write_text(f"# テンプレート「{name}」の分析\n\n" + buf.getvalue(), encoding="utf-8")
    set_profile_entry(prof, "テンプレート", name, {
        "pptx": f"{FOLDER}/{dst.name}",
        "元のスライド": f"{FOLDER}/{src.name}",
        "本文のレイアウト": info["本文のレイアウト"],
        "表紙のレイアウト": info["表紙のレイアウト"],
    })
    print(f"テンプレート「{name}」を追加した（元のスライド: {src.name}）。既定のテンプレートは同梱のまま")
    print(f"saved {dst}")
    print(f"saved {dst.with_suffix('.json')}（見た目の設定）")
    print(f"saved {md}（分析の表。ユーザーに見せる）")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print("  見た目の設定: " + json.dumps(res["style"], ensure_ascii=False))
    print(f"一覧: {prof} に「### {name}」を書いた")
    print(f"  使うとき：頼むときに「テンプレートは{name}で」と言う（構成案のオプションの「テンプレート」に入る）")
    print("  レイアウトが違うときは「本文のレイアウト」「表紙のレイアウト」を次のどれかに直す: "
          + " / ".join(repr(l.name) for l in prs.slide_layouts))


def main():
    a = sys.argv[1:]
    if a and a[0] == "--from-folder":
        opts, rest = {}, []
        it = iter(a[1:])
        for x in it:
            if x in ("--name", "--source"):
                opts[x[2:]] = next(it, None)
            else:
                rest.append(x)
        from_folder(rest[0] if rest else None, opts.get("name"), opts.get("source"))
    elif len(a) == 2:
        prs = strip_slides(a[0], a[1])
        print(f"saved {a[1]}  layouts={[l.name for l in prs.slide_layouts]}")
        for k, v in report(prs).items():
            print(f"  {k}: {v}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

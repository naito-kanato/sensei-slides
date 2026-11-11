"""そのデッキの設定（オプションの一覧）を読む。スキル全体の共通プロフィールは置かない（設定はデッキごと）。

設定の置き場所：
  ゼミ：構成案 outline.md の `## オプション` の表（| オプション | 今の値 |）
  講座：各回の設計メモ memo.md の1節の `- 項目：値` の行（講座の README の「学習者とゴール」から写す）
  追加したテンプレート：作業フォルダの `スライドテンプレート/テンプレート一覧.md`（make_template.py が書く）

    python slide_profile.py --table [--kind ゼミ|講座] [--set 項目=値 ...]   # 始めるときに見せる一覧（必須の抜けに印）
    python slide_profile.py <作業フォルダ>                                   # そのデッキの設定と、追加したテンプレート

build.py から：
    from slide_profile import load_profile, author, deck_options
    P = load_profile(HERE)          # 作業フォルダの outline.md（講座は memo.md）の設定と、追加したテンプレート
    AUTHOR = author(P)              # 表紙の名前（一覧に書いてなければ空文字）
    deck = Deck(workdir=HERE / "build", **deck_options(P))   # 一覧の「テンプレート」「色」。無ければ同梱のテンプレート1
"""
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE_FOLDER = "スライドテンプレート"   # 追加のテンプレートの元と出力を置く、作業フォルダの中のフォルダ
REGISTRY = "テンプレート一覧.md"           # 追加したテンプレートの一覧（スライドテンプレート/ の中）
DEFAULT_TEMPLATE = "同梱（既定）"
BUNDLED_DIR = SKILL / "assets" / "templates"   # 同梱のテンプレート（名前＝ファイル名。テンプレート1〜8、番号は見やすさの順。色は 配色.json）
BUNDLED = BUNDLED_DIR / "テンプレート1.pptx"   # 名前を言わないときのテンプレート

# 聞き手のテーマへの詳しさ → 丁寧さ（推論距離のつまみ。references/inference-distance.md 1節）
FAMILIARITY = {"初学者": 0, "多少知っている": 0, "かなり知っている": 1}   # 選択肢は「初学者・多少知っている」と「かなり知っている」の2つ（前の3つの言葉も読める）
FAMILIARITY_KEY = "聞き手のテーマへの詳しさ"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse(text):
    """`## 節` → `### 小節` → `- 項目: 値` を入れ子の dict に。小節のない節は {項目: 値}。空欄の項目は入れない。"""
    out, sec, sub = {}, None, None
    for line in text.splitlines():
        if m := re.match(r"^##\s+(.+?)\s*$", line):
            sec, sub = m.group(1), None
            out.setdefault(sec, {})
        elif m := re.match(r"^###\s+(.+?)\s*$", line):
            sub = m.group(1)
            if sec is not None:
                out[sec].setdefault(sub, {})
        elif (m := re.match(r"^-\s*([^:：]+?)\s*[:：]\s*(.*?)\s*$", line)) and sec is not None:
            key, val = m.group(1), m.group(2)
            if not val:
                continue
            (out[sec][sub] if sub else out[sec])[key] = val
    return out


def read_options(text: str) -> dict:
    """設定の一覧 {項目: 値}：`## オプション` の表の行と、講座の設計メモの1節の `- 項目：値` の行。"""
    out = {}
    sec = re.search(r"^##\s*オプション\s*$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if sec:
        for line in sec.group(1).splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.strip().startswith("|") and len(cells) >= 2 and cells[0] not in ("オプション", "") and not set(cells[0]) <= set("-: "):
                if cells[1] and cells[1] not in ("（未設定）", "—"):
                    out[cells[0]] = cells[1]
    sec = re.search(r"^##\s*1\.[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    if sec:
        for m in re.finditer(r"^-\s*([^:：\n]+?)\s*[:：]\s*(.+?)\s*$", sec.group(1), re.M):
            out.setdefault(m.group(1), m.group(2))
    return out


def find_registry(start=None):
    """start から親へたどって、最初に見つかった `スライドテンプレート/テンプレート一覧.md`。無ければ None。"""
    p = Path(start or Path.cwd()).resolve()
    for d in [p, *p.parents]:
        f = d / TEMPLATE_FOLDER / REGISTRY
        if f.exists():
            return f
    return None


def load_profile(start=None):
    """そのデッキの設定 {"オプション": {...}, "テンプレート": {...}, "_path": 一覧の場所}。start は作業フォルダ（outline.md か memo.md のある所）。
    見つからなければ空の dict（同梱のテンプレート1・名前なしで作る）。"""
    d = {}
    folder = Path(start or Path.cwd()).resolve()
    for name in ("outline.md", "memo.md"):
        f = folder / name
        if f.exists():
            d["オプション"] = read_options(f.read_text(encoding="utf-8"))
            d["_options_path"] = str(f)
            break
    if (folder / "memo.md").exists() and re.search(r"_\d{2}$", folder.name):   # 講座の回：講座名と回数（表紙の名前の既定）
        course = re.sub(r"_\d{2}$", "", folder.name)
        root = folder.parent.parent if folder.parent.name == "_work" else folder.parent
        readme = root / course / "00_README.md"
        total = None
        if readme.exists():
            t = readme.read_text(encoding="utf-8")
            m = re.search(r"全\s*(\d+)\s*回", t)
            total = int(m.group(1)) if m else (len(re.findall(r"^\|\s*\d+\s*\|", t, re.M)) or None)
        d["_course"] = (course, total)
    reg = find_registry(folder)
    if reg:
        d["テンプレート"] = parse(reg.read_text(encoding="utf-8")).get("テンプレート", {})
        d["_path"] = str(reg)
    return d


def option(p, key, default=None):
    return p.get("オプション", {}).get(key, default)


def author(p):
    """表紙の名前。発表：一覧の「発表者名」、無ければ空（表紙に名前の行を作らない。仮の名前を入れない）。
    講座：「講座名（全N回）」、学習者の名前があれば「講座名（全N回）・〇〇さん向け」。"""
    if p.get("_course"):
        course, total = p["_course"]
        head = f"{course}（全{total}回）" if total else course
        who = option(p, "学習者の名前")
        return option(p, "発表者名") or (f"{head}・{who}さん向け" if who else head)
    return option(p, "発表者名") or option(p, "学習者の名前") or ""


def politeness(p):
    """丁寧さ：一覧に書いてあればその値、無ければ聞き手のテーマへの詳しさから（初学者・多少知っている 0・かなり知っている 1）。"""
    v = option(p, "丁寧さ")
    if v and re.search(r"\d", v):
        return int(re.search(r"\d", v).group(0))
    return level_of(option(p, FAMILIARITY_KEY))


def level_of(familiarity):
    """詳しさの言葉 → 丁寧さ。分からなければ None。"""
    for k, v in FAMILIARITY.items():
        if familiarity and k in familiarity:
            return v
    return None


def bundled_templates():
    """同梱のテンプレート {名前: {pptx}}。一覧に書かなくても、名前で選べる。"""
    return {f.stem: {"pptx": str(f)} for f in sorted(BUNDLED_DIR.glob("*.pptx"))} if BUNDLED_DIR.is_dir() else {}


def templates(p):
    """使えるテンプレート {名前: {pptx, 元のスライド, 本文のレイアウト, 表紙のレイアウト}}：同梱のものと、追加したもの（同じ名前なら追加したほう）。"""
    return {**bundled_templates(), **{k: v for k, v in p.get("テンプレート", {}).items() if isinstance(v, dict)}}


def structure_names():
    """同梱のテンプレートの構造の名前 → ファイルの名前（{"下の帯": "テンプレート4", …}）。構造の名前でも選べるようにする（「結論の囲みで」）。"""
    import json
    out = {}
    for f in sorted(BUNDLED_DIR.glob("テンプレート*.json")) if BUNDLED_DIR.is_dir() else []:
        try:
            out[json.loads(f.read_text(encoding="utf-8"))["label"]] = f.stem
        except Exception:
            pass
    return out


def _clean(name):
    return re.sub(r"（.*?）|\(.*?\)", "", name).strip() if name else name


def template_name(p, name=None, place_name=None):
    """使うテンプレートの名前：依頼で指定した名前 → 一覧の「テンプレート」 → 無ければ None（同梱の既定）。
    名前は「テンプレート3」でも、構造の名前（「結論の囲み」）でもよい。place_name は使わない（互換のため残す）。"""
    for n in (_clean(name), _clean(option(p, "テンプレート"))):
        if n and n not in templates(p) and n in structure_names():
            n = structure_names()[n]
        if n and n != DEFAULT_TEMPLATE and not n.startswith("同梱"):
            if n in templates(p):
                return n
            print(f"[WARN] テンプレート「{n}」が無いので同梱のものを使う（使える名前: {list(templates(p))}）")
    return None


def template(p, name=None, place_name=None, _resolved=False):
    """テンプレートの pptx のパス。既定は同梱の テンプレート1（assets/templates/、変えない）。追加したテンプレートは名前で選ぶ。"""
    n = name if _resolved else template_name(p, name)
    if n:
        tp = Path(templates(p)[n].get("pptx", ""))
        if not tp.is_absolute() and p.get("_path"):
            tp = Path(p["_path"]).parent.parent / tp
        if tp.exists():
            return tp
        print(f"[WARN] テンプレート「{n}」の pptx {tp} が見つからないので同梱のものを使う")
    return BUNDLED


# 始めるときに聞く一覧：(項目, 既定値, 選べる値・説明, 必須か)。kind＝ゼミ／講座で出す行が変わる
OPTIONS = [
    (FAMILIARITY_KEY, "", "初学者・多少知っている／かなり知っている（丁寧さがこれで決まる）", True),
    ("丁寧さ", "", "詳しさから（初学者・多少知っている 0・かなり知っている 1）。1枚に許す「あとで使う前提」の穴の数。変えてもよい", False),
    ("資料", "なし", "なし（テーマだけから。事実は出典で確かめる）／フォルダに入れたもの（materials.py が 資料/ に格納）", False),
    ("聞き手のプロフィール", "", "任意：専門・研究テーマ・よく知っていること（書くと言い換えと止まる所の判定がよくなる）", False),
    ("発表者名", "", "表紙に出す名前（任意）", False),
    ("原稿のモード", "発表", "発表（自分が話す）／AI講義（AIが講師）", False),
    ("発表時間", "", "任意：分（決まっていれば。原稿の長さと枚数の目安に使う）", False),
    ("枚数の目安", "", "本文の枚数の目安（表紙・区切りを除く）。空なら発表時間÷1.5〜2分", False),
    ("枚数が少ないとき", "足さない（短くてよい）", "足さない（短くてよい）／説明を厚くする", False),
    ("答えの位置", "", "先（問いのすぐ後で答えを言い、あとの枚で根拠。Minto 流。発表の既定）／後（前で問いを立て、後ろ3分の1で答えを回収。講座の既定）", False),
    ("ねらい", "", "資料の種類から（論文を紹介する（問題から／方法から）・教科書の節を読む・自分の研究を伝える・提案して納得してもらう など）。"
     "既定の話の型が決まる（python <skill>/scripts/story.py --aims）。講座は地図の「ねらい」の列", False),
    ("範囲", "全部の結果", "全部の結果／主要な結果に絞る", False),
    ("議論のスライド", "入れない", "入れる（疑問点・限界・自分の研究との関係）／入れない", False),
    ("構成案の確認", "見せる", "見せる／任せる（見せずに完成まで）", False),
    ("出力先", "発表フォルダ（<資料名>/）", "スライドと原稿のページを置くフォルダ（資料置き場 資料/ と同じフォルダ）", False),
    ("本文の形の割合", "", "任意：手本にしたい自分のデッキから analyze_structure.py が数えた1行（構成案で本文の形をこの割合に寄せる）", False),
    ("回数の上限", "標準", "標準（担当の起動・make_deck の回数に上限。仕上げの make_deck は4回など）／多め（2倍）／なし。使いすぎを防ぐ", False),
    ("トークンの上限", "Codex 250万・Antigravity 200万・Claude Code 700万", "1回で使ってよいトークン（キャッシュの読みは1/10で数える）を道具ごとに。超えたら止めて聞き、続けてよければ同じ量だけ足して再開する。「なし」で見ない", False),
    ("担当ごとのトークンの上限", "大30%・中25%・小10%", "担当1人（会話1本）が使ってよいトークンを、トークンの上限に対する割合で。大＝仕上げ役・制作役、"
     "中＝設計・裏取り・数字を探す・レビュー・直し・仕上げの直し・完成後のレビュー、小＝地図。超えたら止めて聞く。「なし」で見ない", False),
    ("使用量の上限", "月20%・週40%", "1回（講座の1回・発表の1つ）で使ってよい使用量の枠の％を、枠ごとに（月・週・5時間。例「月20%・週40%・5時間80%」、見ない枠は「なし」）。"
     "超えたら続ける前に聞く。道具が記録に残す枠だけ測れる（今は Codex。どの枠があるかはプランによる）", False),
]
COURSE_SKIP = {"ねらい", "発表者名", "原稿のモード", "発表時間", "枚数の目安", "枚数が少ないとき", "範囲", "議論のスライド", "構成案の確認", "出力先", "本文の形の割合"}


def options_table(p=None, overrides=None, kind="ゼミ"):
    """始めるときにユーザーに見せる一覧（Markdown）。必須の項目が空なら「（必須・未設定）」と出す。
    overrides = 依頼文や答えから決まった値 {項目: 値}。丁寧さは、書いていなければ詳しさから入れる。"""
    ov = dict(overrides or {})
    p = p or {}
    cur = {**p.get("オプション", {}), **ov}
    if "丁寧さ" not in cur and level_of(cur.get(FAMILIARITY_KEY)) is not None:
        cur["丁寧さ"] = f"{level_of(cur[FAMILIARITY_KEY])}（詳しさから）"
    rows = []
    for key, default, choices, required in OPTIONS:
        if kind == "講座" and key in COURSE_SKIP:
            continue
        if key == "答えの位置" and not cur.get(key):
            default = "後（講座の既定）" if kind == "講座" else "先（発表の既定）"
        v = cur.get(key) or default or ("（必須・未設定）" if required else "（任意・未設定）" if "任意" in choices else "（未設定）")
        rows.append((key, v, choices))
    tv = cur.get("テンプレート") or DEFAULT_TEMPLATE
    rows.append(("テンプレート", tv, "／".join([DEFAULT_TEMPLATE, *templates(p)]) + "（追加は「テンプレを追加して」）"))
    rows.append(("色", cur.get("色") or "テンプレートの標準", "青・紺とオレンジ・生成りと山吹・藍・青緑・珊瑚・墨と山吹・深緑・グレーと赤・墨と藍"))
    lines = ["| オプション | 今の値 | 選べる値 |", "|---|---|---|"]
    lines += [f"| {k} | {v} | {c} |" for k, v, c in rows]
    return "\n".join(lines)


def missing_required(values: dict, kind="ゼミ"):
    """必須の項目で空のもの（一覧の値 {項目: 値} から）。"""
    return [k for k, _, _, req in OPTIONS if req and not (kind == "講座" and k in COURSE_SKIP)
            and not (values.get(k) and "未設定" not in values.get(k, ""))]


def deck_options(p, name=None, place_name=None, color=None):
    """Deck(...) に渡す引数：テンプレート（構造）と、使うレイアウトの名前と、配色。既定は同梱の テンプレート1 の標準の色。
        deck = Deck(workdir=HERE / "build", **deck_options(P))                                # 一覧の「テンプレート」「色」
        deck = Deck(workdir=HERE / "build", **deck_options(P, name="テンプレート3", color="深緑"))   # 構造と色を名前で
    色は、color → 一覧の「色」 → 無ければテンプレートの標準の色（assets/templates/配色.json の名前）。"""
    n = template_name(p, name)
    t = templates(p).get(n, {}) if n else {}
    c = color or option(p, "色")
    out = {"template": template(p, n, _resolved=True),
           "content_layout": t.get("本文のレイアウト"), "title_layout": t.get("表紙のレイアウト")}
    if c and c not in ("標準", "既定", "テンプレートの標準"):
        out["color"] = c
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("start", nargs="?", help="作業フォルダ（省略時は今のフォルダ）")
    ap.add_argument("--table", action="store_true", help="始めるときに見せる一覧（Markdown）を出す")
    ap.add_argument("--kind", default="ゼミ", choices=["ゼミ", "講座"])
    ap.add_argument("--set", action="append", default=[], metavar="項目=値", help="依頼文や答えで決まった値（何度でも）")
    a = ap.parse_args()
    p = load_profile(a.start)
    ov = dict(s.split("=", 1) for s in a.set if "=" in s)
    if a.table:
        print(options_table(p, ov, a.kind))
        miss = missing_required({**p.get("オプション", {}), **ov}, a.kind)
        if miss:
            print(f"\n必須の抜け：{'・'.join(miss)}（【質問】で聞いてから進める）")
        return 0
    opts = p.get("オプション", {})
    print(f"設定：{p.get('_options_path', '（outline.md・memo.md が無い）')}")
    print("  " + ("、".join(f"{k}={v}" for k, v in opts.items()) if opts else "（まだ無い）"))
    print(f"  丁寧さ：{politeness(p) if politeness(p) is not None else '（未設定）'}　表紙の名前：{author(p) or '（無し）'}")
    print(f"  テンプレート：既定＝{BUNDLED.name}　追加済み：{'、'.join(p.get('テンプレート', {})) or 'なし'}"
          + (f"（{p['_path']}）" if p.get("_path") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

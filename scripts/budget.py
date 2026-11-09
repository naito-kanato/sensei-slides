"""回数の予算：1回の講座・1つの発表で、担当を何回起動し、make_deck を何回回したかを数え、上限で止める（道具・モデルによらない）。

    python <skill>/scripts/budget.py <work>                   # 今の回数・トークンと上限の一覧
    python <skill>/scripts/budget.py <work> --allow-tokens    # ユーザーが「続けてよい」と言ったとき：トークンの上限を1回分足す

数え方
  - 担当の起動：brief.py が依頼文を出すたびに <work>/budget_log.jsonl に1行（同じ担当・同じ分担が15分以内にもう一度なら数えない）
  - make_deck：build_log.jsonl の行（仕上げと、完成後のレビューのあとの直しを分けて数える。make_deck.py）
上限はオプション「回数の上限」で変える：標準（下の表）／多め（2倍）／なし。上限を超えて続けるのは、ユーザーが許したときだけ（--over）。
トークン：この作業フォルダを扱った会話のトークン（入力＋キャッシュの書き＋キャッシュの読み×0.1＋出力）を道具ごとに足し、
  オプション「トークンの上限」（既定 Codex 250万・Antigravity 200万・Claude Code 700万）で止める。brief.py・make_deck.py が上限で ✘ を出す。
  ユーザーが続けてよいと言ったら --allow-tokens で記録し、上限を同じ量だけ足して再開する。
使用量の％（オプション「使用量の上限」、既定 月20%・週40%）は別に next_step が見る（枠の％が記録に残る道具だけ）。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = "budget_log.jsonl"
ROLE_CAPS = {   # 1回の講座・1つの発表で、担当を起動してよい回数（標準）
    "数字を探す担当": 2, "設計の担当": 1, "裏取りの担当": 2, "レビュー担当の先読み": 1, "レビュー担当": 2, "直しの担当": 2,
    "制作役": 2, "仕上げ役": 1, "完成後のレビュー担当": 1, "仕上げの直しの担当": 2,
}
MAKE_DECK_CAPS = {"仕上げ": 4, "完成後のレビューのあとの直し": 2}
SAME_WITHIN = 15 * 60   # 同じ担当が依頼文を読み直しただけなら数えない
DEFAULT_PERCENT = 20


def scale(work: Path) -> float | None:
    """オプション「回数の上限」：標準 1、多め 2、なし None。"""
    try:
        import slide_profile
        v = slide_profile.option(slide_profile.load_profile(work), "回数の上限", "標準") or "標準"
    except Exception:
        v = "標準"
    if "なし" in v:
        return None
    return 2.0 if "多め" in v else 1.0


WINDOWS = ("5時間", "週", "月")
DEFAULT_PERCENTS = {"5時間": None, "週": 40.0, "月": 20.0}   # 1回（講座の1回・発表の1つ）で使ってよい枠の％。None は見ない


def window_name(minutes) -> str | None:
    """枠の長さ（分）→ 5時間・週・月。"""
    if not minutes:
        return None
    return "5時間" if minutes <= 12 * 60 else "週" if minutes <= 14 * 24 * 60 else "月"


def percent_limits(work: Path) -> dict:
    """オプション「使用量の上限」：「月20%・週40%・5時間80%」のように枠ごと。書いていない枠は既定。数だけなら月の枠。"""
    import re
    try:
        import slide_profile
        v = slide_profile.option(slide_profile.load_profile(work), "使用量の上限", "") or ""
    except Exception:
        v = ""
    out = dict(DEFAULT_PERCENTS)
    found = False
    for name in WINDOWS:
        m = re.search(name + r"\s*[:：]?\s*(\d+(?:\.\d+)?|なし)", v)
        if m:
            out[name] = None if m.group(1) == "なし" else float(m.group(1))
            found = True
    if not found:
        m = re.search(r"(\d+(?:\.\d+)?)", v)
        if m:
            out["月"] = float(m.group(1))
    return out


def percent_limit(work: Path) -> float:
    """月の枠の上限（%）。"""
    return percent_limits(work)["月"] or DEFAULT_PERCENT


def used_by_window(points) -> dict:
    """[(時刻, 枠の長さ（分）, 使った％)] → {枠の名前: この回で増えた％}。
    同時に動いた担当が同じ枠の％を少しずつずれて書くので、1つずつの増え方は足さない。枠がリセットされる（％が大きく下がる）までの区切りごとに
    「最大 − 最小」を取り、区切りどうしを足す。"""
    by = {}
    for t, minutes, pct in sorted(points, key=lambda x: x[0]):
        name = window_name(minutes)
        if name:
            by.setdefault(name, []).append(pct)
    out = {}
    for name, ps in by.items():
        total, seg = 0.0, [ps[0]]
        for a, b in zip(ps, ps[1:]):
            if b < max(seg) - RESET_DROP:   # リセット
                total += max(seg) - min(seg)
                seg = []
            seg.append(b)
        out[name] = total + max(seg) - min(seg)
    return out


RESET_DROP = 15.0   # これより大きく下がったら、枠がリセットされたとみなす（％）


def cap(work: Path, base: int) -> int | None:
    s = scale(work)
    return None if s is None else int(round(base * s))


def load(work: Path) -> list[dict]:
    p = Path(work) / LOG
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def count(work: Path, role: str) -> int:
    return sum(1 for r in load(work) if r.get("role") == role)


def changed_since(work: Path, ts: float) -> bool:
    """ts のあとに、作業フォルダのファイル（記録のファイルは除く）が書き換わったか。"""
    skip = {LOG, "run_record.md", "run_record.json"}
    return any(f.stat().st_mtime > ts for f in Path(work).rglob("*") if f.is_file() and f.name not in skip)


def same_launch(work: Path, last: dict | None) -> bool:
    """前の記録と同じ起動とみなすか：15分以内（依頼文の読み直し）か、そのあと作業フォルダに何も書かれていない
    （メインが依頼文を確かめただけ・起動が途中で失敗した、など。働いていない起動は数えない）。"""
    if not last:
        return False
    return time.time() - last.get("ts", 0) < SAME_WITHIN or not changed_since(work, last.get("ts", 0))


def record(work: Path, role: str, part: str = "") -> bool:
    """1回分を足す（同じ起動とみなせるなら足さない）。足したら True。"""
    now = time.time()
    last = next((r for r in reversed(load(work)) if r.get("role") == role and r.get("part", "") == part), None)
    if same_launch(work, last):
        return False
    with (Path(work) / LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": now, "role": role, "part": part},
                           ensure_ascii=False) + "\n")
    return True


def check_role(work: Path, role: str, part: str = "", over: bool = False) -> str | None:
    """上限なら止める理由の文。止めないなら None（そのとき1回分を記録する）。"""
    base = ROLE_CAPS.get(role)
    c = None if base is None else cap(work, base)
    if c is not None and not over:
        n = count(work, role)
        last = next((r for r in reversed(load(work)) if r.get("role") == role and r.get("part", "") == part), None)
        if n >= c and not same_launch(work, last):
            return (f"✘ 回数の上限：担当「{role}」の起動は、この回 {c} 回まで（もう {n} 回）。ここで止める。"
                    "メインはユーザーに【質問】で聞く（続ける・ここで止める）。続けるなら、ユーザーの答えを添えて brief.py に --over を付ける")
    record(work, role, part)
    return None


# ---- トークンの上限（道具ごと。キャッシュの読みは 1/10 で数える）。超えたら止めてユーザーに聞き、許可されたら同じ量だけ足して再開する
TOKEN_CAPS = {"Codex": 2_500_000, "Antigravity": 2_000_000, "Claude Code": 7_000_000}
TOOL_NAMES = {"codex": "Codex", "antigravity": "Antigravity", "claude": "Claude Code"}


def weighted(r: dict) -> float:
    """会話1本のトークン：入力＋キャッシュの書き＋キャッシュの読み×0.1＋出力（思考を含む）。"""
    return r.get("input", 0) + r.get("cache_write", 0) + 0.1 * r.get("cache_read", 0) + r.get("output", 0)


def token_caps(work: Path) -> dict:
    """オプション「トークンの上限」：「Codex 250万・Antigravity 200万・Claude Code 700万」の形。書いていない道具は既定。「なし」は見ない。"""
    import re
    try:
        import slide_profile
        v = slide_profile.option(slide_profile.load_profile(work), "トークンの上限", "") or ""
    except Exception:
        v = ""
    out = dict(TOKEN_CAPS)
    if v.strip() == "なし":
        return {k: None for k in out}
    for key, name in TOOL_NAMES.items():
        m = re.search(key + r"[^0-9な]*?(\d+(?:\.\d+)?)\s*(万)?|" + key + r"[^0-9]*?(なし)", v, re.I)
        if m:
            out[name] = None if m.group(3) else float(m.group(1)) * (10_000 if m.group(2) else 1)
    return out


def window_rows(work: Path) -> list:
    """この作業フォルダを扱った会話（run_record の行）のうち、作業フォルダに書いていた間と重なるもの。"""
    import run_record
    lo_t, hi_t = active_window(work)
    return [r for r in run_record.collect(Path(work))
            if not (r.get("start") is not None and (r["start"] > hi_t or (r.get("end") or r["start"]) < lo_t))]
    # 重ならない会話（あとで別の回が読んだだけ、など）は数えない


def token_usage(work: Path, rows: list | None = None) -> dict:
    """{道具: この作業フォルダを扱った会話のトークン（重み付き）}。"""
    used = {}
    for r in window_rows(work) if rows is None else rows:
        used[r["tool"]] = used.get(r["tool"], 0) + weighted(r)
    return used


# 役ごとの上限：道具ごとの全体の上限（TOKEN_CAPS）に対する割合。3段（大・中・小）。担当1人（会話1本）ごとに見る。
# ソネット・Codex の回の記録から：ふつうの回はどの役も届かず、暴走した担当（Codex の仕上げ役が make_deck を21回）だけが届く大きさ
ROLE_TIERS = {"大": ("仕上げ役", "制作役"),
              "中": ("設計の担当", "裏取りの担当", "レビュー担当", "直しの担当", "仕上げの直しの担当", "完成後のレビュー担当"),
              "小": ("数字を探す担当", "レビュー担当の先読み", "地図の担当")}
ROLE_SHARES = {"大": 0.25, "中": 0.18, "小": 0.08}


def role_shares(work: Path) -> dict | None:
    """オプション「担当ごとのトークンの上限」：「大25%・中18%・小8%」の形。「なし」は見ない。"""
    import re
    try:
        import slide_profile
        v = slide_profile.option(slide_profile.load_profile(work), "担当ごとのトークンの上限", "") or ""
    except Exception:
        v = ""
    if v.strip() == "なし":
        return None
    out = dict(ROLE_SHARES)
    for k in out:
        m = re.search(k + r"\s*(\d+(?:\.\d+)?)\s*[%％]", v)
        if m:
            out[k] = float(m.group(1)) / 100
    return out


def tier_of(role: str | None) -> str | None:
    return next((t for t, roles in ROLE_TIERS.items() if role in roles), None)


def role_allowances(work: Path) -> dict:
    """{会話のファイル名（拡張子なし）か "all": ユーザーが「続けてよい」と言った回数}。"""
    n = {}
    for r in load(work):
        if r.get("type") == "allow_role_tokens":
            n[r.get("conv", "all")] = n.get(r.get("conv", "all"), 0) + 1
    return n


def role_over(work: Path, rows: list | None = None) -> list:
    """上限を超えた担当 [(役, 段, 会話の名前, 会話のID, 使った量, 上限)]。"""
    shares = role_shares(work)
    if shares is None:
        return []
    caps, al = token_caps(work), role_allowances(work)
    out = []
    for r in window_rows(work) if rows is None else rows:
        tier = tier_of(r.get("role")) if r.get("kind") == "担当" else None
        base = caps.get(r["tool"])
        if not tier or base is None:
            continue
        conv = Path(r["file"]).stem
        lim = base * shares[tier] * (1 + al.get(conv, 0) + al.get("all", 0))
        u = weighted(r)
        if u >= lim:
            out.append((r["role"], tier, r.get("name") or conv, conv, u, lim))
    return out


def role_message(over: list) -> str:
    role, tier, name, conv, u, lim = over[0]
    return (f"✘ 担当ごとのトークンの上限：{role}（{name}）が約{u / 10_000:.0f}万（{tier}の段の上限 {lim / 10_000:.0f}万。キャッシュの読みは1/10）。"
            "担当なら、ここで作業を止めて、メインに「トークンの上限で止めた」と返す。メインはユーザーに【質問】で聞く（続ける・ここで止める）。"
            f"続けるなら `python <skill>/scripts/budget.py <work> --allow-role {conv}` で許可を記録してから再開する（その担当の上限が1回分増える）")


def role_guard(work: Path) -> str | None:
    """担当が走らせるスクリプト（make_deck・scaffold --try all・data.py check）から呼ぶ。超えた担当があれば止める文。"""
    try:
        over = role_over(work)
    except Exception:
        return None
    return role_message(over) if over else None


def active_window(work: Path):
    """作業フォルダにファイルを書いていた間（最初の1時間前〜最後の10分後）。"""
    skip = {LOG, "run_record.md", "run_record.json"}
    ts = [f.stat().st_mtime for f in Path(work).rglob("*") if f.is_file() and f.name not in skip]
    return (min(ts) - 3600, max(ts) + 600) if ts else (0, float("inf"))


def allowances(work: Path) -> dict:
    """{道具: ユーザーが「続けてよい」と言った回数}（"all" はどの道具にも数える）。"""
    n = {}
    for r in load(work):
        if r.get("type") == "allow_tokens":
            n[r.get("tool", "all")] = n.get(r.get("tool", "all"), 0) + 1
    return n


def check_tokens(work: Path, over: bool = False, used: dict | None = None) -> str | None:
    """上限を超えた道具があれば、止める理由の文。上限は、許可1回ごとに同じ量だけ足す。"""
    if over:
        return None
    caps = token_caps(work)
    try:
        rows = window_rows(work) if used is None else None
        used = token_usage(work, rows) if used is None else used
    except Exception:
        return None
    if rows is not None:
        over = role_over(work, rows)
        if over:
            return role_message(over)
    al = allowances(work)
    for tool, u in used.items():
        base = caps.get(tool)
        if base is None:
            continue
        lim = base * (1 + al.get(tool, 0) + al.get("all", 0))
        if u >= lim:
            return (f"✘ トークンの上限：{tool} でこの回 約{u / 10_000:.0f}万（上限 {lim / 10_000:.0f}万。キャッシュの読みは1/10で数える）。ここで止める。"
                    f"メインはユーザーに【質問】で聞く（続ける・ここで止める）。続けるなら `python <skill>/scripts/budget.py <work> --allow-tokens` "
                    f"で許可を記録してから再開する（上限が {base / 10_000:.0f}万 増える）")
    return None


def allow_role_tokens(work: Path, conv: str = "all"):
    with (Path(work) / LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": time.time(), "type": "allow_role_tokens", "conv": conv},
                           ensure_ascii=False) + "\n")


def allow_tokens(work: Path, tool: str = "all"):
    with (Path(work) / LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": time.time(), "type": "allow_tokens", "tool": tool},
                           ensure_ascii=False) + "\n")


def token_line(work: Path) -> str | None:
    try:
        rows = window_rows(work)
        used = token_usage(work, rows)
        over_roles = role_over(work, rows)
    except Exception:
        return None
    if not used:
        return None
    caps, al = token_caps(work), allowances(work)
    parts, over = [], False
    for tool, u in used.items():
        base = caps.get(tool)
        lim = None if base is None else base * (1 + al.get(tool, 0) + al.get("all", 0))
        over = over or (lim is not None and u >= lim)
        parts.append(f"{tool} 約{u / 10_000:.0f}万" + (f"／上限 {lim / 10_000:.0f}万" if lim else ""))
    line = f"{'△' if over or over_roles else '・'} トークン（キャッシュの読みは1/10）：" + "・".join(parts)
    if over_roles:
        line += "。担当ごとの上限を超えた担当：" + "・".join(f"{r}（約{u / 10_000:.0f}万／{lim / 10_000:.0f}万）" for r, _, _, _, u, lim in over_roles)
    return line


def summary(work: Path) -> str:
    s = scale(work)
    if s is None:
        return "回数の上限：なし（オプション）"
    used = {}
    for r in load(work):
        used[r.get("role")] = used.get(r.get("role"), 0) + 1
    items = [(k, used[k], cap(work, v)) for k, v in ROLE_CAPS.items() if used.get(k)]
    try:
        import make_deck
        stage, n, c = make_deck.run_budget(Path(work))
        if n or (Path(work) / "review.md").exists():   # レビューのあとの直しは、仕上げとは別に数える（0回でも出す）
            items.append((f"make_deck（{stage}）", n, c))
    except Exception:
        pass
    if not items:
        return "回数：まだ担当を起動していない"
    full = [k for k, n, c in items if n >= c]
    return ("回数：" + "・".join(f"{k} {n}/{c}" for k, n, c in items)
            + (f"（予定の回数を使い切ったもの：{'・'.join(full)}。もう一度起動するときだけ許可が要る）" if full else ""))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 1
    work = Path(argv[0]).resolve()
    if "--allow-role" in argv:
        k = argv.index("--allow-role")
        conv = argv[k + 1] if len(argv) > k + 1 and not argv[k + 1].startswith("-") else "all"
        allow_role_tokens(work, conv)
        print("担当ごとのトークンの上限を、ユーザーの許可で1回分足した" + ("（どの担当にも）" if conv == "all" else f"（{conv}）"))
    if "--allow-tokens" in argv:
        k = argv.index("--allow-tokens")
        tool = argv[k + 1] if len(argv) > k + 1 and not argv[k + 1].startswith("-") else "all"
        allow_tokens(work, TOOL_NAMES.get(tool.lower(), tool))
        print("トークンの上限を、ユーザーの許可で1回分足した")
    print(summary(work))
    t = token_line(work)
    if t:
        print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""作った記録：この作業フォルダを扱った会話（メインと担当）ごとに、モデル・思考の強さ・トークン・時間をまとめる。

    python <skill>/scripts/run_record.py <work>            # 表を出し、<work>/run_record.md と run_record.json に残す
    python <skill>/scripts/run_record.py <work> --print    # 残さずに出すだけ

読む記録は review_record.py と同じ（Claude Code・Codex の会話の記録。ほかの道具は読めない → 「記録なし」）。
会話ごとに拾うもの
  - 道具・メインか担当か・担当の名前（Claude Code は依頼の短い説明、Codex は担当の呼び名と役）
  - モデル、思考の強さ（effort）、思考の量（Codex は推論の出力トークン、Claude Code は思考の塊の数）
  - トークン：入力（キャッシュに無い分）・キャッシュの読み・キャッシュの書き・出力、呼び出しの回数
  - 始めと終わりの時刻、道具が記録していれば使用枠の％（会話の始めと終わり）
あわせて build_log.py の行（make_deck の回数と作り直した枚）も載せる。
数えるのは、会話を始めたフォルダが作業フォルダの一式（_work の1つ上）の中か、その1つ上のものだけ（--any-cwd で外も）。
メインの会話が、ほかの回や別の作業もしていれば、その分も入る（会話の単位で数える）。数え方は道具ごとに違うので、道具をまたいで足さない。
渡す前の確認（check_done.py）の最後にも1行で出す。合否には使わない。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_record as rr  # noqa: E402

LOOKBACK_DAYS = 3   # 作業フォルダのいちばん古いファイルの日時から、これだけ前の記録まで見る


def project_root(work: Path) -> Path:
    """作業フォルダの一式（_work の1つ上）。会話を始めたフォルダがこの中のものだけ数える（スキルを直す会話などを除く）。"""
    w = Path(work).resolve()
    for p in [w, *w.parents]:
        if p.name == "_work":
            return p.parent
    return w.parent


def _inside(cwd, root: Path | None) -> bool:
    if root is None:
        return True
    if not cwd:
        return False
    try:
        c = Path(cwd).resolve()
        if c == root.parent:   # 解凍したフォルダを開いて始めた会話（一式はその中）
            return True
        c.relative_to(root)
        return True
    except (ValueError, OSError):
        return False


def _since(work: Path) -> float:
    ts = [p.stat().st_mtime for p in Path(work).rglob("*") if p.is_file()]
    return (min(ts) if ts else time.time()) - LOOKBACK_DAYS * 86400


ROLE_HEAD = re.compile(r"スキルの「([^」{}]+)」です")


def role_of(path) -> str | None:
    """担当の会話の役：依頼文の頭「あなたは sensei-slides スキルの「〇〇」です」の、最後に出てきたもの
    （Codex は担当の会話に親の会話が写るので最後。先読みのあと続けてレビューを頼まれた担当は「レビュー担当」）。"""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    found = ROLE_HEAD.findall(text)
    return found[-1] if found else None


def _row(tool, kind, name, path):
    return {"tool": tool, "kind": kind, "name": name, "file": str(path), "role": role_of(path) if kind == "担当" else None,
            "models": [], "effort": [],
            "input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "reasoning": 0, "thinking_blocks": 0,
            "calls": 0, "start": None, "end": None, "limit_start": None, "limit_end": None, "limits": []}


def _span(r, t):
    if t is None:
        return
    r["start"] = t if r["start"] is None else min(r["start"], t)
    r["end"] = t if r["end"] is None else max(r["end"], t)


def _add(lst, v):
    if v and v not in lst:
        lst.append(v)


def claude_rows(work: Path, since: float, root_dir: Path | None = None):
    root = rr.claude_home() / "projects"
    if not root.is_dir():
        return []
    raw = rr._raw_needles(work)
    name_b = {Path(work).name}   # 一式の中で始めた会話は相対パスで書くので、名前で先にふるう
    key = rr._key(root_dir.parent) if root_dir else None
    out = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        local = bool(key) and d.name.lower().startswith(key)
        files = [(f, "メイン") for f in d.glob("*.jsonl")] + [(f, "担当") for f in d.glob("*/subagents/agent-*.jsonl")]
        for f, kind in files:
            try:
                if f.stat().st_mtime < since or not rr._mentions(f, name_b if local else raw):
                    continue
            except OSError:
                continue
            name = f.stem
            meta = f.with_suffix("").with_name(f.stem + ".meta.json")
            if meta.exists():
                try:
                    name = json.loads(meta.read_text(encoding="utf-8")).get("description") or name
                except ValueError:
                    pass
            r = _row("Claude Code", kind, name, f)
            usage, cwd, texts = {}, None, []
            for e in rr._lines(f):
                cwd = cwd or e.get("cwd")
                if e.get("type") != "assistant" or not isinstance(e.get("message"), dict):
                    continue
                m = e["message"]
                t = rr._ts(e.get("timestamp"))
                _span(r, t)
                if m.get("model") and not str(m["model"]).startswith("<"):
                    _add(r["models"], m["model"])
                _add(r["effort"], e.get("effort"))
                for c in m.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "thinking":
                        r["thinking_blocks"] += 1
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        texts.append(rr._norm(json.dumps(c.get("input"), ensure_ascii=False)))
                if isinstance(m.get("usage"), dict):
                    usage[m.get("id") or e.get("uuid")] = m["usage"]   # 1つの応答が何行にも分かれて記録される
            needles = rr._needles(work, cwd)
            if not _inside(cwd, root_dir) or not any(any(n in s for n in needles) for s in texts):
                continue
            for u in usage.values():
                r["input"] += u.get("input_tokens") or 0
                r["cache_read"] += u.get("cache_read_input_tokens") or 0
                r["cache_write"] += u.get("cache_creation_input_tokens") or 0
                r["output"] += u.get("output_tokens") or 0
            r["calls"] = len(usage)
            out.append(r)
    return out


def codex_rows(work: Path, since: float, root_dir: Path | None = None):
    root = rr.codex_home() / "sessions"
    if not root.is_dir():
        return []
    raw = rr._raw_needles(work)
    out = []
    for f in glob.glob(str(root / "**" / "rollout-*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(f) < since:
                continue
        except OSError:
            continue
        rows = rr._lines(f)
        meta = next(rows, {}).get("payload") or {}
        cwd = meta.get("cwd")
        under = False
        if cwd:
            try:
                Path(work).resolve().relative_to(Path(cwd).resolve())
                under = True
            except (ValueError, OSError):
                pass
        if not under and not rr._mentions(f, raw):
            continue
        src = meta.get("thread_source")
        if src == "guardian_review" or not _inside(cwd, root_dir):
            continue
        kind = "担当" if src == "subagent" else "メイン"
        name = meta.get("agent_path") or meta.get("agent_nickname") or Path(f).stem
        r = _row("Codex", kind, name, f)
        start = rr._ts(meta.get("timestamp")) or 0
        needles, texts, total = rr._needles(work, cwd), [], None
        for e in rows:
            t = rr._ts(e.get("timestamp"))
            p = e.get("payload") or {}
            if kind == "担当" and t is not None and t <= start + rr.FORK_SKIP_SEC:
                continue
            typ = e.get("type")
            if typ == "turn_context":
                _add(r["models"], p.get("model"))
                _add(r["effort"], p.get("effort") or ((p.get("collaboration_mode") or {}).get("settings") or {}).get("reasoning_effort"))
            elif typ == "event_msg" and p.get("type") == "token_count":
                _span(r, t)
                info = p.get("info") or {}
                if info.get("total_token_usage"):
                    total = info["total_token_usage"]
                if info.get("last_token_usage"):
                    r["calls"] += 1
                rl = p.get("rate_limits") or {}
                for key in ("primary", "secondary"):   # 枠ごと（5時間・週・月）の％の動き。枠の長さ（分）で見分ける
                    w_ = rl.get(key) or {}
                    if w_.get("used_percent") is not None and t is not None:
                        r["limits"].append((t, w_.get("window_minutes"), w_["used_percent"]))
                prim = rl.get("primary") or {}
                if prim.get("used_percent") is not None:
                    if r["limit_start"] is None:
                        r["limit_start"] = prim["used_percent"]
                    r["limit_end"] = prim["used_percent"]
            elif typ == "response_item" and p.get("type") in ("custom_tool_call", "function_call", "local_shell_call"):
                v = p.get("input") or p.get("arguments") or json.dumps(p.get("action"), ensure_ascii=False)
                texts.append(rr._norm(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)))
        if not any(any(n in s for n in needles) for s in texts):   # 同じ一式のほかの回の会話は数えない
            continue
        if total:
            cached = total.get("cached_input_tokens") or 0
            r["input"] = max(0, (total.get("input_tokens") or 0) - cached)   # Codex の入力はキャッシュの分を含む
            r["cache_read"] = cached
            r["cache_write"] = total.get("cache_write_input_tokens") or 0
            r["output"] = total.get("output_tokens") or 0
            r["reasoning"] = total.get("reasoning_output_tokens") or 0
        out.append(r)
    return out


# ---- Antigravity：~/.gemini/antigravity/conversations/<会話>.db（SQLite。中身は公開されていない protobuf なので、形が変わったら読めなくなる）
def antigravity_home() -> Path:
    return Path(os.environ.get("ANTIGRAVITY_HOME") or Path.home() / ".gemini" / "antigravity")


def _varint(b, i):
    r = s = 0
    while True:
        x = b[i]
        i += 1
        r |= (x & 0x7f) << s
        s += 7
        if x < 0x80:
            return r, i


def _pb(b):
    """protobuf の (番号, 型, 値) の並び。読めなければ例外。"""
    i, out = 0, []
    while i < len(b):
        key, i = _varint(b, i)
        f, w = key >> 3, key & 7
        if f == 0:
            raise ValueError
        if w == 0:
            v, i = _varint(b, i)
            out.append((f, 0, v))
        elif w == 2:
            n, i = _varint(b, i)
            if i + n > len(b):
                raise ValueError
            out.append((f, 2, b[i:i + n]))
            i += n
        elif w == 1:
            i += 8
        elif w == 5:
            i += 4
        else:
            raise ValueError
    return out


def _pb_get(b, path):
    cur = [b]
    for k in path:
        nxt = []
        for x in cur:
            try:
                nxt += [v for f, w, v in _pb(x) if f == k]
            except Exception:
                pass
        cur = nxt
    return cur


def antigravity_rows(work: Path, since: float, root_dir: Path | None = None):
    """作業フォルダの名前が出てくる会話ごとのトークン。gen_metadata の 1.4 が1回の呼び出しの使用量
    （2：キャッシュに無い入力、5：キャッシュの読み、1：毎回の固定の入力、3：出力、9：思考）。"""
    import sqlite3
    d = antigravity_home() / "conversations"
    if not d.is_dir():
        return []
    raw = rr._raw_needles(work)   # 作業フォルダの絶対パス（名前だけだと、ほかの場所の同じ名前の作業も拾う）
    out = []
    for f in d.glob("*.db"):
        try:
            if f.stat().st_mtime < since or not rr._mentions(f, raw):
                continue
            con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
            gens = [x for x, in con.execute("select data from gen_metadata order by idx")]
            stamps = [x for x, in con.execute("select metadata from steps order by idx")]
            con.close()
        except Exception:
            continue
        roles = set(ROLE_HEAD.findall(f.read_bytes().decode("utf-8", "replace")))
        solo = len(roles) == 1 or roles == {"レビュー担当の先読み", "レビュー担当"}   # 先読みのあと続けてレビューを頼まれた担当
        r = _row("Antigravity", "担当" if solo else "会話", f.stem, f)
        for g in gens:
            u = (_pb_get(g, [1, 4]) or [None])[0]
            if u is None:
                continue
            v = lambda k: next((x for x in _pb_get(u, [k]) if isinstance(x, int)), 0)   # noqa: E731
            r["input"] += v(2) + v(1)
            r["cache_read"] += v(5)
            r["output"] += v(3) + v(9)
            r["reasoning"] += v(9)
            r["calls"] += 1
        _span(r, f.stat().st_mtime)
        if r["calls"]:
            out.append(r)
    return out


def collect(work: Path, since: float | None = None, any_cwd: bool = False):
    since = _since(work) if since is None else since
    root_dir = None if any_cwd else project_root(work)
    rows = claude_rows(work, since, root_dir) + codex_rows(work, since, root_dir) + antigravity_rows(work, since, root_dir)
    rows.sort(key=lambda r: (r["kind"] != "メイン", r["start"] or 0))
    return rows


def _t(x):
    return time.strftime("%m-%d %H:%M", time.localtime(x)) if x else "—"


def _k(n):
    return f"{n / 1000:,.0f}k" if n >= 10000 else f"{n:,}"


def table(work: Path, rows) -> str:
    import build_log
    head = [f"# 作った記録（{Path(work).name}）", "", f"集めた日時：{time.strftime('%Y-%m-%d %H:%M')}（run_record.py）", ""]
    b = build_log.line(work)
    if b:
        head += [f"組み：{b}", ""]
    if not rows:
        return "\n".join(head + ["この作業フォルダを扱った会話の記録が見つからない（Claude Code・Codex 以外の道具は読めない）", ""])
    lines = ["| 道具 | 種類 | 名前 | モデル | 思考の強さ | 思考 | 入力 | キャッシュ読み | キャッシュ書き | 出力 | 呼び出し | 時間 | 枠の％ |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        think = f"推論 {_k(r['reasoning'])}" if r["tool"] == "Codex" else f"思考の塊 {r['thinking_blocks']}"
        mins = f"{_t(r['start'])}〜{_t(r['end'])[6:]}" if r["start"] else "—"
        lim = f"{r['limit_start']:g}→{r['limit_end']:g}" if r["limit_start"] is not None else "—"
        lines.append(f"| {r['tool']} | {r['kind']} | {str(r['name'])[:30]} | {'・'.join(r['models']) or '—'} | "
                     f"{'・'.join(r['effort']) or '—'} | {think} | {_k(r['input'])} | {_k(r['cache_read'])} | "
                     f"{_k(r['cache_write'])} | {_k(r['output'])} | {r['calls']} | {mins} | {lim} |")
    sums = []
    for tool in sorted({r["tool"] for r in rows}):
        rs = [r for r in rows if r["tool"] == tool]
        sums.append(f"- {tool}：会話 {len(rs)}（メイン {sum(r['kind'] == 'メイン' for r in rs)}・担当 {sum(r['kind'] == '担当' for r in rs)}）、"
                    f"入力 {_k(sum(r['input'] for r in rs))}・キャッシュ読み {_k(sum(r['cache_read'] for r in rs))}・"
                    f"キャッシュ書き {_k(sum(r['cache_write'] for r in rs))}・出力 {_k(sum(r['output'] for r in rs))}")
    return "\n".join(head + lines + ["", "合計（道具ごと。数え方が違うので道具をまたいで足さない）"] + sums + [""])


def short(rows) -> str:
    if not rows:
        return "会話の記録なし（読めない道具か、記録の場所が違う）"
    ms = sorted({f"{m}{'(' + '・'.join(r['effort']) + ')' if r['effort'] else ''}" for r in rows for m in r["models"]})
    return (f"会話 {len(rows)}（担当 {sum(r['kind'] == '担当' for r in rows)}）、{'・'.join(ms) or 'モデル不明'}、"
            f"出力 {_k(sum(r['output'] for r in rows))}・キャッシュ読み {_k(sum(r['cache_read'] for r in rows))}")


def save(work: Path, rows=None) -> list:
    rows = collect(work) if rows is None else rows
    (Path(work) / "run_record.md").write_text(table(work, rows), encoding="utf-8")
    (Path(work) / "run_record.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="作った記録（モデル・思考・トークン）")
    ap.add_argument("work")
    ap.add_argument("--print", action="store_true", help="ファイルに残さずに出すだけ")
    ap.add_argument("--any-cwd", action="store_true", help="作業フォルダの一式の外で始めた会話も数える")
    a = ap.parse_args(argv)
    work = Path(a.work).resolve()
    rows = collect(work, any_cwd=a.any_cwd)
    if not a.print:
        save(work, rows)
    print(table(work, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

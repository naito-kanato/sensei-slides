"""レビューを本当に別の担当（サブエージェント）がしたかを、AI の道具の会話の記録で確かめる。

手順書は「構成案・設計メモのレビューと完成後のレビューは【別のエージェント】にさせる」と決めているが、
review.md・outline_review.md はメインが書くので、ファイルだけでは、メインが自分で見て書いたのか区別できない。
そこで、道具が残す会話の記録から「作業フォルダの対象のファイルを、サブエージェントが開いたか」を拾う。

    python review_record.py <作業フォルダ>                 # 3つのレビュー（構成案・設計メモ・完成後）を見る
    python review_record.py <作業フォルダ> --kind final    # 完成後のレビューだけ

読める記録（公開された仕様ではないので、形が変わったら「記録なし」になる）：
  * Claude Code：~/.claude/projects/<フォルダ>/<会話>.jsonl がメイン、<会話>/subagents/agent-*.jsonl が担当。
    会話を始めたフォルダはどこでもよい（作業フォルダの絶対パスか、始めたフォルダからの相対パスが出てくる会話を拾う）
  * Codex：~/.codex/sessions/<年>/<月>/<日>/rollout-*.jsonl。冒頭の session_meta の thread_source が
    "subagent" のものが担当（"guardian_review" は許可の審査なので数えない）。担当の記録は、起動した時点までの
    メインの会話の写しから始まるので、起動から1秒以内の行は数えない
  * それ以外の道具（Antigravity・GitHub Copilot など）は読めない → 「記録なし」（△）。確かめられなかったことを、
    問題が無かったことにはしない

判定：
  ✔ 担当の記録に、対象（構成案なら outline.md、設計メモなら memo.md、完成後ならスライドの画像）を開いた跡がある
     （レビューの結果のファイル outline_review.md・memo_review.md・review.md の日時から、14日前までの記録を見る）
  ✘ この作業フォルダを扱った会話の記録はあるのに、担当が対象を開いた跡が無い（メインが自分でレビューした疑い）
  △ この作業フォルダを扱った会話の記録が見つからない（読めない道具か、記録の場所が違う）

拾えないもの：プログラムの中で開いたファイル、シェルの変数で組み立てたパス。後から確かめる仕組みで、防ぐ仕組みではない。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WINDOW_DAYS = 14          # レビューのファイルの日時から、これだけ前までの記録を見る
AFTER_SEC = 15 * 60       # レビューのファイルを書いたあとも、これだけは担当の動きとして数える
FORK_SKIP_SEC = 1.0       # Codex の担当の記録の冒頭の、メインの会話の写し
KINDS = {
    "outline": ("構成案のレビュー", "outline_review.md", re.compile(r"outline\.md")),
    "memo": ("設計メモのレビュー", "memo_review.md", re.compile(r"memo\.md")),
    "final": ("完成後のレビュー", "review.md", re.compile(r"\.png\b", re.I)),
}


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _key(path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(Path(path).resolve())).lower()


def _ts(s) -> float | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except ValueError:
        return None


def _lines(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except OSError:
        return


def _norm(s: str) -> str:
    """パスの書き方をそろえる（区切りの文字・JSON の書き方・大文字と小文字）。"""
    return s.replace("\\\\", "/").replace("\\", "/").lower()


def _tail(path) -> str:
    """ドライブ名を除いた絶対パス（C: と c:、Git Bash の /c/ の違いを避ける）。"""
    s = str(Path(path).resolve())
    return s[2:] if re.match(r"^[A-Za-z]:", s) else s


def _raw_needles(work: Path):
    """記録のファイルを読む前のふるいに使う文字（作業フォルダの絶対パスの、いろいろな書き方）。"""
    t = _tail(work)
    out = set()
    for v in (t, t.replace("\\", "/")):
        out |= {v, json.dumps(v, ensure_ascii=False)[1:-1], json.dumps(v)[1:-1]}
    return out


def _mentions(path, needles) -> bool:
    """ファイルの中に、needles のどれかの文字があるか（読む前のふるい。記録は1本が数十MBのこともある）。"""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return False
    return any(n.encode("utf-8") in data for n in needles)


def _needles(work: Path, cwd=None):
    """道具に渡した入力の中で、この作業フォルダを指す書き方（_norm したもの）：絶対パスと、会話を始めたフォルダからの相対パス。
    作業フォルダの名前だけでは見ない（examples/zemi の「zemi」のような名前は、ほかのコピーにも出てくる）。"""
    out = [_norm(_tail(work))]
    if cwd:
        try:
            rel = Path(work).resolve().relative_to(Path(cwd).resolve())
            if str(rel) not in (".", ""):
                out.append(_norm(str(rel)))
        except (ValueError, OSError):
            pass
    return out


class Actor:
    """会話1本（メインか担当）。events は (時刻, 道具に渡した入力の文字)。"""

    def __init__(self, tool, kind, name):
        self.tool, self.kind, self.name = tool, kind, name
        self.models = set()
        self.events = []
        self.needles = []

    def add(self, t, s):
        self.events.append((t, s, _norm(s)))

    @property
    def mentions_work(self):
        return any(any(n in ns for n in self.needles) for _, _, ns in self.events)

    def opened(self, pattern, since, until):
        """この会話で、時刻の範囲に、作業フォルダの中の pattern に合うものを道具に渡したか（同じ入力の中に作業フォルダの場所があること）。"""
        for t, s, ns in self.events:
            if t is not None and not (since <= t <= until):
                continue
            if pattern.search(s) and any(n in ns for n in self.needles):
                return True
        return False


def claude_actors(work: Path, since: float):
    """Claude Code の会話（メインと担当）のうち、作業フォルダの場所が出てくるもの。会話を始めたフォルダはどこでもよい
    （作業フォルダの外で始めた会話もある）。日時と、ファイルの中の文字で先にふるう。"""
    root = claude_home() / "projects"
    if not root.is_dir():
        return []
    raw = _raw_needles(work)
    out = []
    for d in root.iterdir():
        if not d.is_dir():
            continue
        files = [(f, "メイン") for f in d.glob("*.jsonl")] + [(f, "担当") for f in d.glob("*/subagents/agent-*.jsonl")]
        for f, kind in files:
            try:
                if f.stat().st_mtime < since:
                    continue
            except OSError:
                continue
            if not _mentions(f, raw):
                continue
            a = Actor("Claude Code", kind, f.stem)
            cwd = None
            for e in _lines(f):
                cwd = cwd or e.get("cwd")
                if e.get("type") != "assistant" or not isinstance(e.get("message"), dict):
                    continue
                m = e["message"]
                if m.get("model") and not str(m["model"]).startswith("<"):
                    a.models.add(m["model"])
                for c in m.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        a.add(_ts(e.get("timestamp")), json.dumps(c.get("input"), ensure_ascii=False))
            a.needles = _needles(work, cwd)
            out.append(a)
    return out


def codex_actors(work: Path, since: float):
    root = codex_home() / "sessions"
    if not root.is_dir():
        return []
    raw = _raw_needles(work)
    out = []
    for f in glob.glob(str(root / "**" / "rollout-*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(f) < since:
                continue
        except OSError:
            continue
        rows = _lines(f)
        meta = next(rows, {}).get("payload") or {}
        cwd = meta.get("cwd")
        # 相対パスで書く Codex は、絶対パスが出てこないことがある：会話を始めたフォルダが作業フォルダの上なら読む
        under = False
        if cwd:
            try:
                Path(work).resolve().relative_to(Path(cwd).resolve())
                under = True
            except (ValueError, OSError):
                pass
        if not under and not _mentions(f, raw):
            continue
        src = meta.get("thread_source")
        if src == "guardian_review":
            continue
        kind = "担当" if src == "subagent" else "メイン"
        start = _ts(meta.get("timestamp")) or 0
        a = Actor("Codex", kind, Path(f).stem)
        a.needles = _needles(work, cwd)
        for r in rows:
            t = _ts(r.get("timestamp"))
            p = r.get("payload") or {}
            if kind == "担当" and t is not None and t <= start + FORK_SKIP_SEC:
                continue   # 起動した時点までのメインの会話の写し
            if r.get("type") == "turn_context" and p.get("model"):
                a.models.add(p["model"])
            elif r.get("type") == "response_item" and p.get("type") in ("custom_tool_call", "function_call", "local_shell_call"):
                v = p.get("input") or p.get("arguments") or json.dumps(p.get("action"), ensure_ascii=False)
                a.add(t, v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        out.append(a)
    return out


def actors(work: Path, since: float):
    """作業フォルダを扱った会話（メインと担当）。"""
    return [a for a in claude_actors(work, since) + codex_actors(work, since) if a.mentions_work]


def check(work, kind, until=None, found=None):
    """(印, 項目, 説明)。until はレビューを終えた時刻の目安（省略時はレビューのファイルの日時、無ければ今）。"""
    work = Path(work)
    label, fname, pattern = KINDS[kind]
    f = work / fname
    if until is None:
        until = f.stat().st_mtime if f.exists() else datetime.now().timestamp()
    since = until - WINDOW_DAYS * 86400
    acts = found if found is not None else actors(work, since)
    if not acts:
        return ("△", f"{label}の記録", "この作業フォルダを扱った会話の記録が見つからない（Claude Code・Codex 以外の道具か、記録の場所が違う）。"
                                      "別の担当がレビューしたかは確かめられなかった")
    subs = [a for a in acts if a.kind == "担当" and a.opened(pattern, since, until + AFTER_SEC)]
    if subs:
        models = sorted({m for a in subs for m in a.models}) or ["モデル不明"]
        return ("✔", f"{label}の記録", f"{subs[0].tool} の担当 {len(subs)} 本が開いた記録あり（{'・'.join(models)}）")
    what = {"outline": "outline.md", "memo": "memo.md", "final": "スライドの画像"}[kind]
    return ("✘", f"{label}の記録", f"この作業フォルダの会話の記録はあるが、別の担当が {what} を開いた跡が無い"
                                  "（メインが自分でレビューした疑い）。【別のエージェント】を起動してレビューさせ直し、結果を残す。"
                                  "レビューのあとで作業フォルダを移した・名前を変えたなら、移す前の記録は拾えない")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("work", help="作業フォルダ（_work/<資料名>）")
    ap.add_argument("--kind", choices=list(KINDS), action="append", help="見るレビュー（省略時はファイルがあるもの全部）")
    a = ap.parse_args(argv)
    work = Path(a.work)
    kinds = a.kind or [k for k, (_, fn, _) in KINDS.items() if (work / fn).exists()]
    if not kinds:
        print("レビューの結果のファイル（outline_review.md・memo_review.md・review.md）が無い")
        return 1
    found = actors(work, datetime.now().timestamp() - (WINDOW_DAYS + 30) * 86400)
    bad = 0
    for k in kinds:
        mark, item, msg = check(work, k, found=found)
        bad += mark == "✘"
        print(f"{mark} {item}：{msg}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

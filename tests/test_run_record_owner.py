"""run_record：担当がいれば、メインはその担当を起動した会話だけを数える（同じフォルダの別の会話を数えない）。"""
import run_record
from test_review_record import _claude_dir, _use, _work, _write


def _usage(entry, n, cwd=None):
    entry["cwd"] = str(cwd) if cwd else None
    entry["message"]["usage"] = {"input_tokens": 1, "cache_read_input_tokens": n, "output_tokens": 1}
    entry["message"]["id"] = f"m{n}"
    return entry


def test_other_main_in_same_folder_is_not_counted(tmp_path):
    w = _work(tmp_path)
    d = _claude_dir(w)
    _write(d / "run.jsonl", [_usage(_use("Bash", w / "outline.md"), 100, w.parents[1])])                 # この回のメイン
    _write(d / "run" / "subagents" / "agent-a1.jsonl", [_usage(_use("Read", w / "outline.md"), 50, w.parents[1])])
    _write(d / "other.jsonl", [_usage(_use("Read", w / "outline.md"), 9999, w.parents[1])])              # あとで読んだだけの別の会話
    rows = run_record.collect(w)
    mains = [r["name"] for r in rows if r["kind"] == "メイン"]
    assert mains == ["run"]


def test_main_only_run_is_still_counted(tmp_path):
    w = _work(tmp_path)
    d = _claude_dir(w)
    _write(d / "solo.jsonl", [_usage(_use("Bash", w / "outline.md"), 100, w.parents[1])])
    assert [r["kind"] for r in run_record.collect(w)] == ["メイン"]

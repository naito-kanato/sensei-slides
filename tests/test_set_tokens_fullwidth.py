"""ユーザーが言ったトークンの上限を記録に残す（budget.py --set-tokens）と、全角の英数字の △（check_memo.fullwidth_alnum）。"""
import budget
import check_memo as cm


def test_set_tokens_is_kept_before_memo(tmp_path):
    work = tmp_path / "_work" / "講座_01"            # まだ無い作業フォルダでも記録できる
    assert budget.token_caps(work)["Codex"] == budget.TOKEN_CAPS["Codex"]
    assert budget.main([str(work), "--set-tokens", "Codex 600万・Antigravity 800万"]) == 0
    caps = budget.token_caps(work)
    assert caps["Codex"] == 6_000_000 and caps["Antigravity"] == 8_000_000 and caps["Claude Code"] == budget.TOKEN_CAPS["Claude Code"]
    budget.set_tokens(work, "Codex 900万")           # あとから言った値が勝つ
    assert budget.token_caps(work)["Codex"] == 9_000_000
    (work / "memo.md").write_text("## 1. この回のゴールと前提\n\n- トークンの上限：Codex 300万\n", encoding="utf-8")
    assert budget.token_caps(work)["Codex"] == 9_000_000   # 設計メモのオプションより、記録した値を先に使う
    budget.set_tokens(work, "なし")
    assert budget.token_caps(work)["Codex"] is None
    assert budget.main([str(work), "--set-tokens"]) == 1    # 値が無ければ書かない


def test_fullwidth_alnum():
    rows = [["#", "●見出し", "青帯（結論）", "本文の要点"],
            ["2", "a", "第３世代は評価を改めた", "Ｖｅｒ３．０で広げた"],
            ["3", "b", "半角の90項目は通る", "2013年4月"],
            ["表紙", "c", "４", ""]]
    mark, item, msg = cm.fullwidth_alnum(rows)
    assert mark == "△" and item == "全角の英数字" and "[2]" in msg and "[3]" not in msg
    assert cm.fullwidth_alnum([rows[0], rows[2]]) is None

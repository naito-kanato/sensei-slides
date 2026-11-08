"""検査の結果の出し方（check_memo・check_outline・check_done で共通）。

✘・△ は1行ずつ全部、✔ は「✔ N項目：名前・名前…」の1行にまとめる（担当の会話に載る量を減らす）。
✔ の中身も見たいときは、各スクリプトに --all を付ける。
"""
from __future__ import annotations


def show(res, full: bool = False) -> None:
    ok = [item for mark, item, _ in res if mark == "✔"]
    for mark, item, msg in res:
        if full or mark != "✔":
            print(f"{mark} {item}：{msg}")
    if ok and not full:
        print(f"✔ {len(ok)}項目：{'・'.join(dict.fromkeys(ok))}")


def take_all(argv: list[str]) -> tuple[list[str], bool]:
    """argv から --all を抜く。(残りの引数, --all があったか)"""
    return [a for a in argv if a != "--all"], "--all" in argv

"""作り始める前の環境の確認：このPCで、どこまで作れるかを調べる（SKILL.md 手順0）。何も入れず、何も変えない。

    python <skill>/scripts/check_env.py

調べること
  1. Python の版（3.10 以上）と部品（python-pptx・PyMuPDF・Pillow・matplotlib・numpy・lxml）
  2. 描画の検査と原稿のページに使うもの：描画の検査は PowerPoint を使わない描画（render_check_py.py）でどの PC でもできる。
     Windows の PowerPoint があれば、ERROR 0 の回に PowerPoint で確かめ、原稿のページの画像も PowerPoint で作る。
     描画に使う書体（MS PGothic・Segoe UI・Arial など）が無い PC では代わりの書体で測るので、幅が PowerPoint とずれうる
  3. 図の日本語フォント（Meiryo・Yu Gothic・ヒラギノ・Noto Sans CJK など）
  4. Claude Code で使うとき：道具を絞った担当の型（.claude/agents/sensei-slides-worker.md）があるか（無くても作れる。あると軽い）
足りないものがあれば、入れ方を出す。Python の部品は、エージェントが【質問】で聞いて許可をもらってから、作業フォルダの .venv に入れる。
PC 全体に入るもの（Python 本体・フォント）は、入れるのはユーザー（頼まれたときだけ、確認を出してから入れる）。LibreOffice は要らない。
終了コード：部品が足りなければ 1（スライドが作れない）。PowerPoint・フォントが無いだけなら 0（スライドと検査までは作れる）。
"""
import importlib
import platform
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

PACKAGES = [("pptx", "python-pptx"), ("pymupdf", "PyMuPDF"), ("PIL", "Pillow"), ("matplotlib", "matplotlib"),
            ("numpy", "numpy"), ("lxml", "lxml")]
OS = platform.system()

INSTALL_PY = {
    "Windows": "winget install -e --id Python.Python.3.12（または https://www.python.org/downloads/ から。入れたら新しいターミナルで）",
    "Darwin": "brew install python@3.12（または https://www.python.org/downloads/ から）",
    "Linux": "sudo apt install python3 python3-venv（Fedora などは sudo dnf install python3）",
}
INSTALL_FONT = {
    "Windows": "Windows には Meiryo・Yu Gothic が最初から入っている。無ければ Windows の「フォント」の設定から追加",
    "Darwin": "Mac にはヒラギノが最初から入っている",
    "Linux": "sudo apt install fonts-noto-cjk",
}


def check_packages():
    miss = []
    for mod, name in PACKAGES:
        try:
            importlib.import_module(mod)
        except Exception:
            miss.append(name)
    return miss


def has_powerpoint():
    """Windows に PowerPoint が入っているか（起動はしない。COM の登録を見るだけ）。"""
    if OS != "Windows" or not shutil.which("powershell"):
        return False
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "if ([type]::GetTypeFromProgID('PowerPoint.Application')) { 'yes' } else { 'no' }"],
                           capture_output=True, text=True, errors="replace", timeout=30)
        return "yes" in r.stdout
    except Exception:
        return False


def libreoffice():
    try:
        import render_check_lo
        return render_check_lo.find_soffice()
    except SystemExit:
        return None
    except Exception:
        return None


def render_fonts():
    """描画の検査で文字の幅を測る書体のうち、この PC に無いもの（テンプレートのテーマの書体）。"""
    try:
        import render_check_py
        return [n for n in render_check_py.CHECK_FONTS if render_check_py.find_face(n, False, False) is None]
    except Exception:
        return None


def ja_font():
    try:
        from matplotlib import font_manager
        import figkit
        names = {f.name for f in font_manager.fontManager.ttflist}
        return next((n for n in figkit.JA_FONTS if n in names), None)
    except Exception:
        return None


WORKER = "sensei-slides-worker.md"


def worker_agent():
    """Claude Code の置き場所（.claude/skills/<名前>/）にスキルがあるとき、担当の型があるか。(Claude Code か, 型の場所 or None)。
    担当は呼び出しのたびに道具の説明を読み直すので、道具を絞った型だと1回あたりが軽い（同梱の assets/claude/）。"""
    skill = Path(__file__).resolve().parents[1]
    if skill.parent.name != "skills" or skill.parent.parent.name != ".claude":
        return False, None
    for d in (skill.parents[2] / ".claude" / "agents", Path.home() / ".claude" / "agents"):
        if (d / WORKER).exists():
            return True, d / WORKER
    return True, None


def main():
    rows, todo = [], []
    py_ok = sys.version_info >= (3, 10)
    rows.append(("✔" if py_ok else "✘", "Python", platform.python_version() + ("" if py_ok else "（3.10 以上にする）")))
    if not py_ok:
        todo.append("Python 3.10 以上を入れる：" + INSTALL_PY.get(OS, INSTALL_PY["Linux"]))
    miss = check_packages()
    rows.append(("✘" if miss else "✔", "Python の部品", "足りない：" + "・".join(miss) if miss else "そろっている"))
    if miss:
        todo.append("部品を入れる（エージェントが聞いて、許可があれば .venv に入れる）：python -m venv .venv → .venv の python -m pip install -r <skill>/requirements.txt（Windows は .venv\\Scripts\\python、Mac・Linux は .venv/bin/python）")
    ppt = has_powerpoint()
    lo = libreoffice()
    rows.append(("✔" if not miss else "✘", "描画の検査", "PowerPoint を使わない描画（render_check_py.py）で、どの回も描いて検査する"
                 + ("。ERROR 0 の回に PowerPoint で1回描いて確かめる" if ppt else "")))
    rows.append(("✔" if ppt else "－", "PowerPoint", "あり（ERROR 0 の回の確かめと、原稿のページの画像はこれで）" if ppt else
                 "なし（検査と原稿のページの画像は、PowerPoint を使わない描画で作る。見た目は近いが同じではないので、最後は画像を目で見る）"))
    if lo and not ppt:
        rows.append(("✔", "LibreOffice", f"あり（{lo}。原稿のページの画像はこれで）"))
    fonts = render_fonts() if not miss else None
    if fonts is not None:
        rows.append(("✔" if not fonts else "△", "描画の書体", "PowerPoint と同じ書体で測る" if not fonts else
                     f"{'・'.join(fonts)} が無い。代わりの書体で測るので、文字の幅が PowerPoint と少しずれうる（最後は画像を目で見る）"))
    font = ja_font()
    no_mpl = "matplotlib" in miss
    rows.append(("✔" if font else "－" if no_mpl else "△", "図の日本語フォント",
                 font or ("調べられない（matplotlib が無い。部品を入れてからもう一度）" if no_mpl else "見つからない（図の日本語が□になる）")))
    if not font and not no_mpl:
        todo.append("日本語フォントを入れる：" + INSTALL_FONT.get(OS, INSTALL_FONT["Linux"]))

    cc, worker = worker_agent()
    if cc:
        skill = Path(__file__).resolve().parents[1]
        rows.append(("✔" if worker else "△", "担当の型（Claude Code）", f"あり（{worker}）" if worker else
                     f"無い（道具ぜんぶの担当で動き、1回の呼び出しが重い）→ {(skill / 'assets' / 'claude' / WORKER).as_posix()} を "
                     f"{(skill.parents[2] / '.claude' / 'agents').as_posix()}/ に写すと、次の会話から軽い担当で動く（写すのはユーザーの許可を得てから）"))

    for mark, item, msg in rows:
        print(f"{mark} {item}：{msg}")
    if todo:
        print("\n足りないもの（部品は、聞いて許可をもらってから .venv に入れる。PC 全体に入るものは、入れるのはユーザー）：")
        for t in todo:
            print(f"  - {t}")
    else:
        print("\n全部そろっている")
    return 1 if (miss or not py_ok) else 0


if __name__ == "__main__":
    sys.exit(main())

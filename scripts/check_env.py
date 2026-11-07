"""作り始める前の環境の確認：このPCで、どこまで作れるかを調べる（SKILL.md 手順0）。何も入れず、何も変えない。

    python <skill>/scripts/check_env.py

調べること
  1. Python の版（3.10 以上）と部品（python-pptx・PyMuPDF・Pillow・matplotlib・numpy・lxml）
  2. 描画の検査と原稿のページに使うもの：Windows の PowerPoint、無ければ LibreOffice（どちらか1つあればよい）
  3. 図の日本語フォント（Meiryo・Yu Gothic・ヒラギノ・Noto Sans CJK など）
足りないものがあれば、入れ方を出す。Python の部品は、エージェントが【質問】で聞いて許可をもらってから、作業フォルダの .venv に入れる。
PC 全体に入るもの（Python 本体・LibreOffice・フォント）は、入れるのはユーザー（頼まれたときだけ、確認を出してから入れる）。
終了コード：部品が足りなければ 1（スライドが作れない）。描画のもの・フォントが無いだけなら 0（スライドまでは作れる）。
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
INSTALL_LO = {
    "Windows": "winget install TheDocumentFoundation.LibreOffice（または https://www.libreoffice.org/download/ から）",
    "Darwin": "brew install --cask libreoffice（または https://www.libreoffice.org/download/ から）",
    "Linux": "sudo apt install libreoffice-impress（Fedora などは sudo dnf install libreoffice-impress）",
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
                           capture_output=True, text=True, timeout=30)
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


def ja_font():
    try:
        from matplotlib import font_manager
        import figkit
        names = {f.name for f in font_manager.fontManager.ttflist}
        return next((n for n in figkit.JA_FONTS if n in names), None)
    except Exception:
        return None


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
    rows.append(("✔" if ppt else "－", "PowerPoint", "あり（描画の検査と原稿のページはこれで）" if ppt else "なし"))
    rows.append(("✔" if lo else "－", "LibreOffice", (f"あり（{lo}）" + ("" if ppt else "。描画の検査と原稿のページはこれで（やや甘め。最後は画像を目で見る）")) if lo else "なし"))
    if not ppt and not lo:
        rows.append(("✘", "描画の検査・原稿のページ", "どちらも無いので作れない（スライドの .pptx までは作れる）"))
        todo.append("LibreOffice（無料）を入れる：" + INSTALL_LO.get(OS, INSTALL_LO["Linux"]))
    font = ja_font()
    rows.append(("✔" if font else "△", "図の日本語フォント", font or "見つからない（図の日本語が□になる）"))
    if not font:
        todo.append("日本語フォントを入れる：" + INSTALL_FONT.get(OS, INSTALL_FONT["Linux"]))

    for mark, item, msg in rows:
        print(f"{mark} {item}：{msg}")
    if todo:
        print("\n足りないもの（部品は、聞いて許可をもらってから .venv に入れる。PC 全体に入るものは、入れるのはユーザー）：")
        for t in todo:
            print(f"  - {t}")
        if not ppt and not lo:
            print("  入れなくても、pptx だけは作れる（make_deck.py --no-render。描画の検査と原稿のページは、LibreOffice を入れればあとから）")
    else:
        print("\n全部そろっている")
    return 1 if (miss or not py_ok) else 0


if __name__ == "__main__":
    sys.exit(main())

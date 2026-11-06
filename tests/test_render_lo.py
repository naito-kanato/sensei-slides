"""LibreOffice 版の描画（render_check_lo.py）。LibreOffice が無い環境（CI など）では飛ばす。"""
import json
import shutil
import subprocess
import sys

import pytest

import check_layout
import render_check_lo as lo

try:
    SOFFICE = lo.find_soffice()
except SystemExit:
    SOFFICE = None

need_lo = pytest.mark.skipif(SOFFICE is None, reason="LibreOffice が無い")


def test_soffice_from_env(monkeypatch, tmp_path):
    fake = tmp_path / "soffice.exe"
    fake.write_text("")
    monkeypatch.setenv("SOFFICE", str(fake))
    assert lo.find_soffice() == str(fake)


@need_lo
def test_course_example_renders_like_powerpoint(built, tmp_path, capsys):
    """講座の見本を LibreOffice で描くと、PowerPoint と同じく ERROR 0・WARN 0（Windows で比べたときの結果）"""
    pptx = built / "examples" / "course" / "AI活用講座" / "01_生成AIは何をしているか_スライド.pptx"
    out = tmp_path / "render"
    r = subprocess.run([sys.executable, "-X", "utf8", str(lo.__file__), "-Pptx", str(pptx), "-OutDir", str(out)],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, r.stderr
    data = json.loads((out / "shapes.json").read_text(encoding="utf-8"))
    assert data["engine"] == "libreoffice" and data["slides"] == 15
    assert len(list(out.glob("slide-*.png"))) == 15
    assert check_layout.main(str(out / "shapes.json"), str(pptx)) == 0
    assert "0 errors" in capsys.readouterr().out


@need_lo
def test_export_pdf(built, tmp_path):
    import pymupdf as fitz
    pptx = built / "examples" / "zemi" / "重力波の初観測_スライド.pptx"
    pdf = lo.export_pdf(pptx, tmp_path / "slides.pdf")
    assert fitz.open(pdf).page_count == 14

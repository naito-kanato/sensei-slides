"""数字を探す担当の「驚きの事実」（data.py）と、資料が土台なら1人（next_step.source_based）。"""
import data
import next_step

DATA = """## データ：損失の下がり方
- 驚き：予言の3や1でなく0.5
- 単位：—／分母：—／時点：2009年
- 出典：論文 p.3
- 確認：○
- 別の読み方：2本の梁だけ
| 区分 | 値 |
|---|---|
| 予言 | 3 |
| 実測 | 0.5 |

## 事実：金属にも二準位系がある
- 驚き：結晶の金属には無いと思われがちだが、多結晶の金属でも見つかっている
- 出典：論文 p.1
- 確認：○
- 別の読み方：無秩序な金属の例が中心
"""


def test_fact_is_parsed_and_merged(tmp_path):
    w = tmp_path / "_work" / "X講座_01"
    w.mkdir(parents=True)
    (w / "data_1.md").write_text(DATA, encoding="utf-8")
    (w / "memo.md").write_text("# 設計メモ\n\n## 3. 事実と出典\n\n## 4. 問題\n", encoding="utf-8")
    facts = data.parse_facts(DATA)
    assert [f["title"] for f in facts] == ["金属にも二準位系がある"] and not data.fact_problems(facts[0])
    assert len(data.parse(DATA)) == 1
    data.merge(w)
    memo = (w / "memo.md").read_text(encoding="utf-8")
    assert "### データ1：損失の下がり方" in memo and "### 驚きの事実1：金属にも二準位系がある" in memo
    d = data.datasets(memo)[1]
    assert d["fields"]["驚き"] == "予言の3や1でなく0.5"     # 組の中身に、事実の行が混ざらない


def test_fact_needs_source():
    f = data.parse_facts("## 事実：題\n- 驚き：…\n- 確認：○\n- 別の読み方：…\n")[0]
    assert data.fact_problems(f) == ["「出典」が無い"]


def test_source_based(tmp_path):
    r = tmp_path / "00_README.md"
    r.write_text("- 資料の扱い：**土台**。論文の全部\n", encoding="utf-8")
    assert next_step.source_based(r)
    r.write_text("- 資料の扱い：橋渡し（卒論の式だけ）\n", encoding="utf-8")
    assert not next_step.source_based(r)
    assert not next_step.source_based(tmp_path / "無い.md")

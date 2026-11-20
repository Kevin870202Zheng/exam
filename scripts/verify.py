#!/usr/bin/env python3
"""校验文档与 HKSI 官方样题的一致性。

检查两件事：
  1. 04 表格里 60 个答案，与官方答案页逐题一致（防止手改出错）；
  2. 各文档正文的关键计算值仍在（防止改动时误删/写错数字）。

前置：先运行 ./scripts/fetch-sources.sh 取得 source/p7-sample-chi.pdf（或其 .txt）。

退出码：0 通过；1 有差异；2 前置文件缺失或格式变化。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOC_ANSWERS = ROOT / "04-官方样题60题考点地图.md"
TXT = ROOT / "source" / "p7-sample-chi.txt"
PDF = ROOT / "source" / "p7-sample-chi.pdf"

DOCS = {
    "02": ROOT / "02-必背数字与公式.md",
    "04": ROOT / "04-官方样题60题考点地图.md",
}

# (文档, 说明, 应出现的字符串)
KEY_VALUES = [
    ("04", "Q3  风险溢价", "2.59%"),
    ("04", "Q21 债券价格", "944,918.75"),
    ("04", "Q41 汇兑损失（港元计价）", "10,000,000 港元"),
    ("04", "Q45 FRA 折现后结算额", "14,918"),
    ("04", "Q47 理论除权价", "19.5 元"),
    ("04", "Q50 半年复利终值", "112.62"),
    ("04", "Q50 连续复利上限", "112.75"),
    ("04", "Q59 预期回报", "4.7%"),
    ("02", "Q21 年金因子", "5.5081"),
    ("02", "Q52 远期贴水年化", "1.16%"),
]


def load_official_text() -> str:
    if TXT.exists():
        return TXT.read_text(encoding="utf-8", errors="ignore")
    if PDF.exists():
        try:
            import pypdf
        except ImportError:
            sys.exit("需要 pypdf 才能读 PDF：python3 -m pip install pypdf")
        reader = pypdf.PdfReader(str(PDF))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    sys.exit("缺少官方样题：请先运行 ./scripts/fetch-sources.sh")


def official_answers(text: str) -> dict[int, str]:
    """官方答案页形如 '1 D 21 B 41 A'，每题每行三组。"""
    answers: dict[int, str] = {}
    for line in text.splitlines():
        for match in re.finditer(r"(\d{1,2})\s+([A-D])\s", line):
            q, a = int(match.group(1)), match.group(2)
            if 1 <= q <= 60 and q not in answers:
                answers[q] = a
    return answers


def doc_answers(doc: str) -> dict[int, str]:
    """04 表格行格式：| # | 课题 | 考点 | **X** | 理由 |"""
    answers: dict[int, str] = {}
    row = re.compile(r"\|\s*(\d{1,2})\s*\|\s*[^|]+\|[^|]*\|\s*\*\*([A-D])\*\*\s*\|")
    for line in doc.splitlines():
        m = row.match(line)
        if m:
            answers[int(m.group(1))] = m.group(2)
    return answers


def main() -> int:
    if not DOC_ANSWERS.exists():
        sys.exit(f"找不到文档：{DOC_ANSWERS}")

    off = official_answers(load_official_text())
    if len(off) != 60:
        print(f"✗ 官方答案只解析到 {len(off)} 题（应为 60），PDF 格式可能变了，请人工检查")
        return 2
    print(f"✓ 官方答案解析成功：{len(off)} 题")

    mine = doc_answers(DOC_ANSWERS.read_text(encoding="utf-8"))
    if len(mine) != 60:
        print(f"✗ 04 中只解析到 {len(mine)} 题答案（应为 60）")
        return 1

    diff = [(q, off[q], mine[q]) for q in range(1, 61) if off[q] != mine[q]]
    if diff:
        print("✗ 以下题目答案与官方不一致：")
        for q, o, m in diff:
            print(f"   第 {q} 题：官方 {o}，文档 {m}")
        return 1
    print("✓ 04 答案与官方逐题一致：60/60")

    texts: dict[str, str] = {}
    missing: list[str] = []
    for key, label, value in KEY_VALUES:
        if key not in texts:
            path = DOCS[key]
            texts[key] = path.read_text(encoding="utf-8") if path.exists() else ""
        if value not in texts[key]:
            missing.append(f"{key} · {label} → 应有「{value}」")
    if missing:
        print("✗ 以下关键数值找不到（可能被误改）：")
        for item in missing:
            print(f"   {item}")
        return 1
    print(f"✓ 关键计算值均在对应文档中：{len(KEY_VALUES)} 项")

    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

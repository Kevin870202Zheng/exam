#!/usr/bin/env python3
"""把手册 PDF 提取成带页码标记的纯文本，供 grep 定点核对文档用。

手册需自行从 HKSI 门户下载（报名后免费），放入 source/ 后再运行本脚本。
输出留在 source/（不入版本库）。

用法:
    python3 scripts/extract_manual.py                      # 自动找 source/*Full*.pdf
    python3 scripts/extract_manual.py "source/某个文件.pdf"

依赖: pypdf + cryptography（手册为 AES 加密，缺 cryptography 会报 DependencyError）
"""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source"


def find_manual() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    hits = sorted(SRC.glob("*Full*.pdf")) or sorted(SRC.glob("P7*.pdf"))
    if not hits:
        sys.exit("找不到手册 PDF。先把手册放进 source/，或显式传入路径。")
    return hits[0]


def main() -> None:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("缺少 pypdf：python3 -m pip install --user pypdf")

    pdf = find_manual()
    if not pdf.exists():
        sys.exit(f"文件不存在：{pdf}")

    try:
        reader = PdfReader(str(pdf))
        if reader.is_encrypted:
            reader.decrypt("")
        pages = [p.extract_text() or "" for p in reader.pages]
    except Exception as exc:
        if "cryptography" in str(exc).lower() or "AES" in str(exc):
            sys.exit("手册为 AES 加密，缺少 cryptography：python3 -m pip install --user cryptography")
        raise

    # 文件名 "P7 V3.6 Full (Chi).pdf" -> manual-v36-chi.txt
    m = re.search(r"v?(\d+)\.(\d+)", pdf.stem, re.I)
    ver = f"v{m.group(1)}{m.group(2)}" if m else "manual"
    lang = "chi" if re.search(r"chi|中", pdf.stem, re.I) else "eng"
    out = SRC / f"manual-{ver}-{lang}.txt"

    with out.open("w", encoding="utf-8") as fh:
        for i, text in enumerate(pages, 1):
            fh.write(f"\n=== p{i} ===\n{text}\n")

    chars = sum(len(t) for t in pages)
    print(f"页数: {len(pages)}")
    print(f"字符: {chars:,}")
    print(f"输出: {out.relative_to(ROOT)}  ({out.stat().st_size / 1024:.0f} KB)")
    print("\n定位示例:")
    print(f'  grep -n "^=== p" {out.relative_to(ROOT)} | head')


if __name__ == "__main__":
    main()

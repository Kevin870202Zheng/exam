#!/usr/bin/env bash
# 获取本地素材（不入版本库）：HKSI 官方 PDF + 参考仓库 + 文本提取
#
# 这些文件受版权约束，不能随仓库分发。新克隆本仓库后运行一次：
#     ./scripts/fetch-sources.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/source"
mkdir -p "$SRC"

fetch() { # $1=url  $2=文件名
  printf '→ %s\n' "$2"
  curl -fsSL -o "$SRC/$2" "$1"
  printf '   %s\n' "$(du -h "$SRC/$2" | cut -f1)"
}

# --- 官方文件（可信度最高） ---
fetch "https://www.hksi.org/media/4987/p7-sample-practice-test-chi.pdf" "p7-sample-chi.pdf"
fetch "https://www.hksi.org/media/4982/p7-sample-practice-test-eng.pdf" "p7-sample-eng.pdf"
fetch "https://www.hksi.org/media/8440/p7-syllabus_eng_v35_clean.pdf" "p7-syllabus-v35.pdf"

# --- 提取可搜索文本（需要 pypdf） ---
if python3 -c 'import pypdf' 2>/dev/null; then
  python3 - "$SRC" <<'PY'
import pathlib, sys, pypdf
src = pathlib.Path(sys.argv[1])
for pdf in sorted(src.glob("*.pdf")):
    reader = pypdf.PdfReader(pdf)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    out = pdf.with_suffix(".txt")
    out.write_text(text)
    print(f"   文本：{out.name}（{len(reader.pages)} 页，{len(text)} 字符）")
PY
else
  echo "!! 未安装 pypdf，跳过文本提取：python3 -m pip install pypdf"
  echo "   （不装也能用，只影响 grep 检索与 scripts/verify.py）"
fi

# --- 第三方参考仓库（无 LICENSE，仅作交叉参考，绝不入库） ---
if [ ! -d "$SRC/ref-github-hksi-paper7" ]; then
  echo "→ 参考仓库 hksi-paper7（浅克隆）"
  git clone --depth 1 https://github.com/YongzeYang/hksi-paper7.git \
    "$SRC/ref-github-hksi-paper7"
fi

echo
echo "完成。source/ 已被 .gitignore 排除，不会进入版本库。"
echo "下一步：python3 scripts/verify.py"

#!/usr/bin/env python3
"""把文档里的关键数字逐条丢到手册原文里搜，输出命中页码。

手册需自行从 HKSI 门户下载（报名后免费）并放入 source/，先跑 extract_manual.py。
本脚本**只在本地可用**（手册不入版本库），结论请以「命中页码」的形式写进文档，
让没有手册的人也能靠页码复核。

用法:
    python3 scripts/audit_manual.py                  # 批量核对，输出表格
    python3 scripts/audit_manual.py --ctx 存保        # 看某条命中页的原文上下文
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source"

# (标签, 正则, 我的文档 §)
CHECKS = [
    ("LERS 发钞价 7.80", r"7\.80", "A"),
    ("强方 7.75 / 弱方 7.85", r"7\.75|7\.85", "A"),
    ("LERS 实施 1983", r"1983", "A"),
    ("兑换保证 2005", r"2005年5月", "A"),
    ("持牌银行资本 3 亿", r"3億港元|3億元", "B"),
    ("RLB 资本 1 亿", r"1億港元|1億元", "B"),
    ("DT 资本 2,500 万", r"2,500萬", "B"),
    ("RLB 存款 50 万", r"50萬", "B"),
    ("DT 存款 10 万", r"10萬", "B"),
    ("DT 期限 3 个月", r"3個月", "B"),
    ("存保 80 万", r"80萬|800,000", "B★"),
    ("盈利测试 3,500 万", r"3,500萬", "C★"),
    ("盈利测试 4,500 万", r"4,500萬", "C★"),
    ("市值 5 亿", r"5億元", "C★"),
    ("市值/收入 40 亿", r"40億元", "C★"),
    ("市值/收入 20 亿", r"20億元", "C★"),
    ("现金流 1 亿", r"1億元", "C★"),
    ("公众持股 25%", r"25%", "C★"),
    ("市值 >100 亿", r"100億元", "C★"),
    ("最低 15%", r"15%", "C★"),
    ("股东 300 名", r"300名", "C★"),
    ("印花税 0.1%", r"0\.1%", "C★"),
    ("交易费 0.00565%", r"0\.00565%", "C★"),
    ("SFC 征费 0.0027%", r"0\.0027%", "C★"),
    ("AFRC 0.00015%", r"0\.00015%", "C★"),
    ("恒指 1969", r"1969", "C"),
    ("WVR 10 倍", r"10倍", "C"),
    ("EFB 91/182/364 天", r"91天|182天|364天", "D"),
    ("投资级 BBB-/Baa3", r"BBB-|Baa3", "D"),
    ("即期 T+2", r"T\+2", "E"),
    ("沪港通", r"滬港通", "C"),
    ("SPAC", r"SPAC", "C"),
    ("18C 特专科技", r"特專科技", "C"),
]


def load_pages() -> dict:
    cands = sorted(SRC.glob("manual-*.txt"))
    if not cands:
        sys.exit("找不到 source/manual-*.txt，先运行：python3 scripts/extract_manual.py")
    txt = cands[0].read_text(encoding="utf-8")
    pages, cur, buf = {}, 0, []
    for ln in txt.split("\n"):
        m = re.match(r"=== p(\d+) ===", ln.strip())
        if m:
            if cur:
                pages[cur] = "".join(buf)
            cur, buf = int(m.group(1)), []
        else:
            buf.append(ln)
    if cur:
        pages[cur] = "".join(buf)
    return pages


# 手册 PDF 提取出的文本用全角符号：T＋2、0.1％、（）、，。不折半角会大量误判「未命中」。
FULL2HALF = str.maketrans("＋％（）０１２３４５６７８９．，：；－＝", "+%()0123456789.,:;-=")


def norm(s: str) -> str:
    """去掉所有空白并折半角——手册还会把数字切断（如 '202 6 年'）。"""
    return re.sub(r"\s+", "", s.translate(FULL2HALF))


def main() -> None:
    pages = load_pages()
    flat = {p: norm(t) for p, t in pages.items()}

    if "--page" in sys.argv:
        p = int(sys.argv[sys.argv.index("--page") + 1])
        print(flat.get(p, f"无第 {p} 页")[:3000])
        return

    if "--grep" in sys.argv:
        pat = sys.argv[sys.argv.index("--grep") + 1]
        rx = re.compile(pat)
        n = 0
        for p in sorted(flat):
            for m in rx.finditer(flat[p]):
                s = max(0, m.start() - 100)
                print(f"p{p}: …{flat[p][s:m.end() + 100]}…\n")
                n += 1
                if n >= 10:
                    return
        if n == 0:
            print(f"未找到：{pat}")
        return

    if "--ctx" in sys.argv:
        key = " ".join(sys.argv[sys.argv.index("--ctx") + 1:])
        for label, pat, _ in CHECKS:
            if key not in label:
                continue
            rx = re.compile(pat)
            for p in sorted(flat):
                for m in rx.finditer(flat[p]):
                    s = max(0, m.start() - 90)
                    print(f"[{label}] p{p}: …{flat[p][s:m.end() + 90]}…\n")
        return

    print(f"{'项目':<22}{'§':<5}{'命中页':<26}次数")
    print("-" * 76)
    miss = []
    for label, pat, sec in CHECKS:
        rx = re.compile(pat)
        hits = [(p, len(rx.findall(flat[p]))) for p in sorted(flat) if rx.search(flat[p])]
        pgs = ",".join(f"p{p}" for p, _ in hits[:4]) or "★未命中★"
        print(f"{label:<22}{sec:<5}{pgs:<26}{sum(n for _, n in hits)}")
        if not hits:
            miss.append(label)
    print("-" * 76)
    print(f"{len(CHECKS) - len(miss)}/{len(CHECKS)} 项在手册中命中")
    if miss:
        print("未命中（需人工看原文或确认是否已被手册改写）: " + "、".join(miss))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
메르 블로그 글 단위 분리 스크립트
각 섹터 폴더의 .txt 파일을 [숫자] 패턴으로 분리 → parsed/{섹터}/
"""
import re
import os
from pathlib import Path

BASE = Path.home() / "메르_리더"
INPUT = BASE / "input"
PARSED = BASE / "parsed"

# [숫자] 패턴 (줄 시작)
ARTICLE_START = re.compile(r'^\[(\d+)\]', re.MULTILINE)

summary = {}

for sector_dir in sorted(INPUT.iterdir()):
    if not sector_dir.is_dir():
        continue
    sector = sector_dir.name
    txt_files = sorted(sector_dir.glob("*.txt"))
    if not txt_files:
        continue

    # 섹터별 출력 폴더
    out_dir = PARSED / sector
    out_dir.mkdir(parents=True, exist_ok=True)

    global_num = 0  # 섹터 통합 글 번호

    for txt_file in txt_files:
        try:
            text = txt_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  [ERROR] {txt_file}: {e}")
            continue

        # [숫자] 위치 찾기
        matches = list(ARTICLE_START.finditer(text))
        if not matches:
            print(f"  [SKIP] {txt_file.name} — [숫자] 패턴 없음")
            continue

        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            article_text = text[start:end].strip()
            if not article_text:
                continue

            global_num += 1
            out_file = out_dir / f"{sector}_{global_num:03d}.txt"
            out_file.write_text(article_text, encoding="utf-8")

    summary[sector] = global_num
    print(f"  {sector}: {global_num}개")

print("\n=== 처리 완료 ===")
total = sum(summary.values())
for sector, cnt in sorted(summary.items(), key=lambda x: -x[1]):
    print(f"  {sector}: {cnt}개")
print(f"\n총 {total}개 글")

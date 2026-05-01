#!/usr/bin/env python3
"""
메르 글 → JSON 카드 생성 스크립트
글 1개 = API 호출 1개 원칙
"""
import re
import os
import json
import time
from pathlib import Path
import anthropic

BASE = Path.home() / "메르_리더"
PARSED = BASE / "parsed"
PROCESSED = BASE / "processed"

# 섹터 → 통합 폴더 매핑
SECTOR_MAP = {
    "금리·채권·통화정책": "금융·통화",
    "환율·외환시장": "금융·통화",
    "중동·지정학": "지정학",
    "중국경제·정치": "지정학",
    "미국경제·정책": "미국·글로벌",
    "글로벌 기타": "미국·글로벌",
    "한국경제·정책": "한국경제",
    "부동산·건설·PF": "부동산",
    "반도체·AI·기술": "기술·산업",
    "배터리·전기차": "기술·산업",
    "조선·방위산업": "중후장대",
    "주식·투자·금융": "자본시장",
    "에너지·원자재·기후": "에너지·자원",
}

SYSTEM_PROMPT = """너는 메르 블로그 글을 분석해서 JSON 카드를 만드는 어시스턴트야.

## "이 글이 말하는 것" 규칙
- 도입 단락 1개 + 소제목 단락 2~4개
- 도입: 시점·전체 그림 + 이 장면이 보여주는 것 (2~3문장). 도입에 시계열 위치 명시
- 각 소제목 단락: 3~4문장, 마지막에 중요도·의미 문장 1개
- 소제목: `짧은 핵심 구` (의문문·평가어 금지)
- 전체 약 450~550자
- 보고서 톤. 메르를 주어로 한 인용 표현 절대 금지. 인라인 번호 금지
- 핵심 숫자·고유명사 자연스럽게 녹이기

## "메르가 던지는 질문" 규칙
- 1문장, 질문 형식
- 글의 핵심 통찰을 질문으로 추출

## "나의 답" 규칙
- 2~3문장 (4문장 넘기지 말 것)
- 단호하게, 양시론 금지
- 본문에 없는 큰 추측 금지

## 원문 단락 규칙
- 원문 그대로 (구어체·반복 유지)
- 용어풀이: 처음 등장 어려운 용어·고유명사, 1~2줄 사실 정보
- 맥락풀이: 글 내부 인과·연결고리, 1~2줄
- 주석은 꼭 필요한 단락에만 (모든 단락에 달지 말 것)

반드시 유효한 JSON만 출력. 코드블록 없이 JSON 객체만."""

CARD_TEMPLATE = """다음 메르 블로그 글을 분석해서 JSON 카드를 만들어줘.

섹터_원래: {sector}
섹터_통합: {unified}

---
{article_text}
---

아래 JSON 구조로 출력:
{{
  "섹터_원래": "{sector}",
  "섹터_통합": "{unified}",
  "글_번호": {num},
  "글_제목": "제목",
  "날짜": "YYYY-MM-DD",
  "원본_링크": "https://...",
  "태그": ["#태그1", "#태그2"],
  "이_글이_말하는_것": {{
    "도입": "...",
    "단락1": {{"제목": "...", "본문": "..."}},
    "단락2": {{"제목": "...", "본문": "..."}},
    "단락3": {{"제목": "...", "본문": "..."}}
  }},
  "메르가_던지는_질문": "...?",
  "나의_답": "...",
  "원문_단락": [
    {{"번호": 1, "본문": "...", "용어풀이": null, "맥락풀이": null}},
    ...
  ]
}}"""


def extract_article_num(filename: str) -> int:
    m = re.search(r'_(\d+)\.txt$', filename)
    return int(m.group(1)) if m else 0


def process_article(client: anthropic.Anthropic, article_path: Path, sector: str, unified: str) -> dict | None:
    text = article_path.read_text(encoding="utf-8", errors="replace")
    num = extract_article_num(article_path.name)

    prompt = CARD_TEMPLATE.format(
        sector=sector,
        unified=unified,
        num=num,
        article_text=text
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            thinking={"type": "enabled", "budget_tokens": 3000},
            messages=[{"role": "user", "content": prompt}],
            system=SYSTEM_PROMPT,
        )

        # thinking 블록 제외하고 text만 추출
        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text = block.text
                break

        # JSON 파싱
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = re.sub(r'^```\w*\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)

        return json.loads(result_text)

    except json.JSONDecodeError as e:
        print(f"  [JSON ERROR] {article_path.name}: {e}")
        print(f"  Raw: {result_text[:200]}")
        return None
    except Exception as e:
        print(f"  [API ERROR] {article_path.name}: {e}")
        return None


def run(sector: str, limit: int | None = None):
    unified = SECTOR_MAP.get(sector, sector)
    parsed_dir = PARSED / sector
    out_dir = PROCESSED / unified
    out_dir.mkdir(parents=True, exist_ok=True)

    progress_file = BASE / "progress.log"
    errors_file = BASE / "errors.log"

    # 이미 처리된 파일 로드
    done = set()
    if progress_file.exists():
        for line in progress_file.read_text().splitlines():
            done.add(line.strip())

    articles = sorted(parsed_dir.glob("*.txt"))
    if limit:
        articles = articles[:limit]

    client = anthropic.Anthropic()

    print(f"\n[{sector}] → {unified} | 총 {len(articles)}개")

    for i, art_path in enumerate(articles, 1):
        key = art_path.name
        if key in done:
            print(f"  [{i}/{len(articles)}] SKIP {key}")
            continue

        print(f"  [{i}/{len(articles)}] {key} ...", end=" ", flush=True)

        result = process_article(client, art_path, sector, unified)

        if result:
            out_file = out_dir / art_path.name.replace(".txt", ".json")
            out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            with open(progress_file, "a") as f:
                f.write(key + "\n")
            print("OK")
        else:
            with open(errors_file, "a") as f:
                f.write(f"{key}\n")
            print("FAIL")

        # 속도 제한 방지
        if i < len(articles):
            time.sleep(0.5)

    print(f"\n완료: {out_dir}")


if __name__ == "__main__":
    import sys
    sector = sys.argv[1] if len(sys.argv) > 1 else "조선·방위산업"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(sector, limit)

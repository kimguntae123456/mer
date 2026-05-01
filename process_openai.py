#!/usr/bin/env python3
"""
메르 글 → JSON 카드 생성 (OpenAI gpt-4o-mini, 병렬 처리)
글 1개 = API 호출 1개 원칙
"""
import re
import os
import json
import asyncio
import aiofiles
from pathlib import Path
from openai import AsyncOpenAI

BASE = Path.home() / "메르_리더"
PARSED = BASE / "parsed"
PROCESSED = BASE / "processed"

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

FEW_SHOT_EXAMPLE = """
## 예시 출력 (이 스타일과 깔을 따를 것)

입력 섹터: 조선·방위산업
입력 글: 이라크 천궁-Ⅱ 수출 계약 관련 글

출력:
{
  "섹터_원래": "조선·방위산업",
  "섹터_통합": "중후장대",
  "글_번호": 2,
  "글_제목": "이라크에 천궁 팔았는데, 이게 이스라엘 이란 공격로 막는 거 아닌가",
  "원본_제목": "한국 방위산업 근황 업데이트 (feat 이라크 천궁-Ⅱ 수출)",
  "날짜": "2025-11-15",
  "원본_링크": "https://blog.naver.com/ranto28/224076955758",
  "태그": ["#천궁Ⅱ", "#이라크", "#LIG넥스원", "#이스라엘"],
  "이_글이_말하는_것": {
    "도입": "25년 11월 기준, 이라크의 3.7조원 천궁-Ⅱ 8개 포대 수출 계약이 복잡한 변수들을 끌어안고 있다. 이라크는 러시아제 S-400, 중국제 FD-2000B 도입을 연달아 실패한 끝에 천궁으로 방향을 틀었고, 작년 3월 구매의향 타진 후 6개월 만에 계약서에 서명했다. 무기거래가 짧아도 2년 걸리는 세계에서, 이 속도 자체가 이미 이상 신호다.",
    "도입_주석": [
      {"유형": "용어풀이", "대상": "천궁-Ⅱ", "내용": "한국형 중거리 지대공 미사일 체계. 패트리어트보다 3분의 1 가격에 AESA 레이더로 포대당 최대 40개 목표 동시 추적·요격 가능."}
    ],
    "단락1": {
      "제목": "이라크가 천궁을 선택한 경로",
      "본문": "이라크의 수다니 총리는 이란 혁명수비대의 간접 통제를 받는 인민동원군 기반의 반서방 인물로, 미국이 분류한 4단계 적대국이다. S-400은 러시아의 우크라이나 전쟁으로 공급 불가, FD-2000B는 협상 무산으로 한국 천궁이 마지막 선택지가 됐다. 달리 갈 곳이 없어진 이라크와 채울 수 있는 수출 공백이 맞아떨어진 구조다.",
      "주석": [
        {"유형": "맥락풀이", "내용": "S-400 → FD-2000B → 천궁 순서가 이라크의 구매 의도를 보여줌. 처음부터 서방 견제용 방공 체계를 원했던 것."}
      ]
    },
    "단락2": {
      "제목": "한국 안보 공백과 납품 구조의 긴장",
      "본문": "천궁-Ⅱ는 북한 탄도미사일 대응용으로 신규 배치 중인 자산이다. 이미 사우디·UAE에 20개 포대 발주로 생산 라인이 풀가동 중이고, 한국군 배치 일정도 밀리고 있다. 안보 공백을 감수하면서까지 진행되는 수출이라는 점에서 K2·K9 사례와 본질적으로 다르다.",
      "주석": []
    },
    "단락3": {
      "제목": "이스라엘 반발과 지정학적 위험 구조",
      "본문": "이스라엘에서 이란까지 어떤 경로로 가더라도 이라크 영공을 통과해야 한다. 이라크에 천궁이 배치되면 이스라엘의 이란 공격 경로에 방공망이 생기는 것이다. 계약은 체결됐고 납품만 남은 상태라 취소 단계는 지났다. 6개월 계약·1.5년 납품이라는 비정상적 속도가 돌아올 리스크를 미처 계산할 시간을 주지 않았다.",
      "주석": [
        {"유형": "맥락풀이", "내용": "이라크 영공은 이란-이스라엘 간 공격 통로로 실제 사용됨. 천궁 배치는 이 통로를 막는 효과."}
      ]
    }
  },
  "메르가_던지는_질문": "급하게 사겠다는 고객에게 평소보다 훨씬 조심해야 한다면, 이미 계약이 끝난 이라크 천궁 수출은 한국에 어떤 리스크로 돌아올 수 있을까?",
  "나의_답": "이스라엘이 이란 공격 시 이라크 영공을 우회할 방법이 없는 한, 납품 이후 천궁이 미·이스라엘 전투기에 위협이 되는 사태는 구조적으로 예정되어 있다. 계약 취소 단계는 지났고, 남은 선택지는 운용 조건이나 정치적 담보를 최대한 확보하는 것뿐인데, 그것도 이미 늦었을 가능성이 크다.",
  "원문_단락": [
    {"번호": 1, "본문": "오늘은 방위산업 업데이트입니다.", "용어풀이": null, "맥락풀이": null},
    {"번호": 2, "본문": "이라크가 천궁-Ⅱ를 사겠다고 했습니다.", "용어풀이": "천궁-Ⅱ: 한국형 지대공 미사일 체계. 패트리어트 대비 3분의 1 가격.", "맥락풀이": null}
  ]
}

## 이 예시에서 핵심 패턴
- 글_제목: 원본 제목을 버리고 핵심 사실+긴장을 담아 재작성. "이라크에 천궁 팔았는데, 이게 이스라엘 이란 공격로 막는 거 아닌가" — 30자 내외, 숫자/고유명사 살리기
- 도입: 시계열 위치 명시 ("25년 11월 기준"), 이상 신호·반전 포인트로 끝내기
- 소제목: 단정 구 형식 ("이라크가 천궁을 선택한 경로"), 의문문·평가어 금지
- 주석: 꼭 필요한 단락에만. 모든 단락에 달지 말 것
- 나의_답: YES/NO 중 하나. "필요하다", "중요하다", "고려해야 한다" 금지. 마지막 문장까지 입장 유지
"""

SYSTEM_PROMPT = f"""너는 메르 블로그 글을 분석해서 JSON 카드를 만드는 어시스턴트야.

{FEW_SHOT_EXAMPLE}

---

## 글_제목 작성 규칙
- 원본_제목은 그대로 "원본_제목" 필드에 보존
- 글_제목은 반드시 재작성: 핵심 사실 + 긴장·함의를 자연스럽게 담기
- 형식: 단정·의문·병치 중 글마다 가장 읽기 좋은 것
- 핵심 숫자·고유명사 살리기. 30자 내외. 평가어("놀랍다", "충격적") 금지

## "이 글이 말하는 것" 규칙
- 도입 단락 1개 + 소제목 단락 2~4개
- 도입: 시계열 위치 명시 + 이 장면이 보여주는 것 (2~3문장)
- 각 소제목 단락: 3~4문장, 마지막에 중요도·의미 문장 1개
- 소제목: 짧은 단정 구 (의문문·평가어 금지)
- 전체 약 450~550자
- 보고서 톤. 메르를 주어로 한 인용 표현 절대 금지. 인라인 번호 금지
- 메르 특유 비유·수치·표현은 그대로 살리기

## "메르가 던지는 질문" 규칙
- 1문장, 질문 형식
- 글 전체가 던지는 핵심 통찰을 질문으로

## "나의 답" 규칙
- 2~3문장 (4문장 넘기지 말 것)
- 반드시 YES/NO 중 하나를 고르고 그 이유 1가지만
- 마지막 문장: "~다" 또는 "~한다" 형식으로 끝낼 것
- 절대 금지: "필요하다", "중요하다", "고려해야 한다", "신중해야 한다", "균형이", "양면이"
- 절대 금지: 두 가지를 나열하며 둘 다 필요하다고 하는 구조
- 절대 금지: 조건절("~한다면")로만 결론 내는 것 — 반드시 현재 상황에 대한 판단을 담을 것

### 나의_답 BAD vs GOOD 예시

BAD: "외부 투자 유치와 실현 가능한 사업 모델이 동시에 필요하다."
→ 이유: 아무 입장도 없음. 당연한 말.

BAD: "대립 상황이 계속된다면 발루치족의 독립 요구가 더 강하게 표출될 가능성이 크다. 이는 이란과 파키스탄, 그리고 중국의 관계에도 부정적인 영향을 미칠 것이다."
→ 이유: 조건절+vague한 영향 나열. YES/NO 없음.

GOOD: "상속이 1순위다. 인적분할·에너지 상장·방산 분리 모두 상속세 재원 마련과 경영권 분리라는 목적이 뒤에 있다. 주주가치 개선은 부산물이지 목적이 아니다."

GOOD: "K9 SPH-M 수주가 가장 가시적인 기회고, 차륜형 공개는 그 준비다. 단거리 대드론 분야는 미국 AI 스타트업이 선점 중이라 한국이 끼어들기 어렵고, 한국의 강점은 여전히 재래식 화포와 중거리 방공 체계에 있다."

GOOD: "전면적 위기보다는 국지적 펀드런이 반복되는 형태일 것이다. 사기와 부실은 이미 있고, 공개될 때마다 해당 펀드에서 환매가 집중된다. 1.7조달러 전체로 번지려면 금리 급등이나 경기침체 같은 외부 충격이 동반돼야 한다."

GOOD: "현지생산·기술이전으로 들어간 이상, 핵심 부품 의존도를 유지하는 것이 유일한 잠금 수단이다. K-2PL의 엔진·포신을 폴란드가 자체 생산하기 시작하는 순간 잠금이 풀리므로, 그 전에 다음 업그레이드 사이클로 의존도를 갱신해야 한다."

### 글_제목 BAD vs GOOD 예시

BAD: "이란과 파키스탄의 갈등, 발루치족이 만든 복잡한 상황"
→ 이유: 핵심 긴장 없음. '복잡한 상황'은 평가어. 원본의 "짜고 치는" 표현을 날려버림.

GOOD: "이란·파키스탄이 서로 쏘는 척 짜고 치는데, 발루치족은 그걸 모른다"
→ 원본 제목의 핵심 표현("짜고 치는")을 살려서 아이러니를 전면에

GOOD: "이라크에 천궁 팔았는데, 이게 이스라엘 이란 공격로 막는 거 아닌가"
GOOD: "인도-파키스탄전에서 중국제 J-10C가 라팔 3대를 격추했다, 이게 의미하는 것"
GOOD: "K2 연 200대 뽑는 나라가, 레오파르트 연 50대 독일을 제쳤다"
GOOD: "후티 미사일이 이스라엘 공항을 뚫었다 — 극초음속 미사일 앞에 방공망이 흔들린다"

**글_제목 추가 규칙**: 원본 제목에 메르 특유의 비유·표현("짜고 치는", "영끌", "더 콤마가 됐다" 등)이 있으면 그 표현을 중심으로 재작성. 가장 반직관적·아이러니한 요소를 앞에 꺼낼 것.

## 원문_단락 규칙
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
  "글_제목": "재작성된 제목",
  "원본_제목": "원본 제목 그대로",
  "날짜": "YYYY-MM-DD",
  "원본_링크": "https://...",
  "태그": ["#태그1", "#태그2"],
  "이_글이_말하는_것": {{
    "도입": "...",
    "도입_주석": [],
    "단락1": {{"제목": "...", "본문": "...", "주석": []}},
    "단락2": {{"제목": "...", "본문": "...", "주석": []}},
    "단락3": {{"제목": "...", "본문": "...", "주석": []}}
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


async def process_article(client: AsyncOpenAI, article_path: Path, sector: str, unified: str) -> dict | None:
    text = article_path.read_text(encoding="utf-8", errors="replace")
    num = extract_article_num(article_path.name)

    prompt = CARD_TEMPLATE.format(
        sector=sector,
        unified=unified,
        num=num,
        article_text=text
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=8000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content.strip()
        return json.loads(result_text)

    except json.JSONDecodeError as e:
        print(f"  [JSON ERROR] {article_path.name}: {e}")
        return None
    except Exception as e:
        print(f"  [API ERROR] {article_path.name}: {e}")
        return None


async def run_sector(client: AsyncOpenAI, sector: str, semaphore: asyncio.Semaphore,
                     done: set, progress_file: Path, errors_file: Path, out_dir: Path,
                     articles: list, unified: str):
    async def process_one(i, art_path):
        key = art_path.name
        if key in done:
            print(f"  SKIP {key}")
            return

        async with semaphore:
            print(f"  [{i}/{len(articles)}] {key} ...", end=" ", flush=True)
            result = await process_article(client, art_path, sector, unified)

        if result:
            out_file = out_dir / art_path.name.replace(".txt", ".json")
            out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            async with aiofiles.open(progress_file, "a") as f:
                await f.write(key + "\n")
            print("OK")
        else:
            async with aiofiles.open(errors_file, "a") as f:
                await f.write(f"{key}\n")
            print("FAIL")

    tasks = [process_one(i, art_path) for i, art_path in enumerate(articles, 1)]
    await asyncio.gather(*tasks)


async def run_all(sectors: list):
    progress_file = BASE / "progress.log"
    errors_file = BASE / "errors.log"

    done = set()
    if progress_file.exists():
        for line in progress_file.read_text().splitlines():
            done.add(line.strip())

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    semaphore = asyncio.Semaphore(5)  # 최대 5개 동시 처리

    for sector in sectors:
        unified = SECTOR_MAP.get(sector, sector)
        parsed_dir = PARSED / sector
        out_dir = PROCESSED / unified
        out_dir.mkdir(parents=True, exist_ok=True)

        articles = sorted(parsed_dir.glob("*.txt"))
        remaining = [a for a in articles if a.name not in done]

        print(f"\n[{sector}] → {unified} | 총 {len(articles)}개 (잔여 {len(remaining)}개)")

        await run_sector(client, sector, semaphore, done, progress_file, errors_file, out_dir, articles, unified)

        # done 갱신
        if progress_file.exists():
            done = set(l.strip() for l in progress_file.read_text().splitlines())

        print(f"  완료: {out_dir}")

    await client.close()


if __name__ == "__main__":
    import sys

    ALL_SECTORS = [
        "중동·지정학",
        "반도체·AI·기술",
        "환율·외환시장",
        "미국경제·정책",
        "중국경제·정치",
        "부동산·건설·PF",
        "금리·채권·통화정책",
        "에너지·원자재·기후",
        "글로벌 기타",
    ]

    if len(sys.argv) > 1:
        sectors = [sys.argv[1]]
    else:
        sectors = ALL_SECTORS

    asyncio.run(run_all(sectors))

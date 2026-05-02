#!/usr/bin/env python3
"""
메르 블로그 새 글 수집 스크립트
RSS → 본문 크롤링 → OpenAI 처리 → HTML 재생성
"""
import re
import os
import json
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from html.parser import HTMLParser

BASE = Path(__file__).parent
PARSED = BASE / "parsed" / "신규"
PROCESSED_NEW = BASE / "processed" / "신규"
PROGRESS = BASE / "progress.log"
NEW_LOG = BASE / "new_posts.log"

RSS_URL = "https://rss.blog.naver.com/ranto28"
BLOG_BASE = "https://blog.naver.com"

# 비경제 글 블랙리스트 키워드 (제목에 포함 시 즉시 제외)
BLACKLIST_KEYWORDS = [
    "맛집", "카페", "음식", "먹지", "먹을", "고등어", "밀면", "곰장어",
    "간장", "와사비", "소금빵", "생선구이", "커피", "라면",
    "여행", "부산", "제주", "유럽",
    "블로그", "이웃", "키우는", "후기", "리포트",
    "주절주절", "주린이", "딸", "아들",
    "영화", "드라마", "넷플릭스", "책",
    "운동", "건강", "다이어트", "심근경색", "오메가3", "유산균", "장건강",
    "피부", "탈모", "비만약", "스킨부스터", "보톡스",
    "일상", "소식", "기부인증", "기부내용", "추천맛집",
    "포트폴리오 근황", "포트폴리오 업데이트",
]

# 경제 분석 글 화이트리스트 (포함 시 바로 통과)
WHITELIST_KEYWORDS = [
    "경제", "금리", "금융", "환율", "달러", "원화", "주식", "채권",
    "부동산", "PF", "금값", "유가", "원유", "반도체", "AI",
    "미국", "중국", "일본", "연준", "FOMC", "Fed",
    "관세", "무역", "수출", "수입", "GDP", "인플레",
    "은행", "증권", "펀드", "ETF", "비트코인", "코인",
    "방위산업", "조선", "배터리", "전기차",
    "feat", "근황", "업데이트",  # 메르 경제글 패턴
]


def is_relevant(title: str) -> str:
    """제목 기반 관련성 판단. 'yes'/'no'/'maybe' 반환"""
    title_lower = title.lower()
    for kw in BLACKLIST_KEYWORDS:
        if kw in title:
            return "no"
    for kw in WHITELIST_KEYWORDS:
        if kw.lower() in title_lower:
            return "yes"
    return "maybe"


async def classify_relevance(client, title: str) -> bool:
    """애매한 제목을 OpenAI로 판단 (초저비용)"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=5,
            messages=[{
                "role": "user",
                "content": f"다음 블로그 글 제목이 경제·금융·지정학 분석 글이면 YES, 맛집·여행·일상·블로그운영이면 NO로만 답해:\n\n{title}"
            }]
        )
        ans = response.choices[0].message.content.strip().upper()
        return "YES" in ans
    except Exception:
        return True  # 오류 시 처리 시도

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
    "신규": "신규",
}

ALL_SECTORS = list(SECTOR_MAP.keys())


class NaverBlogParser(HTMLParser):
    """네이버 블로그 본문 추출"""
    def __init__(self):
        super().__init__()
        self.in_content = False
        self.depth = 0
        self.text_parts = []
        self.content_div = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if "se-main-container" in cls or "post-view" in cls or "se_component_wrap" in cls:
            self.in_content = True
            self.depth = 1
        elif self.in_content:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.in_content:
            self.depth -= 1
            if self.depth <= 0:
                self.in_content = False

    def handle_data(self, data):
        if self.in_content:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

    def get_text(self):
        return "\n".join(self.text_parts)


def fetch_rss():
    """RSS에서 최신 글 목록 가져오기"""
    req = Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as r:
        xml_data = r.read()
    root = ET.fromstring(xml_data)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        if link:
            items.append({"title": title, "link": link, "pub_date": pub_date})
    return items


def fetch_blog_postlist(since_date: str, max_pages: int = 20) -> list:
    """
    네이버 블���그 PostTitleListAsync API로 since_date 이후 글 수집
    since_date: 'YYYY-MM-DD'
    """
    from urllib.parse import unquote
    items = []
    cutoff = datetime.strptime(since_date, "%Y-%m-%d")

    for page in range(1, max_pages + 1):
        url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId=ranto28&currentPage={page}&countPerPage=30"
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://blog.naver.com/ranto28"
        })
        try:
            with urlopen(req, timeout=15) as r:
                raw = r.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  [API 오류 p{page}] {e}")
            break

        # JSON 파싱이 깨질 수 있어 regex로 추출
        posts = re.findall(
            r'"logNo":"(\d+)","title":"([^"]*)",".*?"addDate":"([^"]*?)"', raw
        )

        if not posts:
            break

        found_old = False
        for logno, title_enc, add_date in posts:
            link = f"https://blog.naver.com/ranto28/{logno}"
            title = unquote(title_enc).replace("+", " ").replace("&quot;", '"')

            # 날짜 파싱 ("2026. 4. 30." 또는 "10시간 전" 등)
            date_str = ""
            date_m = re.match(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})', add_date)
            if date_m:
                y, m, d = date_m.groups()
                dt = datetime(int(y), int(m), int(d))
                date_str = dt.strftime("%Y-%m-%d")
                if dt < cutoff:
                    found_old = True
                    continue
            else:
                # "N시간 전", "N일 전" 등 → 오늘 날짜로 처리
                date_str = datetime.now().strftime("%Y-%m-%d")

            items.append({"title": title, "link": link, "pub_date": date_str})

        if found_old:
            break

    return items


def fetch_blog_content(url: str) -> str:
    """네이버 블로그 본문 텍스트 추출"""
    # 모바일 URL로 변환 (파싱 쉬움)
    post_id = url.rstrip("/").split("/")[-1]
    blog_id = url.split("/")[3] if "blog.naver.com" in url else "ranto28"
    mobile_url = f"https://m.blog.naver.com/{blog_id}/{post_id}"

    req = Request(mobile_url, headers={
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
    })
    try:
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception:
        # fallback to original URL
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")

    # 간단한 정규식으로 텍스트 추출
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

    # se-main-container부터 본문 끝까지 추출
    m = re.search(r'class="se-main-container"(.*?)(?=<div[^>]*class="[^"]*(?:comment|footer|aside|wrap_btn)[^"]*")', html, re.DOTALL)
    if not m:
        # fallback: se-main-container부터 넉넉히
        m = re.search(r'class="se-main-container"(.{500,50000})', html, re.DOTALL)
    if not m:
        m = re.search(r'id="postViewArea"(.*?)(?=<div class="wrap_btn_post"|</body>)', html, re.DOTALL)

    raw = m.group(0) if m else html[:50000]
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = re.sub(r'\s+', '\n', text).strip()
    return text


def get_processed_links() -> set:
    """이미 처리된 링크 목록 (new_posts.log)"""
    if NEW_LOG.exists():
        return set(NEW_LOG.read_text().splitlines())
    return set()


async def classify_and_process(client, title: str, content: str, link: str, date: str) -> dict | None:
    """OpenAI로 섹터 분류 + 카드 생성"""
    from openai import AsyncOpenAI
    from process_openai import SYSTEM_PROMPT

    sector_list = "\n".join(f"- {s}" for s in ALL_SECTORS[:-1])

    prompt = f"""다음 메르 블로그 새 글을 분석해서 JSON 카드를 만들어줘.

먼저 아래 섹터 중 가장 적합한 것 1개를 골라:
{sector_list}

섹터_통합 매핑:
금리·채권·통화정책→금융·통화, 환율·외환시장→금융·통화, 중동·지정학→지정학, 중국경제·정치→지정학, 미국경제·정책→미국·글로벌, 글로벌 기타→미국·글로벌, 한국경제·정책→한국경제, 부동산·건설·PF→부동산, 반도체·AI·기술→기술·산업, 배터리·전기차→기술·산업, 조선·방위산업→중후장대, 주식·투자·금융→자본시장, 에너지·원자재·기후→에너지·자원

아래 JSON 구조로 출력:
{{
  "섹터_원래": "선택한 섹터",
  "섹터_통합": "매핑표에 따른 통합 폴더",
  "글_번호": 0,
  "글_제목": "재작성된 제목",
  "원본_제목": "{title}",
  "날짜": "{date}",
  "원본_링크": "{link}",
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
    {{"번호": 2, "본문": "...", "용어풀이": null, "맥락풀이": null}}
  ]
}}

---
{content[:12000]}
---"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=8000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"  [ERROR] {title}: {e}")
        return None


async def main(backfill_since: str = None):
    import sys
    if backfill_since is None and "--backfill" in sys.argv:
        idx = sys.argv.index("--backfill")
        backfill_since = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "2025-04-06"

    if backfill_since:
        print(f"백필 모드: {backfill_since} 이후 글 수집 중...")
        try:
            items = fetch_blog_postlist(since_date=backfill_since, max_pages=20)
            print(f"  목록에서 {len(items)}개 발견")
        except Exception as e:
            print(f"목록 수집 오류: {e}")
            # fallback to RSS
            items = fetch_rss()
    else:
        print("RSS 확인 중...")
        try:
            items = fetch_rss()
        except Exception as e:
            print(f"RSS 오류: {e}")
            return

    processed_links = get_processed_links()
    new_items = [it for it in items if it["link"] not in processed_links]

    if not new_items:
        print("새 글 없음.")
        return

    print(f"새 글 {len(new_items)}개 발견 — 관련성 필터링 중...")

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # 관련성 필터
    filtered_items = []
    for item in new_items:
        title = item["title"]
        relevance = is_relevant(title)
        if relevance == "no":
            print(f"  [제외] {title[:50]}")
        elif relevance == "yes":
            filtered_items.append(item)
        else:  # maybe
            ok = await classify_relevance(client, title)
            if ok:
                filtered_items.append(item)
            else:
                print(f"  [제외-AI] {title[:50]}")

    print(f"경제 관련 글 {len(filtered_items)}개 처리 시작")

    PARSED.mkdir(parents=True, exist_ok=True)

    new_count = 0
    for item in filtered_items:
        title = item["title"]
        link = item["link"]
        print(f"  처리: {title[:40]}...")

        try:
            content = fetch_blog_content(link)
        except Exception as e:
            print(f"    [크롤링 실패] {e}")
            continue

        # 날짜: pub_date가 이미 YYYY-MM-DD면 그대로 사용
        pub = item.get("pub_date", "")
        if re.match(r'\d{4}-\d{2}-\d{2}', pub):
            date_str = pub[:10]
        else:
            try:
                from email.utils import parsedate
                dt = datetime(*parsedate(pub)[:6])
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")

        result = await classify_and_process(client, title, content, link, date_str)
        if not result:
            continue

        # 적절한 폴더에 저장
        sector = result.get("섹터_원래", "신규")
        unified = SECTOR_MAP.get(sector, "신규")

        # 후처리: 섹터_통합 강제 매핑, 글_번호 자동 할당
        result["섹터_통합"] = unified

        out_dir = BASE / "processed" / unified
        out_dir.mkdir(parents=True, exist_ok=True)

        # 글_번호: 해당 폴더 내 같은 섹터의 max+1
        existing_nums = []
        for f in out_dir.glob(f"{sector}_*.json"):
            m = re.search(r'_(\d{3,})\.json$', f.name)
            if m:
                existing_nums.append(int(m.group(1)))
        next_num = max(existing_nums, default=0) + 1
        result["글_번호"] = next_num

        # 파일명: 섹터_글번호.json (기존 형식 통일)
        fname = f"{sector}_{next_num:03d}.json"
        (out_dir / fname).write_text(json.dumps(result, ensure_ascii=False, indent=2))

        # 로그 기록
        with open(NEW_LOG, "a") as f:
            f.write(link + "\n")

        new_count += 1
        print(f"    OK → {unified}/{fname}")

    await client.close()

    if new_count > 0:
        print(f"\n{new_count}개 처리 완료. HTML 재생성 중...")
        import subprocess
        subprocess.run(["python3", str(BASE / "render_html.py")], check=True)
        print("완료.")
    else:
        print("처리된 새 글 없음.")


if __name__ == "__main__":
    import sys
    backfill = None
    if "--backfill" in sys.argv:
        idx = sys.argv.index("--backfill")
        backfill = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "2025-04-06"
    asyncio.run(main(backfill_since=backfill))

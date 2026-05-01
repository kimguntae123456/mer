#!/usr/bin/env python3
"""
메르 리더 HTML 렌더러 v3
processed/ JSON → output/ (React SPA with pre-built design files)
"""
import json
import html
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROCESSED = BASE / "processed"
OUTPUT = BASE / "output"
HANDOFF = Path.home() / "Downloads" / "메르"

# Static files to copy from handoff directory
STATIC_FILES = [
    "index.html",
    "styles.css",
    "components.jsx",
    "article-view.jsx",
    "clips.jsx",
    "app.jsx",
    "tweaks-panel.jsx",
    "manifest.json",
    "sw.js",
    "icon-192.svg",
    "icon-512.svg",
]


def build_all_data():
    """processed/ 전체 JSON 로드"""
    all_cards = []
    for folder_dir in sorted(PROCESSED.iterdir()):
        if not folder_dir.is_dir():
            continue
        for jf in sorted(folder_dir.glob("*.json")):
            try:
                d = json.loads(jf.read_text(encoding="utf-8"))
                all_cards.append(d)
            except Exception as e:
                print(f"  [SKIP] {jf.name}: {e}")
    return all_cards


def card_to_data(d):
    """JSON 카드 → React app이 기대하는 dict"""
    body = d.get("이_글이_말하는_것", {})
    paras = []
    for key in ["단락1", "단락2", "단락3", "단락4"]:
        p = body.get(key)
        if p and isinstance(p, dict):
            paras.append({
                "title": p.get("제목", ""),
                "body": p.get("본문", ""),
                "anns": p.get("주석", []),
            })
    return {
        "title": d.get("글_제목", d.get("원본_제목", "")),
        "date": d.get("날짜", ""),
        "folder": d.get("섹터_통합", ""),
        "sector": d.get("섹터_원래", ""),
        "tags": d.get("태그", []),
        "intro": body.get("도입", ""),
        "intro_anns": body.get("도입_주석", []),
        "paras": paras,
        "question": d.get("메르가_던지는_질문", ""),
        "answer": d.get("나의_답", ""),
        "link": d.get("원본_링크", ""),
    }


def escape_for_js(s):
    """Escape string fields for safe embedding in JS."""
    if not isinstance(s, str):
        return s
    s = html.escape(s)
    # Prevent </script> injection
    s = s.replace("</script>", "<\\/script>")
    return s


def escape_data(obj):
    """Recursively escape string values in data structure."""
    if isinstance(obj, str):
        return escape_for_js(obj)
    elif isinstance(obj, list):
        return [escape_data(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: escape_data(v) for k, v in obj.items()}
    return obj


def generate_data_js(all_cards):
    """Generate data.js with window.MERU_DATA = [...]"""
    compact = [card_to_data(d) for d in sorted(
        all_cards, key=lambda x: x.get("날짜", ""), reverse=True
    )]
    escaped = escape_data(compact)
    data_json = json.dumps(escaped, ensure_ascii=False, separators=(",", ":"))
    # Extra safety: replace any literal </script> in the JSON string
    data_json = data_json.replace("</script>", "<\\/script>")
    return f"window.MERU_DATA = {data_json};\n"


def copy_static_files():
    """Copy pre-built static files from handoff to output."""
    copied = []
    for fname in STATIC_FILES:
        src = HANDOFF / fname
        if src.exists():
            shutil.copy2(src, OUTPUT / fname)
            copied.append(fname)
        else:
            print(f"  [WARN] 핸드오프에 없음: {fname}")
    return copied


def main():
    OUTPUT.mkdir(exist_ok=True)

    # 1. Copy static files
    copied = copy_static_files()
    print(f"정적 파일 {len(copied)}개 복사: {', '.join(copied)}")

    # 2. Generate data.js from processed/ JSONs
    all_cards = build_all_data()
    print(f"총 {len(all_cards)}개 글 로드")

    data_js = generate_data_js(all_cards)
    (OUTPUT / "data.js").write_text(data_js, encoding="utf-8")
    print(f"→ {OUTPUT}/data.js 생성 ({len(data_js)//1024}KB)")

    print("완료")


if __name__ == "__main__":
    main()

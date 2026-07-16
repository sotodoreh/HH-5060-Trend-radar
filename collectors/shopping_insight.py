# -*- coding: utf-8 -*-
"""트랙 1 — 네이버 데이터랩 쇼핑인사이트 인기검색어 수집.

내부 API(getCategoryKeywordRank.naver)를 직접 호출한다. Playwright 불필요.
카테고리 × (50대+60대 여성) 필터로 주간 인기검색어 TOP500을 가져온다.
"""
import sys
import time
import datetime as dt

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config


def _week_range(end: dt.date | None = None) -> tuple[str, str]:
    """데이터랩 주간 조회 구간. 직전 일요일을 끝으로 4주 구간을 잡는다.

    (데이터랩 주간 단위는 월~일. 마지막 완결 주의 일요일을 endDate 로 사용)
    """
    today = end or dt.date.today()
    # 직전 일요일
    last_sunday = today - dt.timedelta(days=today.weekday() + 1)
    start = last_sunday - dt.timedelta(days=27)  # 4주 구간
    return start.isoformat(), last_sunday.isoformat()


def fetch_category_keywords(cid: int, pages: int = config.TOP_N_PAGES,
                            start_date: str | None = None,
                            end_date: str | None = None) -> list[dict]:
    """한 카테고리의 인기검색어를 페이지 순회로 수집. [{rank, keyword}, ...]"""
    if not (start_date and end_date):
        start_date, end_date = _week_range()

    session = requests.Session()
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Referer": config.DATALAB_REFERER,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    })

    results: list[dict] = []
    for page in range(1, pages + 1):
        body = {
            "cid": cid,
            "timeUnit": config.TIME_UNIT,
            "startDate": start_date,
            "endDate": end_date,
            "age": config.TARGET_AGE,
            "gender": config.TARGET_GENDER,
            "count": 20,
            "page": page,
        }
        resp = session.post(config.DATALAB_RANK_URL, data=body,
                            timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        ranks = data.get("ranks") or []
        if not ranks:
            break
        results.extend({"rank": r["rank"], "keyword": r["keyword"]} for r in ranks)
        time.sleep(config.REQUEST_DELAY_SEC)
    return results


def collect_all(pages: int = config.TOP_N_PAGES) -> dict:
    """8개 카테고리 전체 수집. {카테고리명: [{rank, keyword}, ...]}"""
    out = {}
    start_date, end_date = _week_range()
    print(f"[track1] 조회 구간: {start_date} ~ {end_date} / 페이지 {pages} (={pages*20}위까지)")
    for name, info in config.CATEGORIES.items():
        print(f"[track1] {name} (cid={info['cid']}) 수집 중...")
        try:
            out[name] = fetch_category_keywords(info["cid"], pages, start_date, end_date)
            print(f"[track1]   → {len(out[name])}개")
        except Exception as e:  # 한 카테고리 실패가 전체를 죽이지 않도록
            print(f"[track1]   ⚠️ 실패: {e}")
            out[name] = []
    return {"period": f"{start_date} ~ {end_date}", "keywords": out}


if __name__ == "__main__":
    import json
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print(json.dumps(collect_all(pages), ensure_ascii=False, indent=2)[:3000])

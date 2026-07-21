# -*- coding: utf-8 -*-
"""트랙 2 — 네이버쇼핑 베스트(SNX Best) 수집.

snxbest.naver.com 내부 API를 무인증으로 호출한다 (2026-07-21 검증).
5060 여성(WOMEN_50) 기준 이슈/신규/인기 구매 키워드 + 각 키워드의 인기상품(리뷰수 포함).

구조:
  keyword/rank   → 급상승/신규/인기 구매 키워드 20개 (rankFluctuation=순위변동 내장)
  keyword/rank/{rankId} → 해당 키워드 상품 20개 (title/price/reviewCount)
"""
import sys
import time
import datetime as dt

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config


def _recent_sunday(d: dt.date | None = None) -> dt.date:
    """가장 최근 일요일 (SNX 주간 데이터의 ymd 기준)."""
    d = d or dt.date.today()
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)  # Mon=0..Sun=6


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "ko,en;q=0.9",
        "Referer": config.SNX_REFERER,
    })
    return s


def _fetch_keywords(s: requests.Session, sort_type: str, ymd: str, count: int) -> list[dict]:
    url = (f"{config.SNX_RANK_URL}?ageType={config.SNX_AGE_TYPE}&categoryId=A"
           f"&sortType={sort_type}&periodType=WEEKLY&ymd={ymd}")
    r = s.get(url, timeout=config.REQUEST_TIMEOUT)
    r.raise_for_status()
    return (r.json() or [])[:count]


def _fetch_products(s: requests.Session, rank_id: str, count: int) -> list[dict]:
    r = s.get(f"{config.SNX_RANK_URL}/{rank_id}", timeout=config.REQUEST_TIMEOUT)
    r.raise_for_status()
    prods = (r.json() or {}).get("products", [])
    out = []
    for p in prods[:count]:
        rc = str(p.get("reviewCount", "")).replace(",", "")
        out.append({
            "rank": p.get("rank"),
            "title": p.get("title"),
            "price": p.get("price"),
            "review_count": int(rc) if rc.isdigit() else None,
            "review_score": p.get("reviewScore"),
            "url": p.get("linkUrl"),
            "is_ad": bool(p.get("isAd")),
        })
    return out


def collect_all() -> dict:
    """{'ymd': 'YYYYMMDD', 'hype': {'이슈': [...], '신규': [...], '인기': [...]}}

    각 항목: {rank, keyword, category, rank_fluctuation, status, products:[...]}
    """
    if not config.NAVER_BEST_ENABLED:
        print("[track2] 비활성화 상태 — 건너뜀")
        return {}

    s = _session()

    # ymd 결정: 최근 일요일 → 데이터 없으면(0건) 전주 일요일로 폴백
    ymd = None
    for back in (0, 7, 14):
        cand = (_recent_sunday() - dt.timedelta(days=back)).strftime("%Y%m%d")
        try:
            probe = _fetch_keywords(s, "KEYWORD_ISSUE", cand, 1)
            if probe:
                ymd = cand
                break
        except Exception as e:
            print(f"[track2] ymd={cand} 조회 실패: {e}")
    if not ymd:
        print("[track2] 유효한 주간 데이터를 찾지 못함 — 건너뜀")
        return {}

    print(f"[track2] SNX Best 수집 (ymd={ymd}, 대상={config.SNX_AGE_TYPE})")
    hype = {}
    for sort_type, label in config.SNX_SORT_TYPES.items():
        try:
            kws = _fetch_keywords(s, sort_type, ymd, config.HYPE_KEYWORDS)
            items = []
            for k in kws:
                prods = _fetch_products(s, k["rankId"], config.HYPE_PRODUCTS)
                items.append({
                    "rank": k.get("rank"),
                    "keyword": k.get("title"),
                    "sub": k.get("subTitle"),
                    "category": k.get("catNm1"),
                    "rank_fluctuation": k.get("rankFluctuation"),
                    "status": k.get("status"),          # STABLE/UP/DOWN/NEW 등
                    "products": prods,
                })
                time.sleep(config.REQUEST_DELAY_SEC)
            hype[label] = items
            print(f"[track2]   {label}: 키워드 {len(items)}개")
        except Exception as e:
            print(f"[track2]   {label} 실패: {e}")
            hype[label] = []
    return {"ymd": ymd, "hype": hype}


if __name__ == "__main__":
    import json
    print(json.dumps(collect_all(), ensure_ascii=False, indent=2)[:2500])

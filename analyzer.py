# -*- coding: utf-8 -*-
"""델타 계산 · 급상승/신규 진입 감지 · 렌탈 파생 카테고리 구성.

입력: 이번 주 스냅샷 + (있으면) 전주 스냅샷 (data/history/YYYY-WW.json)
출력: 대시보드가 읽는 latest.json 의 keywords / rising / stats 부분
"""
import re

import config


def _index_by_keyword(rows: list[dict]) -> dict[str, int]:
    return {r["keyword"]: r["rank"] for r in rows}


def build_derived(keywords_by_cat: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """렌탈상품 등 파생 카테고리: 전 카테고리 키워드에서 패턴 매칭으로 추출."""
    derived = {}
    for name, spec in config.DERIVED_CATEGORIES.items():
        pat = re.compile(spec["pattern"])
        hits = []
        for cat, rows in keywords_by_cat.items():
            for r in rows:
                if pat.search(r["keyword"]):
                    hits.append({"keyword": r["keyword"], "rank": r["rank"], "source": cat})
        # 원 카테고리 순위 기준 정렬 후 재순위 부여
        hits.sort(key=lambda x: x["rank"])
        derived[name] = [
            {"rank": i + 1, "keyword": h["keyword"], "source": h["source"]}
            for i, h in enumerate(hits)
        ]
    return derived


def compute_deltas(current: dict[str, list[dict]],
                   previous: dict[str, list[dict]] | None) -> dict[str, list[dict]]:
    """카테고리별로 prev_rank / delta / is_new 를 붙인다."""
    out = {}
    for cat, rows in current.items():
        prev_idx = _index_by_keyword(previous.get(cat, [])) if previous else {}
        enriched = []
        for r in rows:
            prev_rank = prev_idx.get(r["keyword"])
            item = {
                "rank": r["rank"],
                "keyword": r["keyword"],
                "prev_rank": prev_rank,
                "delta": (prev_rank - r["rank"]) if prev_rank else None,
                "is_new": previous is not None and prev_rank is None,
            }
            if "source" in r:
                item["source"] = r["source"]
            enriched.append(item)
        out[cat] = enriched
    return out


def pick_rising(keywords: dict[str, list[dict]]) -> list[dict]:
    """급상승(delta >= RISING_MIN_DELTA) + 신규 진입 키워드를 전 카테고리에서 추출."""
    rising = []
    for cat, rows in keywords.items():
        for r in rows:
            if r["is_new"] or (r["delta"] is not None and r["delta"] >= config.RISING_MIN_DELTA):
                rising.append({"category": cat, **{k: r[k] for k in
                               ("rank", "keyword", "prev_rank", "delta", "is_new")}})
    # 신규는 현재 순위 오름차순, 급상승은 델타 내림차순 — 섞어서 스코어 정렬
    def score(x):
        if x["is_new"]:
            return 1000 - x["rank"]          # 신규는 상위 진입일수록 높게
        return x["delta"]                     # 급상승은 델타 크기
    rising.sort(key=score, reverse=True)
    return rising[: config.RISING_TOP_LIMIT]


def analyze(current_snapshot: dict, previous_snapshot: dict | None) -> dict:
    """스냅샷 2개 → 대시보드 데이터 골격 생성."""
    cur_kw = dict(current_snapshot["keywords"])
    cur_kw.update(build_derived(current_snapshot["keywords"]))

    prev_kw = None
    if previous_snapshot:
        prev_kw = dict(previous_snapshot["keywords"])
        prev_kw.update(build_derived(previous_snapshot["keywords"]))

    keywords = compute_deltas(cur_kw, prev_kw)
    rising = pick_rising(keywords)

    # 대시보드 노출은 카테고리당 상위 N개로 제한 (수집분은 히스토리에 전량 보존)
    keywords_view = {
        cat: rows[: config.KEYWORDS_PER_CATEGORY] for cat, rows in keywords.items()
    }

    stats = {
        "rising_count": sum(1 for r in rising if not r["is_new"]),
        "new_count": sum(1 for r in rising if r["is_new"]),
        "gap_count": None,  # Hmall 체크 활성화 후 채움
    }
    return {"keywords": keywords_view, "rising": rising, "stats": stats}

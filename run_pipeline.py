# -*- coding: utf-8 -*-
"""주간 파이프라인 오케스트레이터.

수집(트랙1·2) → 히스토리 저장 → 델타 분석 → (Hmall 체크) → Claude 인사이트
→ data/latest.json + docs/data/latest.json 생성

사용법:
  python run_pipeline.py                # 정식 실행 (TOP500)
  python run_pipeline.py --pages 2      # 테스트 (TOP40)
  python run_pipeline.py --skip-insight # Claude API 호출 없이
"""
import sys
if hasattr(sys.stdout, "reconfigure"):  # Windows 콘솔(cp949)에서 한글/이모지 출력 오류 방지
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

import config
import analyzer
import insight as insight_mod
from collectors import shopping_insight, naver_best

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
HISTORY = DATA / "history"
DOCS_DATA = ROOT / "docs" / "data"


def iso_week(d: dt.date | None = None) -> str:
    d = d or dt.date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def prev_snapshot(current_week: str) -> dict | None:
    """히스토리에서 현재 주차 이전의 가장 최근 스냅샷을 찾는다."""
    files = sorted(HISTORY.glob("*.json"))
    candidates = [f for f in files if f.stem < current_week]
    if not candidates:
        return None
    with open(candidates[-1], encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=config.TOP_N_PAGES,
                    help="카테고리당 수집 페이지 수 (페이지당 20개)")
    ap.add_argument("--skip-insight", action="store_true")
    args = ap.parse_args()

    week = iso_week()
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))  # KST

    # 1) 수집
    track1 = shopping_insight.collect_all(pages=args.pages)
    track2 = naver_best.collect_all()   # {"ymd":.., "hype":{이슈/신규/인기}} or {}
    hype = track2.get("hype", {})

    # 2) 히스토리 스냅샷 저장 (델타 계산의 원천 — 전량 보존)
    HISTORY.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "week": week,
        "collected_at": now.isoformat(),
        "period": track1["period"],
        "keywords": track1["keywords"],
        "hype": hype,
        "hype_ymd": track2.get("ymd"),
    }
    snap_path = HISTORY / f"{week}.json"
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False)
    print(f"[pipeline] 스냅샷 저장: {snap_path}")

    # 3) 델타 분석
    prev = prev_snapshot(week)
    print(f"[pipeline] 전주 스냅샷: {'있음 (' + prev['week'] + ')' if prev else '없음 — 첫 주는 델타 없이 진행'}")
    result = analyzer.analyze(snapshot, prev)

    # 4) 인사이트
    if args.skip_insight:
        insights = {"generated": False, "summary": "", "candidates": []}
    else:
        insights = insight_mod.generate_insights(result["rising"], hype or None)

    # 5) latest.json 조립
    latest = {
        "meta": {
            "week": week,
            "generated_at": now.isoformat(),
            "period": snapshot["period"],
            "prev_week": prev["week"] if prev else None,
            "target": "50–60대 여성",
            "sample": False,
        },
        "stats": result["stats"],
        "categories": config.CATEGORY_ORDER,
        "keywords": result["keywords"],
        "rising": result["rising"],
        "rising_by_cat": result["rising_by_cat"],
        "hype": hype,
        "hype_ymd": track2.get("ymd"),
        "insights": insights,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / "latest.json", "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, indent=1)

    # 6) GitHub Pages 는 docs/ 만 서빙하므로 복사본 생성
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DATA / "latest.json", DOCS_DATA / "latest.json")
    print(f"[pipeline] 완료: data/latest.json, docs/data/latest.json ({week})")


if __name__ == "__main__":
    main()

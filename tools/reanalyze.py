# -*- coding: utf-8 -*-
"""재수집 없이, 이미 저장된 히스토리 스냅샷 2개로 분석만 다시 실행해 latest.json 갱신.

analyzer / insight 로직을 고친 뒤 네이버를 다시 긁지 않고 결과만 재생성할 때 사용.
사용법: python tools/reanalyze.py [--insight]
"""
import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config
import analyzer
import insight as insight_mod
from run_pipeline import HISTORY, DATA, DOCS_DATA


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insight", action="store_true", help="Claude API 인사이트도 생성")
    args = ap.parse_args()

    snaps = sorted(HISTORY.glob("*.json"))
    if not snaps:
        print("[reanalyze] 히스토리 스냅샷이 없습니다. run_pipeline.py 를 먼저 실행하세요.")
        return
    with open(snaps[-1], encoding="utf-8") as f:
        current = json.load(f)
    previous = None
    if len(snaps) >= 2:
        with open(snaps[-2], encoding="utf-8") as f:
            previous = json.load(f)

    print(f"[reanalyze] 현재={current['week']} / 전주={previous['week'] if previous else '없음'}")
    result = analyzer.analyze(current, previous)

    if args.insight:
        insights = insight_mod.generate_insights(result["rising"], current.get("products") or None)
    else:
        insights = {"generated": False, "summary": "", "candidates": []}

    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    latest = {
        "meta": {
            "week": current["week"],
            "generated_at": now.isoformat(),
            "period": current["period"],
            "prev_week": previous["week"] if previous else None,
            "target": "50–60대 여성",
            "sample": False,
        },
        "stats": result["stats"],
        "categories": config.CATEGORY_ORDER,
        "keywords": result["keywords"],
        "rising": result["rising"],
        "products": current.get("products") or {},
        "insights": insights,
    }
    with open(DATA / "latest.json", "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, indent=1)
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DATA / "latest.json", DOCS_DATA / "latest.json")
    print(f"[reanalyze] 갱신 완료: stats={result['stats']}, rising={len(result['rising'])}개")


if __name__ == "__main__":
    main()

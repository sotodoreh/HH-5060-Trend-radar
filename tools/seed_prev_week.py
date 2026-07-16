# -*- coding: utf-8 -*-
"""첫 시연용 시드 스크립트 — 전주 스냅샷을 소급 수집한다.

델타/급상승 감지는 전주 스냅샷이 있어야 작동하므로, 최초 구축 시 이 스크립트로
한 주 전 구간을 수집해 history 에 넣어두면 1주차부터 급상승 화면을 보여줄 수 있다.

사용법: python tools/seed_prev_week.py [pages]
        (이후 python run_pipeline.py 를 실행하면 델타가 계산됨)
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config
from collectors import shopping_insight
from run_pipeline import HISTORY, iso_week


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 2

    today = dt.date.today()
    last_sunday = today - dt.timedelta(days=today.weekday() + 1)
    prev_end = last_sunday - dt.timedelta(days=7)      # 한 주 전 일요일
    prev_start = prev_end - dt.timedelta(days=27)
    prev_week = iso_week(today - dt.timedelta(days=7))

    print(f"[seed] 전주 구간 {prev_start} ~ {prev_end} (주차 {prev_week}) / 페이지 {pages}")
    keywords = {}
    for name, info in config.CATEGORIES.items():
        print(f"[seed] {name} 수집 중...")
        keywords[name] = shopping_insight.fetch_category_keywords(
            info["cid"], pages, prev_start.isoformat(), prev_end.isoformat())

    HISTORY.mkdir(parents=True, exist_ok=True)
    snap = {
        "week": prev_week,
        "collected_at": dt.datetime.now().isoformat(),
        "period": f"{prev_start} ~ {prev_end}",
        "keywords": keywords,
        "products": {},
    }
    path = HISTORY / f"{prev_week}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)
    print(f"[seed] 저장 완료: {path} — 이제 run_pipeline.py 를 실행하세요")


if __name__ == "__main__":
    main()

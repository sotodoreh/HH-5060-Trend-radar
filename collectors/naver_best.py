# -*- coding: utf-8 -*-
"""트랙 2 — 네이버쇼핑 베스트 랭킹 수집 (연령 필터).

⚠️ 베스트 페이지는 클라이언트 렌더링이라 requests 단독으로는 상품 목록을 얻기 어렵다.
   (2026-07-16 실측: HTML 200 응답이나 상품 데이터는 스크립트 로드 후 주입)

구현 순서 4단계 과제. 확정 전까지 NAVER_BEST_ENABLED=False 로 두고,
파이프라인은 이 트랙 없이도 정상 동작한다.

엔드포인트 확정 시 진행 방법:
  1. 브라우저 개발자도구(F12) → Network 탭에서 베스트 페이지의 XHR 요청 확인
  2. 연령 필터(50대/60대) 적용 시 호출되는 API URL/파라미터를 config.py 에 기록
  3. 아래 collect_all() 에 파싱 로직 구현
  4. config.NAVER_BEST_ENABLED = True
requests 로 안 되면 Playwright 로 전환 (requirements.txt 주석 참고).
"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config


def collect_all() -> dict:
    """{카테고리명: [{rank, name, price, review_count, url}, ...]}"""
    if not config.NAVER_BEST_ENABLED:
        print("[track2] 비활성화 상태 (config.NAVER_BEST_ENABLED=False) — 건너뜀")
        return {}
    raise NotImplementedError("네이버쇼핑 베스트 엔드포인트 확정 후 구현")


if __name__ == "__main__":
    print(collect_all())

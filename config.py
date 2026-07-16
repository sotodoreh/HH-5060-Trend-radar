# -*- coding: utf-8 -*-
"""5060 트렌드 레이더 — 전역 설정.

스크래핑 포인트(엔드포인트/파라미터/셀렉터)는 사이트 개편 시 이 파일만 고치면 되도록
전부 여기에 모아둔다. (라방바 파이프라인과 동일한 유지보수 전략)
"""

# 사내망 등 TLS 검사 환경에서는 OS 인증서 저장소를 신뢰해야 requests 가 동작한다.
# (truststore 미설치 환경 — 예: 기본 GitHub Actions — 에서도 문제없도록 best-effort)
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# ──────────────────────────────────────────────
# 공통 요청 설정
# ──────────────────────────────────────────────
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
REQUEST_DELAY_SEC = 1.2   # 네이버 차단 방지용 요청 간 딜레이
REQUEST_TIMEOUT = 20

# ──────────────────────────────────────────────
# 트랙 1 — 네이버 데이터랩 쇼핑인사이트 (검증 완료: 2026-07-16)
#   POST https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver
#   form: cid, timeUnit, startDate, endDate, age, gender, count(20), page(1~25)
#   → 페이지당 20개 × 25페이지 = TOP 500
# ──────────────────────────────────────────────
DATALAB_RANK_URL = "https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver"
DATALAB_CATEGORY_URL = "https://datalab.naver.com/shoppingInsight/getCategory.naver"
DATALAB_REFERER = "https://datalab.naver.com/shoppingInsight/sCategory.naver"

TARGET_AGE = "50,60"      # 50대 + 60대
TARGET_GENDER = "f"       # 여성
TIME_UNIT = "week"
TOP_N_PAGES = 25          # 25페이지 = TOP500. 테스트 시 --pages 로 축소 가능

# 8개 대상 카테고리 → 데이터랩 cid 매핑 (2026-07-16 getCategory.naver 로 실측 확인)
# '렌탈상품'은 데이터랩에 직접 카테고리가 없어 파생(derived) 방식:
#   전 카테고리 수집 키워드에서 렌탈/렌트/구독 패턴을 필터링해 구성한다.
CATEGORIES = {
    "일반식품":  {"cid": 50000006},   # 식품 (L1)
    "건강식품":  {"cid": 50000023},   # 식품 > 건강식품
    "뷰티":      {"cid": 50000002},   # 화장품/미용 (L1)
    "가전":      {"cid": 50000003},   # 디지털/가전 (L1)
    "생활용품":  {"cid": 50000078},   # 생활/건강 > 생활용품
    "주방용품":  {"cid": 50000061},   # 생활/건강 > 주방용품
    "여행":      {"cid": 50007256},   # 여가/생활편의 > 해외여행 (국내여행/체험: 50007252)
    # "렌탈상품"은 아래 DERIVED_CATEGORIES 로 처리
}

DERIVED_CATEGORIES = {
    "렌탈상품": {"pattern": r"렌탈|렌털|렌트|구독"},
}

# 대시보드 표기 순서 (파생 카테고리 포함)
CATEGORY_ORDER = ["일반식품", "건강식품", "뷰티", "가전", "생활용품", "주방용품", "여행", "렌탈상품"]

# ──────────────────────────────────────────────
# 트랙 2 — 네이버쇼핑 베스트 (⚠️ 미검증 — 클라이언트 렌더링 페이지)
#   1차 버전은 실패해도 파이프라인이 죽지 않도록 graceful skip.
#   엔드포인트 확정 후 아래 값만 갱신하면 된다. (구현 순서 4단계)
# ──────────────────────────────────────────────
NAVER_BEST_URL = "https://search.shopping.naver.com/best/home"
NAVER_BEST_ENABLED = False   # 엔드포인트 확정 후 True 로 전환

# ──────────────────────────────────────────────
# Hmall 보유 여부 체크 (⚠️ 미검증 — SPA, 검색 API 확인 필요)
#   러프 판정: 검색 결과 존재 여부 + 방송상품(라이브/데이터방송) 필터 기준
# ──────────────────────────────────────────────
HMALL_SEARCH_URL = "https://www.hyundaihmall.com/front/spa/search"
HMALL_ENABLED = False        # 검색 API 확정 후 True 로 전환

# ──────────────────────────────────────────────
# Claude API
# ──────────────────────────────────────────────
INSIGHT_MODEL = "claude-opus-4-8"    # 인사이트 생성
EXTRACT_MODEL = "claude-opus-4-8"    # Hmall 검색용 핵심 키워드 추출 (비용 절감 시 "claude-haiku-4-5")

# ──────────────────────────────────────────────
# 분석 파라미터
# ──────────────────────────────────────────────
RISING_MIN_DELTA = 30     # 순위가 이만큼 이상 상승하면 '급상승'
RISING_TOP_LIMIT = 40     # 대시보드에 노출할 급상승/신규 키워드 최대 개수 (전 카테고리 합산)
KEYWORDS_PER_CATEGORY = 100  # latest.json 에 카테고리별로 담을 키워드 수 (수집은 TOP500, 노출은 상위 N)

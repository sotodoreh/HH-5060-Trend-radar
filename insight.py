# -*- coding: utf-8 -*-
"""Claude API 인사이트 생성.

입력: 트랙1 급상승 관심사 (+ 트랙2 hype 상품, Hmall 보유 여부 — 활성화 시)
출력: 방송상품화 후보 3~5개 + 근거 (JSON 구조화 출력)

핵심 로직: 관심사 급상승 × 관련 상품 hype × 당사 방송 미보유 교차점 = 최상위 소싱 후보
"""
import json
import os

import config

# 인사이트 텍스트는 회의자료 인용 가능성이 있어 사내 문서 스타일을 강제한다.
STYLE_GUIDE = """
[문서 스타일 — 반드시 준수]
- 헤드라인 : 설명 구조. 항목당 2줄 이내.
- 병렬 나열은 `/`, 인과는 `→`, 감소는 `▲`, 상품·프로그램명은 낫표 「 」.
- 기피 표현: ~을 통한, ~하는, 레버, 구좌, 프리미엄화
- 선호 표현: 유인책, 시간대, 편성 인프라, 간결한 인과
- 용어: 정액비=광고비(업체 지불), 취급고=GMV, 순주문=취소·반품 제외
"""

SYSTEM = f"""너는 홈쇼핑(현대홈쇼핑) 상품기획·편성 전략 분석가다.
50~60대 여성 고객의 네이버 쇼핑 검색 트렌드 데이터를 보고,
방송상품화(라이브·데이터방송) 후보와 그 근거를 도출한다.

판단 기준:
1) 관심사 급상승 폭과 지속 가능성 (일시적 이슈 vs 구조적 트렌드)
2) 홈쇼핑 채널 적합성 (시연 가능성 / 객단가 / 5060 여성 소구력)
3) Hmall·방송 보유 여부 데이터가 있으면 '미보유 갭'을 최우선 가점

{STYLE_GUIDE}
"""

INSIGHT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "이번 주 5060 여성 트렌드 총평. 헤드라인 : 설명 구조, 3~4문장.",
        },
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "방송상품화 후보 (상품/카테고리명)"},
                    "category": {"type": "string"},
                    "reason": {"type": "string", "description": "근거. 헤드라인 : 설명, 2줄 이내"},
                    "hmall_status": {
                        "type": "string",
                        "enum": ["방송상품 미보유", "유사상품 보유", "편성 이력 有", "미확인"],
                    },
                    "score": {"type": "integer", "description": "우선순위 1(최상)~5"},
                },
                "required": ["name", "category", "reason", "hmall_status", "score"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "candidates"],
    "additionalProperties": False,
}


def _hype_digest(hype: dict) -> list[dict]:
    """인사이트 프롬프트에 넣을 hype 요약 (키워드 + 대표상품 리뷰수)."""
    digest = []
    for label, items in (hype or {}).items():
        for it in items[:8]:
            p = (it.get("products") or [{}])[0]
            digest.append({
                "관점": label, "키워드": it.get("keyword"), "카테고리": it.get("category"),
                "순위변동": it.get("rank_fluctuation"),
                "대표상품": p.get("title"), "리뷰수": p.get("review_count"), "가격": p.get("price"),
            })
    return digest


def generate_insights(rising: list[dict], hype: dict | None = None,
                      hmall: dict | None = None) -> dict:
    """{'generated': bool, 'summary': str, 'candidates': [...]}"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[insight] ANTHROPIC_API_KEY 미설정 — 인사이트 생성 건너뜀")
        return {"generated": False, "summary": "", "candidates": []}

    payload = {"급상승_및_신규진입_검색키워드": rising}
    if hype:
        payload["실구매_hype_상품"] = _hype_digest(hype)
    if hmall:
        payload["hmall_보유여부"] = hmall

    user_msg = (
        "아래는 이번 주 50~60대 여성 네이버쇼핑 트렌드 데이터다.\n"
        "- 급상승_및_신규진입_검색키워드: 데이터랩 검색 관심사. delta=전주 대비 순위 상승 폭, is_new=TOP500 신규 진입.\n"
        "- 실구매_hype_상품: 실제 구매 급상승 키워드와 대표상품(리뷰수=판매 신호).\n"
        "검색 관심사 급상승 × 실구매 hype 가 겹치는 지점을 특히 주목하라.\n"
        "방송상품화 후보 3~5개를 근거와 함께 도출하라.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    # 인사이트 생성 실패(키 오류·크레딧 부족·모델 접근·응답 파싱 등)가
    # 파이프라인 전체를 죽이지 않도록 방어. 실패해도 데이터/대시보드는 발행된다.
    try:
        import anthropic
        # Secrets 붙여넣기 시 키 끝에 줄바꿈/공백이 섞이면 HTTP 헤더가 깨져
        # 'Connection error' 로 위장된 실패가 난다 → 앞뒤 공백 제거 후 사용
        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"].strip()
        )
        resp = client.messages.create(
            model=config.INSIGHT_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": INSIGHT_SCHEMA}},
            messages=[{"role": "user", "content": user_msg}],
        )
        if resp.stop_reason == "refusal":
            print("[insight] 요청 거부됨 — 인사이트 없이 진행")
            return {"generated": False, "summary": "", "candidates": []}
        text = next((b.text for b in resp.content if b.type == "text"), None)
        if not text:
            print(f"[insight] 텍스트 블록 없음 (stop_reason={resp.stop_reason}) — 인사이트 없이 진행")
            return {"generated": False, "summary": "", "candidates": []}
        data = json.loads(text)
        return {"generated": True, **data}
    except Exception as e:
        # 대표 원인: 크레딧 부족/결제 미완(402), 잘못된 키(401), 모델 접근 불가(403/404),
        # Secret에 섞인 공백/줄바꿈(헤더 오류가 Connection error 로 표시됨)
        msg = f"{type(e).__name__}: {e}"
        cause = getattr(e, "__cause__", None)
        while cause is not None:  # 겉포장이 아니라 진짜 원인을 로그에 남긴다
            msg += f"\n[insight]   └ 원인: {type(cause).__name__}: {cause}"
            cause = getattr(cause, "__cause__", None)
        print(f"[insight] ⚠️ 생성 실패 — 데이터는 정상 발행, 인사이트만 건너뜀: {msg}")
        return {"generated": False, "summary": "", "candidates": []}


if __name__ == "__main__":
    sample = [
        {"category": "건강식품", "keyword": "저속노화", "rank": 12, "prev_rank": 180, "delta": 168, "is_new": False},
        {"category": "가전", "keyword": "제습기", "rank": 3, "prev_rank": 95, "delta": 92, "is_new": False},
    ]
    print(json.dumps(generate_insights(sample), ensure_ascii=False, indent=2))

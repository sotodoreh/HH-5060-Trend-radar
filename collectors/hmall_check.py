# -*- coding: utf-8 -*-
"""Hmall 보유 여부 체크.

트랙 2 급등 상품의 핵심 키워드를 Hmall 검색에 투입해
① 검색 결과 존재 여부 ② 방송상품(라이브/데이터방송) 여부를 러프하게 판정한다.

⚠️ Hmall은 SPA 라서 검색 결과 API 확인이 필요 (2026-07-16 실측: 셸 HTML만 응답).
   구현 순서 5단계 과제. 확정 전까지 HMALL_ENABLED=False.

전처리: 상품명 그대로 검색하면 매칭 실패 → Claude API로
"브랜드 + 제형/유형 핵심어"를 추출한 뒤 검색한다.
"""
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
import config


def extract_search_keyword(product_name: str) -> str:
    """Claude API로 상품명에서 검색용 핵심 키워드(브랜드+제형/유형) 추출."""
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=config.EXTRACT_MODEL,
        max_tokens=256,
        system=(
            "쇼핑몰 상품명에서 검색용 핵심 키워드를 추출한다. "
            "브랜드명 + 제형/유형 핵심어만 남기고 용량·수량·프로모션 문구는 제거. "
            "결과는 키워드 문자열 하나만 출력."
        ),
        messages=[{"role": "user", "content": product_name}],
    )
    return next(b.text for b in resp.content if b.type == "text").strip()


def check_product(product_name: str) -> dict:
    """{'checked': bool, 'found': bool, 'broadcast': bool, 'keyword': str}"""
    if not config.HMALL_ENABLED:
        return {"checked": False, "found": False, "broadcast": False, "keyword": ""}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[hmall] ANTHROPIC_API_KEY 미설정 — 키워드 추출 불가, 건너뜀")
        return {"checked": False, "found": False, "broadcast": False, "keyword": ""}
    keyword = extract_search_keyword(product_name)
    # TODO(구현 순서 5): Hmall 검색 API 확정 후 실제 조회 구현
    #   판정 기준: 첫 1~2페이지 노출 여부 / 방송상품 필터 결과 존재 여부
    raise NotImplementedError("Hmall 검색 API 확정 후 구현")


if __name__ == "__main__":
    print(check_product("종근당건강 락토핏 골드 2g x 50포 x 3통"))

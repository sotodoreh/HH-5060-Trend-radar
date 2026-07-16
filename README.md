# 5060 트렌드 레이더

홈쇼핑 핵심 고객층인 **50–60대 여성**의 쇼핑 관심사·구매 트렌드를 매주 자동 수집하고,
상품 소싱·방송 편성·마케팅에 활용할 인사이트를 도출하는 웹 대시보드.

> 사업부 AI/LLM 스터디 과제. 매주 월요일 아침 GitHub Actions 가 자동 수집 →
> GitHub Pages 대시보드가 갱신됩니다.

## 구조 (투트랙)

| 트랙 | 소스 | 내용 | 상태 |
|---|---|---|---|
| 1. 관심사 레이더 | 네이버 데이터랩 쇼핑인사이트 | 카테고리별 인기검색어 TOP500 (5060 여성 필터) → 전주 대비 급상승/신규 진입 감지 | ✅ 작동 |
| 2. Hype 상품 레이더 | 네이버쇼핑 베스트 | 순위 급등 상품 + 리뷰수 급증 감지 | 🚧 준비 중 |
| + Hmall 체크 | hyundaihmall.com | 급등 상품의 자사몰/방송상품 보유 여부 | 🚧 준비 중 |
| + AI 인사이트 | Claude API | 방송상품화 후보 3~5개 + 근거 | ✅ 작동 (API 키 필요) |

대상 카테고리(8개): 일반식품 / 건강식품 / 뷰티 / 가전 / 생활용품 / 주방용품 / 여행 / 렌탈상품
(렌탈상품은 데이터랩에 직접 카테고리가 없어 전 카테고리 키워드에서 렌탈·구독 패턴을 필터링하는 파생 방식)

## 파일 구성

```
trend-radar/
├── collectors/
│   ├── shopping_insight.py    # 트랙1 (데이터랩 내부 API — 검증 완료)
│   ├── naver_best.py          # 트랙2 (엔드포인트 확정 후 활성화)
│   └── hmall_check.py         # Hmall 보유 여부 (동일)
├── analyzer.py                # 델타 계산, 급상승/신규 감지, 렌탈 파생
├── insight.py                 # Claude API 인사이트 (JSON 구조화 출력)
├── run_pipeline.py            # 오케스트레이터
├── config.py                  # 카테고리 cid, 엔드포인트, 파라미터 (전부 여기)
├── data/
│   ├── latest.json            # 최신 결과
│   └── history/YYYY-WW.json   # 주차별 스냅샷 (델타 계산용)
├── docs/                      # GitHub Pages (index.html + data/latest.json 복사본)
└── .github/workflows/weekly.yml
```

## 로컬 실행

```bash
pip install -r requirements.txt

# 테스트 (카테고리당 TOP40, Claude 호출 없이)
python run_pipeline.py --pages 2 --skip-insight

# 정식 실행 (TOP500 + AI 인사이트)
set ANTHROPIC_API_KEY=sk-ant-...   # (macOS/Linux: export ...)
python run_pipeline.py
```

대시보드 확인: `python -m http.server 8000 -d docs` → http://localhost:8000

## 배포

GitHub 업로드 → Pages → Actions 설정 절차는 **[DEPLOY.md](DEPLOY.md)** 에 단계별로 정리.

## 운영 유의사항 (리스크)

1. **스크래핑 포인트 3곳** (쇼핑인사이트 / 쇼핑베스트 / Hmall) — 사이트 개편 시 `config.py` 만 수정하면 되도록 분리해둠
2. **네이버 차단 가능성** — 주 1회 실행 + 요청 딜레이 + UA 설정. GitHub Actions IP가 차단되면 로컬 실행 후 push 로 대체 가능 (`run_pipeline.py` → `git push`)
3. **Hmall 은 자사몰이지만 사내 정책 확인 권장**
4. **리뷰수 델타는 2주차부터** — 첫 시연은 순위 변동 위주
5. Secrets: `ANTHROPIC_API_KEY` (필수), 네이버 공식 API 키·텔레그램은 확장 시

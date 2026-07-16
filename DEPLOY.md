# 배포 가이드 — GitHub 처음이어도 따라오면 됩니다

목표: 이 폴더를 GitHub 에 올리고 → 무료 웹주소(GitHub Pages)로 대시보드를 공개하고 →
매주 월요일 아침 자동 수집(GitHub Actions)까지 켜는 것.

> 💡 지름길: Claude Code 에게 **"trend-radar 깃허브에 올려줘. 저장소 이름은 trend-radar"** 라고
> 시키면 2~3단계 명령어를 대신 실행해 줍니다. 아래는 직접 할 때의 절차입니다.

---

## 0단계. 준비물 확인

- GitHub 계정 (이미 있음 ✅)
- Git 프로그램: 터미널(PowerShell)에서 아래 입력
  ```
  git --version
  ```
  버전이 나오면 OK. `인식할 수 없는...` 이라고 나오면 https://git-scm.com/download/win 에서
  설치 (전부 기본값으로 Next만 눌러도 됨) 후 터미널을 새로 열기.

## 1단계. GitHub 에서 빈 저장소 만들기 (웹브라우저)

1. https://github.com 로그인 → 우측 상단 **`+`** 버튼 → **New repository**
2. 입력값:
   - **Repository name**: `trend-radar`
   - **Public** 선택 ← 중요! (무료 Pages 는 Public 저장소만 가능)
   - ⚠️ "Add a README file" 등 체크박스는 **모두 체크하지 않음** (빈 저장소여야 함)
3. **Create repository** 클릭
4. 생성 직후 나오는 페이지에서 `https://github.com/내아이디/trend-radar.git` 주소 확인

## 2단계. 이 폴더를 GitHub 로 올리기 (터미널)

PowerShell 을 열고 아래를 **한 줄씩** 입력. (`내아이디` 부분만 본인 GitHub 아이디로 교체)

```
cd C:\Users\Hhome\Desktop\Claude\trend-radar
git init
git add .
git commit -m "5060 트렌드 레이더 초기 버전"
git branch -M main
git remote add origin https://github.com/내아이디/trend-radar.git
git push -u origin main
```

- 처음 `git commit` 할 때 "이름/이메일을 설정하라"고 나오면:
  ```
  git config --global user.name "본인이름"
  git config --global user.email "GitHub가입이메일"
  ```
  입력 후 commit 부터 다시.
- 처음 `git push` 할 때 **브라우저 로그인 창**이 뜹니다 → GitHub 로그인 →
  Authorize 클릭. (Windows 의 Git Credential Manager 가 자동으로 기억해서 다음부턴 안 물어봄)

성공하면 브라우저에서 `github.com/내아이디/trend-radar` 새로고침 → 파일들이 보임.

## 3단계. GitHub Pages 켜기 (대시보드 웹 공개)

1. 저장소 페이지에서 **Settings** 탭 → 왼쪽 메뉴 **Pages**
2. **Build and deployment** 항목:
   - Source: `Deploy from a branch`
   - Branch: `main` 선택, 폴더는 **`/docs`** 선택 ← 중요!
   - **Save**
3. 1~2분 뒤 같은 페이지 상단에 주소가 나타남:
   ```
   https://내아이디.github.io/trend-radar/
   ```
   이 주소가 **시연용 대시보드 주소**입니다. PC/모바일 모두 열림.

## 4단계. Claude API 키 등록 (AI 인사이트용)

1. 저장소 **Settings** → 왼쪽 **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
   - Name: `ANTHROPIC_API_KEY`
   - Secret: 발급받은 키 (`sk-ant-...`) 붙여넣기
3. **Add secret**

> 키 발급: https://console.anthropic.com → API Keys. 키가 아직 없어도 대시보드와
> 수집은 정상 작동하고, AI 인사이트 박스만 "설정 후 생성" 으로 표시됩니다.

## 5단계. 자동 수집 테스트 (수동 실행)

매주 월요일 09:00(KST)에 자동 실행되지만, 지금 바로 테스트할 수 있습니다:

1. 저장소 **Actions** 탭 → 왼쪽 **weekly-trend-radar** 클릭
2. 오른쪽 **Run workflow** 버튼 → 초록색 **Run workflow**
3. 2~5분 뒤 초록 체크 ✅ 가 뜨면 성공 → 잠시 후 대시보드 새로고침하면 최신 데이터 반영

## 끝! 매주 흐름

```
월요일 09:00  GitHub Actions 자동 실행
  → 네이버 데이터랩 수집 (8개 카테고리 × 5060 여성 TOP500)
  → 전주 대비 급상승/신규 진입 계산
  → Claude 가 방송상품화 후보 도출
  → 데이터 커밋 → 대시보드 자동 갱신
스터디 공유: https://내아이디.github.io/trend-radar/ 링크만 던지면 됨
```

---

## 문제 해결

| 증상 | 해결 |
|---|---|
| Pages 주소가 404 | Settings→Pages 에서 폴더가 `/docs` 인지 확인. 켠 직후엔 1~2분 대기 |
| Actions 가 push 단계에서 실패 (403) | Settings→Actions→General→Workflow permissions 를 **Read and write permissions** 로 변경 |
| Actions 수집 단계 실패 (네이버 차단 의심) | GitHub 서버 IP가 차단됐을 수 있음 → 로컬 PC에서 `python run_pipeline.py` 실행 후 `git add data docs/data` → `git commit -m "weekly data"` → `git push` 로 대체 |
| 대시보드에 옛날 데이터 | 강력 새로고침 (Ctrl+F5) |
| git push 에서 인증 오류 반복 | `git credential-manager github login` 실행 후 재시도 |

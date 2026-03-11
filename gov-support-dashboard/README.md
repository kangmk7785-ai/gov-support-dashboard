# 🏛 2026 정부 지원금 통합 안내 대시보드

정부·지자체·공공기관 지원사업 정보를 **매일 자동으로 수집**하여 웹 대시보드에 표시하는 시스템입니다.

> 기업마당 API + 보조금24 API → 매일 새벽 6시 자동 수집 → GitHub Pages로 무료 호스팅

---

## 🚀 설치 방법 (10분이면 완료!)

### 1단계: 이 저장소를 내 GitHub에 복사

1. GitHub에 로그인합니다
2. 우측 상단의 **+** 버튼 → **New repository** 클릭
3. Repository name: `gov-support-dashboard`
4. **Public** 선택 (GitHub Pages 무료 사용을 위해)
5. **Create repository** 클릭

생성된 저장소에 이 폴더의 모든 파일을 업로드합니다:
- `index.html`
- `data.json`
- `scripts/fetch_data.py`
- `.github/workflows/daily-update.yml`
- `README.md`

> 💡 **가장 쉬운 방법**: GitHub 웹에서 "Upload files" 버튼으로 폴더째 드래그&드롭

---

### 2단계: API 키 발급 (무료)

#### ① 기업마당 API 키
1. [기업마당](https://www.bizinfo.go.kr) 접속 → 회원가입
2. 마이페이지 → API 신청 또는 [공공데이터포털](https://www.data.go.kr)에서 "기업마당" 검색
3. 활용 신청 후 API 키 복사

#### ② 공공데이터포털 API 키
1. [공공데이터포털](https://www.data.go.kr) 접속 → 회원가입/로그인
2. "보조금24 공공서비스" 검색 → 활용 신청
3. 마이페이지에서 API 키 복사

> 두 개 다 무료이며, 보통 즉시~1일 이내 승인됩니다.

---

### 3단계: GitHub에 API 키 등록

1. 내 저장소 페이지에서 **Settings** 탭 클릭
2. 왼쪽 메뉴에서 **Secrets and variables** → **Actions** 클릭
3. **New repository secret** 버튼으로 아래 2개를 각각 등록:

| Name | Value |
|------|-------|
| `BIZINFO_API_KEY` | 기업마당에서 발급받은 API 키 |
| `DATA_GO_KR_API_KEY` | 공공데이터포털에서 발급받은 API 키 |

> ⚠️ API 키는 절대 코드에 직접 넣지 마세요! Secrets에만 등록합니다.

---

### 4단계: GitHub Pages 활성화

1. 저장소 **Settings** → 왼쪽 메뉴 **Pages**
2. **Source**를 **GitHub Actions**로 선택
3. 저장

---

### 5단계: 첫 실행 (수동)

1. 저장소에서 **Actions** 탭 클릭
2. 왼쪽에 **📡 정부 지원금 매일 자동 업데이트** 클릭
3. **Run workflow** → **Run workflow** 버튼 클릭
4. 1~2분 후 실행 완료!

완료되면 아래 주소에서 대시보드를 볼 수 있습니다:
```
https://[내GitHub아이디].github.io/gov-support-dashboard/
```

---

## 📅 이후에는?

**아무것도 안 해도 됩니다!** 매일 한국시간 오전 6시에 자동으로:

1. 기업마당 + 보조금24 API에서 최신 데이터 수집
2. 기존 데이터와 병합 (중복 제거)
3. 대시보드 HTML 자동 생성
4. GitHub Pages에 자동 배포

---

## 📁 파일 구조

```
gov-support-dashboard/
├── index.html                          ← 대시보드 웹페이지 (자동 생성)
├── data.json                           ← 수집된 지원사업 데이터 (자동 갱신)
├── scripts/
│   └── fetch_data.py                   ← API 데이터 수집 스크립트
├── .github/
│   └── workflows/
│       └── daily-update.yml            ← 매일 자동 실행 설정
└── README.md                           ← 이 파일
```

---

## ❓ 자주 묻는 질문

**Q: 비용이 드나요?**
A: 전부 무료입니다. GitHub Actions 무료 사용량(월 2,000분)이면 충분합니다.

**Q: 코딩을 몰라도 되나요?**
A: 네! 위 5단계만 따라하시면 됩니다. 코드 수정이 필요 없습니다.

**Q: API 키 승인이 안 돼요**
A: 공공데이터포털은 보통 즉시 승인됩니다. 기업마당은 1~2일 걸릴 수 있습니다. 하나만 있어도 작동합니다.

**Q: 데이터가 정확한가요?**
A: 정부 공식 API에서 가져오는 데이터이므로 신뢰할 수 있습니다. 단, 세부 신청요건은 반드시 공식 홈페이지에서 확인하세요.

**Q: 다른 API도 추가할 수 있나요?**
A: `scripts/fetch_data.py`에 새로운 API 함수를 추가하면 됩니다.

---

## 📡 사용하는 공공 API

| API | 제공기관 | 데이터 내용 |
|-----|---------|------------|
| 기업마당 API | 중소벤처기업부 | 중소기업·소상공인 지원사업 공고 |
| 보조금24 API | 행정안전부 | 정부 보조금·복지 서비스 목록 |

---

*이 프로젝트는 공공데이터를 활용하여 제작되었습니다.*

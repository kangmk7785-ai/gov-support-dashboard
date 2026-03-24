# 🏛 2026 정부 지원금 통합 안내 대시보드

정부·지자체·공공기관 지원사업 정보를 **매일 자동으로 수집**하여 웹 대시보드로 공개하는 시스템입니다.

> **Netlify (무료 웹호스팅) + GitHub Actions (매일 자동 수집)**

---

## ✅ 완성되면 이렇게 됩니다

- 🌐 `https://내사이트.netlify.app` 주소로 **누구나** 접속 가능
- 📡 매일 새벽 6시에 **자동으로** 최신 지원사업 수집
- 🔄 수집된 데이터가 자동으로 웹사이트에 반영
- 💰 완전 **무료** (서버비 0원)

---

## 🚀 설치 가이드 (총 4단계, 약 15분)

---

### ✋ 사전 준비

- **GitHub 계정** → [github.com](https://github.com)에서 무료 가입
- **Netlify 계정** → [netlify.com](https://www.netlify.com)에서 무료 가입 (GitHub 계정으로 로그인 가능)

---

### 📌 1단계: GitHub에 저장소 만들기 (3분)

1. [github.com](https://github.com) 로그인
2. 우측 상단 **+** 버튼 → **New repository**
3. 설정:
   - Repository name: **`gov-support-dashboard`**
   - ✅ **Public** 선택
   - ✅ **Add a README file** 체크
4. **Create repository** 클릭
5. 생성된 저장소에서 **Add file** → **Upload files**
6. 이 ZIP의 **모든 파일**을 드래그&드롭으로 업로드
   - `index.html`
   - `data.json`
   - `netlify.toml`
   - `requirements.txt`
   - `runtime.txt`
   - `scripts/` 폴더 (안에 `fetch_data.py`)
   - `.github/` 폴더 (안에 `workflows/daily-update.yml`)
7. **Commit changes** 클릭

> 💡 `.github` 폴더가 안 보이면: 파일을 하나씩 만들어도 됩니다.
> GitHub에서 **Add file → Create new file** → 파일명에 `.github/workflows/daily-update.yml` 입력 후 내용 붙여넣기

---

### 📌 2단계: API 키 발급 & GitHub에 등록 (5분)

#### API 키 발급

1. [공공데이터포털](https://www.data.go.kr) 접속 → 회원가입/로그인
2. 검색창에 **"기업마당"** 검색 → **중소기업 지원사업 공고 조회** 활용 신청
3. 검색창에 **"보조금24"** 또는 **"공공서비스"** 검색 → 활용 신청
4. **마이페이지** → 발급된 API 키 2개 복사
5. [온통청년](https://www.youthcenter.go.kr) 가입 → 마이페이지 → OPEN API → 인증키 발급 신청

> 공공데이터포털은 보통 즉시 승인. 온통청년은 담당자 승인 필요(1~3일). API 키 없이도 기존 데이터로 사이트는 작동합니다.

#### GitHub Secrets에 등록

1. GitHub 저장소 → **Settings** 탭
2. 왼쪽 메뉴: **Secrets and variables** → **Actions**
3. **New repository secret** 클릭 후 아래 3개 등록:

| Name (정확히 입력) | Value | 용도 |
|---|---|---|
| `BIZINFO_API_KEY` | 기업마당 API 키 | 소상공인·창업·기술 + 지자체 |
| `DATA_GO_KR_API_KEY` | 공공데이터포털 API 키 | 보조금24 + HRD-Net 훈련 |
| `YOUTH_API_KEY` | 온통청년 인증키 | 청년 정책 전체 |

---

### 📌 3단계: Netlify에 연결 (3분) ⭐ 핵심!

1. [app.netlify.com](https://app.netlify.com) 접속 → GitHub 계정으로 로그인
2. **Add new site** → **Import an existing project**
3. **GitHub** 선택 → 권한 허용
4. 방금 만든 **`gov-support-dashboard`** 저장소 선택
5. 설정 화면:
   - Branch to deploy: **`main`**
   - Build command: **비워두기** (빈칸)
   - Publish directory: **`.`** (점 하나)
6. **Deploy site** 클릭!

> 🎉 약 30초 후 배포 완료!
> `https://랜덤이름.netlify.app` 주소가 생성됩니다.

#### 사이트 이름 변경 (선택)
- Netlify 대시보드 → **Domain management** → **Options** → **Edit site name**
- 예: `gov-support-2026` → `https://gov-support-2026.netlify.app`

---

### 📌 4단계: 자동 업데이트 확인 (2분)

1. GitHub 저장소 → **Actions** 탭
2. **📡 매일 자동 업데이트 → Netlify 배포** 클릭
3. **Run workflow** → **Run workflow** 클릭
4. 1~2분 후 초록색 ✅ 표시되면 성공!
5. Netlify가 자동으로 변경을 감지하고 재배포합니다

> 이후 매일 새벽 6시에 자동 실행됩니다. 끝!

---

## 🔄 작동 원리

```
매일 새벽 6시
    │
    ▼
GitHub Actions 실행
    │
    ├─ 기업마당 API 호출 → 최신 지원사업 수집
    ├─ 보조금24 API 호출 → 복지/보조금 수집
    ├─ 데이터 병합 & 중복 제거
    ├─ data.json 업데이트
    └─ index.html 자동 생성
    │
    ▼
GitHub에 자동 커밋 & 푸시
    │
    ▼
Netlify가 변경 감지 → 자동 재배포
    │
    ▼
🌐 웹사이트 자동 갱신 완료!
```

---

## 💡 선택사항: Netlify Build Hook 설정

더 확실한 자동 배포를 원하면:

1. Netlify 대시보드 → **Site configuration** → **Build & deploy** → **Build hooks**
2. **Add build hook** → 이름: `github-auto-update` → **Save**
3. 생성된 URL 복사
4. GitHub 저장소 → **Settings** → **Secrets** → **New repository secret**:

| Name | Value |
|---|---|
| `NETLIFY_BUILD_HOOK` | Netlify에서 복사한 URL |

> 이렇게 하면 GitHub Actions가 데이터 수집 후 Netlify에 직접 "재배포해!"라고 알려줍니다.

---

## 📁 파일 구조

```
gov-support-dashboard/
├── index.html              ← 대시보드 (자동 생성)
├── data.json               ← 지원사업 데이터 (자동 갱신)
├── netlify.toml            ← Netlify 설정
├── requirements.txt        ← Python 패키지 목록
├── runtime.txt             ← Python 버전
├── scripts/
│   └── fetch_data.py       ← API 데이터 수집 스크립트
├── .github/
│   └── workflows/
│       └── daily-update.yml ← 매일 자동 실행 설정
└── README.md
```

---

## ❓ FAQ

**Q: 완전 무료인가요?**
→ 네. GitHub Actions(월 2,000분 무료) + Netlify(월 100GB 무료) 모두 무료입니다.

**Q: API 키 없어도 작동하나요?**
→ 네. API 키 없으면 기존 data.json의 22건 데이터로 사이트가 표시됩니다. 자동 수집만 안 될 뿐입니다.

**Q: 사이트 주소를 내 도메인으로 바꿀 수 있나요?**
→ Netlify → Domain management에서 커스텀 도메인 연결이 가능합니다. (도메인 구매는 별도)

**Q: 데이터가 안 나와요**
→ GitHub → Actions 탭에서 최근 실행 로그를 확인하세요. API 키 오류인 경우가 대부분입니다.

---

*공공데이터를 활용하여 제작되었습니다.*

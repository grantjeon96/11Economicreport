# 📈 일일 경제 지표 모니터링 및 메일 전송 시스템 - 에이전트 작업 요약 가이드 (Agent Summary)

이 문서는 에이전트가 세션 중단 후 작업을 재개하거나, 시스템의 구조와 현재 진행 상황을 즉시 파악하고 대응할 수 있도록 돕는 요약 가이드입니다. 

---

## 📌 1. 프로젝트 개요 & 아키텍처

본 프로젝트는 거시 경제 지표, 주요 주식, ETF, 환율, 원자재, 암호화폐 등 총 **19개 지표**의 데이터를 실시간 수집 및 가공하고, 이를 세련된 Glassmorphism 다크 테마 웹 대시보드로 시각화하며, 매일 아침 분석 요약 차트와 AI 경제 브리핑이 포함된 HTML 보고서를 이메일로 자동 전송하고, 로컬 스피커로 TTS 음성 브리핑 알람을 재생하는 통합 시스템입니다.

### 데이터 & 서비스 흐름
```
[yfinance API]
      │
      ▼ (Period: 1 Year)
[backend/collector.py] ─── 결측치 처리 (ffill/bfill) & 전일대비 변동량 계산
      │
      ├───────────────────────┬───────────────────────────────┐
      ▼ (JSON 저장)            ▼ (Matplotlib 요약 차트 생성)   ▼ (AI 뉴스 대본 생성)
[backend/data/metrics.json]  [backend/data/report_chart.png]  [backend/alarm.py]
      │                        │                               │
      ├────────────────┐       │ (MIME Inline Attachment)      ▼ (Beep 멜로디 및 TTS 재생)
      ▼ (API 서빙)      │       ▼                            [로컬 오디오 (스피커)]
[backend/main.py]      │     [backend/notifier.py]
 (FastAPI)             │       │
      │                │       ▼ (SMTP 전송)
      ▼                └───────► [수신자 이메일 (HTML Report)]
[frontend] (React + Vite + Chart.js)
```

---

## 📂 2. 디렉토리 구조 및 핵심 파일 역할

- `c:\Users\전민정\.gemini\11.경제지표모으기`
  - 📂 **`backend/`**: 데이터 수집, 이메일 알림 전송, 음성 알람 및 API 제공
    - 📄 **`main.py`**: FastAPI 기반 API 서버. 데이터 수집, 메일 발송, TTS 알람 스크립트에 대한 수동 트리거 및 백그라운드 태스크 연동.
    - 📄 **`collector.py`**: `yfinance`를 활용해 19개 지표의 최신 데이터를 수집 및 가공하여 `data/metrics.json`으로 저장.
    - 📄 **`notifier.py`**: 수집된 데이터를 바탕으로 Matplotlib 다중 서브플롯(2중 축, 상대 지수 변환 등) 요약 이미지(`report_chart.png`)를 생성하고, `alarm.py`에서 생성한 AI 브리핑 대본을 포함한 HTML 템플릿과 결합해 이메일을 전송.
    - 📄 **`alarm.py`**: 수집된 데이터를 요약하여 Gemini API(또는 로컬 백업 템플릿)로 경제 앵커 톤앤매너의 아침 브리핑 대본을 생성하고, winsound 기반 도미솔도 알람 멜로디 재생 후 PowerShell SpeechSynthesizer를 통해 로컬 스피커로 TTS 한국어 음성 낭독을 수행.
    - 📄 **`.env`**: SMTP 설정, API 서버 호스트/포트, 그리고 Gemini API 호출용 `GEMINI_API_KEY` 설정.
    - 📂 **`data/`**: 수집된 `metrics.json`과 생성된 `report_chart.png` 임시 저장 공간.
  - 📂 **`frontend/`**: React, Vite, Vanilla CSS 기반 프론트엔드 대시보드
    - 📄 **`package.json`**: React, Vite, Chart.js 등 라이브러리 종속성.
    - 📂 **`src/`**: Glassmorphism 디자인의 대시보드 UI를 그리는 React 컴포넌트 및 CSS.
      - `App.jsx` 내 상단 헤더에 "지금 갱신", "브리핑 알람 듣기", "보고서 메일 전송" 등의 제어 기능 통합.
  - 📄 **`run_daily.bat`**: Windows 작업 스케줄러 등록용 배치 파일. 가상환경(`.venv2`)을 활성화하고 수집(`collector.py`), 알림(`notifier.py`), 알람 및 TTS(`alarm.py`)를 연속 실행함.
  - 📄 **`register_scheduler.bat`**: Windows 작업 스케줄러에 `run_daily.bat`을 자동으로 등록해 주는 원클릭 등록 스크립트.
  - 📄 **`README.md`**: 사용자를 위한 시스템 전체 실행법 및 이메일 설정 가이드.

---

## ⚙️ 3. 환경 변수 및 설정 상태 (`backend/.env`)

이메일 보고서 발송 및 AI 브리핑 기능을 위해서는 아래 환경 변수 설정이 필수적입니다.
- **SMTP 서버**: `smtp.gmail.com`
- **SMTP 포트**: `587`
- **발신 이메일**: `grantjeon2864@gmail.com`
- **수신 이메일**: `grantjeon2864@gmail.com`
- **SMTP 비밀번호 (`SMTP_PASSWORD`)**: Gmail 2단계 인증을 활성화한 후 발급받은 **16자리 구글 앱 비밀번호** 입력 필요. (현재 `umutousdoatiofma` 설정됨)
- **Gemini API Key (`GEMINI_API_KEY`)**: AI 뉴스 브리핑 자동 작성을 위한 구글 AI 스튜디오 API 키. 미지정 시 로컬 하드코딩 템플릿으로 대체 동작.

---

## 💻 4. 로컬 실행 및 제어 명령어

에이전트는 터미널에서 다음 명령어를 실행하여 서버 및 스크립트를 수동으로 기동하거나 상태를 테스트할 수 있습니다. (※ 절대 `cd` 명령어를 사용하지 말고 Cwd 옵션을 활용하십시오)

### A. 백엔드 API 서버 실행
- **실행 환경**: 가상환경 `.venv2` (Python 3.x)
- **실행 명령 (Cwd: 루트 디렉토리)**:
  ```powershell
  .\.venv2\Scripts\python.exe backend/main.py
  ```
- **API 기본 주소**: `http://127.0.0.1:8000`

### B. 프론트엔드 대시보드 개발 서버 실행
- **실행 명령 (Cwd: `frontend/` 디렉토리)**:
  ```powershell
  npm run dev
  ```
- **대시보드 주소**: `http://localhost:5173`

### C. 데이터 수집 및 이메일 발송 일괄 수동 테스트
- **실행 명령 (Cwd: 루트 디렉토리)**:
  ```powershell
  .\.venv2\Scripts\python.exe backend/collector.py
  .\.venv2\Scripts\python.exe backend/notifier.py
  .\.venv2\Scripts\python.exe backend/alarm.py
  ```

---

## 🛠️ 5. 주요 문제 상황 및 대응 가이드 (Troubleshooting)

1. **에이전트 세션 만료/중단 후 재개 시**:
   - 워크스페이스 내 `backend/data/metrics.json`과 `backend/data/report_chart.png` 존재 및 정합성을 검증합니다.
   - 백엔드와 프론트엔드 개발 서버의 구동 상태를 확인합니다.
2. **SMTP 전송 에러 (AuthenticationError 등)**:
   - `backend/.env`의 `SMTP_PASSWORD`가 올바른 구글 앱 비밀번호인지 확인합니다.
3. **TTS 또는 알람 사운드 작동 오류**:
   - `alarm.py`는 Windows 전용 `winsound` 및 PowerShell SpeechSynthesizer를 사용합니다. 비-Windows 환경이거나 오디오 장치가 없는 가상 환경에서는 작동하지 않거나 에러 로그가 출력될 수 있습니다.
4. **yfinance 데이터 수집 실패**:
   - 야후 파이낸스 일시적 차단이나 데이터 공백 시 결측치 보정 로직(`ffill()`, `bfill()`)이 실행되는지 로그를 모니터링합니다.

---

## 📝 6. 작업 진행 상태 & 다음 작업 후보 (Checklist)

- [x] 19대 경제 지표 수집 스크립트 작성 완료 (`backend/collector.py`)
- [x] 이메일 발송용 다중 서브플롯 Matplotlib 차트 생성 및 발송 스크립트 작성 완료 (`backend/notifier.py`)
- [x] Gemini API 및 로컬 백업 템플릿 기반 아침 경제 앵커 브리핑 대본 생성 스크립트 작성 완료 (`backend/alarm.py`)
- [x] winsound 경쾌한 알람음(도-미-솔-도) 멜로디 구현 완료 (`backend/alarm.py`)
- [x] PowerShell SpeechSynthesizer 기반 로컬 스피커 TTS 음성 낭독 연동 완료 (`backend/alarm.py`)
- [x] 백엔드 API 연동 및 알람 재생 엔드포인트 `/api/play-alarm` 추가 완료 (`backend/main.py`)
- [x] React + Vite + Chart.js Glassmorphism 프론트엔드 대시보드 구축 완료 (`frontend/`)
- [x] 프론트엔드 대시보드 상단 제어 바에 "브리핑 알람 듣기" 버튼 및 기능 추가 완료 (`frontend/src/App.jsx`)
- [x] 이메일용 HTML 본문에 AI 뉴스 앵커 브리핑 카드 연동 완료 (`backend/notifier.py`)
- [x] Windows 작업 스케줄러 자동 실행 연동 배치 파일 작성 및 alarm.py 통합 완료 (`run_daily.bat`)
- [x] 시스템 요약 안내 README 작성 완료 (`README.md`)
- [x] SMTP 포트 오류 수정 완료 (585 -> 587)
- [x] 실제 SMTP 비밀번호 설정 후 메일 발송 수동 테스트 및 검증 완료
- [x] Windows 작업 스케줄러에 배치 파일 등록 동작 검증 (매일 07:30 실행 등록 완료)


# 📈 일일 경제 지표 모니터링 대시보드 & 메일 전송 시스템

이 프로젝트는 거시 경제 지표, 주요 주식, ETF, 환율, 원자재 및 암호화폐(비트코인) 등 총 19개 지표의 최신 데이터를 왜곡 없이 실시간 수집하고, 이를 프리미엄 다크 모드 웹 대시보드로 세련되게 시각화하며, 매일 아침 분석 요약 차트가 포함된 HTML 보고서를 이메일로 자동 발송하는 통합 시스템입니다.

---

## 🛠️ 기술 스택 및 구조
- **데이터 레이어**: Python `yfinance` API (신뢰성 높은 데이터 추출)
- **백엔드 API**: Python `FastAPI` + `Uvicorn` (데이터 서빙 및 백그라운드 수집/메일 발송 트리거)
- **프론트엔드**: React + Vite + Vanilla CSS (Glassmorphism 다크 테마) + `Chart.js` (인터랙티브 시각화)
- **자동화 스케줄러**: Windows 작업 스케줄러 + `.bat` 실행 배치 파일

---

## 🚀 시작하기 전에: 이메일 SMTP 설정

매일 아침 이메일로 경제지표 요약 리포트를 받기 위해 SMTP 발송 설정을 완료해야 합니다.

1. **Gmail 앱 비밀번호 발급**:
   - `grantjeon2864@gmail.com` 구글 계정에 로그인합니다.
   - [구글 계정 관리] -> [보안] -> [2단계 인증]을 활성화합니다.
   - 2단계 인증 설정 완료 후, 최하단의 **[앱 비밀번호 (App Password)]** 메뉴를 클릭합니다.
   - 앱 이름을 `경제지표 수집기` 등으로 지정하고 **[만들기]**를 눌러 **16자리 비밀번호**를 발급받습니다.

2. **설정 파일 수정**:
   - [backend/.env](file:///c:/Users/전민정/.gemini/11.경제지표모으기/backend/.env) 파일을 텍스트 에디터로 엽니다.
   - `SMTP_PASSWORD` 항목에 발급받은 16자리 앱 비밀번호를 공백 없이 입력하고 저장합니다.
     ```env
     SMTP_PASSWORD=abcd efgh ijkl mnop  # (예시 - 실제 발급받은 문자열 입력)
     ```

---

## 💻 로컬 실행 방법

### 1. 백엔드 API 서버 실행
1. 파워쉘(PowerShell) 또는 CMD를 열고 프로젝트 루트 디렉토리로 이동합니다.
2. 가상환경의 파이썬을 활용해 FastAPI 서버를 작동시킵니다.
   ```bash
   .\.venv2\Scripts\python.exe backend/main.py
   ```
3. 백엔드 서버가 `http://127.0.0.1:8000`에서 실행됩니다.

### 2. 프론트엔드 대시보드 실행
1. 새로운 터미널 창을 열고 `frontend/` 디렉토리로 이동합니다.
2. 아래 명령어로 개발 서버를 시작합니다.
   ```bash
   cd frontend
   npm run dev
   ```
3. 웹 브라우저를 열고 `http://localhost:5173`에 접속하여 프리미엄 대시보드를 확인합니다.

---

## ⏰ 매일 아침 자동 메일 발송 설정 (Windows 작업 스케줄러)

매일 아침 정해진 시간에 자동으로 최신 데이터를 수집하고 이메일 리포트를 전송하려면 Windows의 작업 스케줄러에 등록하십시오.

1. 키보드의 `Windows Key + R`을 누르고 `taskschd.msc`를 입력하여 **작업 스케줄러**를 실행합니다.
2. 우측 [동작] 패널에서 **[기본 작업 만들기...]**를 클릭합니다.
3. **이름**: `경제지표 일일 리포트 발송`을 입력하고 [다음]을 누릅니다.
4. **작업 시작 시간**: **[매일]**을 선택하고 [다음]을 누릅니다.
5. **시간**: 매일 아침 메일을 받고 싶으신 시각 (예: 오전 07:30)을 설정하고 [다음]을 누릅니다.
6. **동작**: **[프로그램 시작]**을 선택하고 [다음]을 누릅니다.
7. **프로그램/스크립트**: **[찾아보기...]**를 눌러 본 프로젝트 폴더 내에 있는 [run_daily.bat](file:///c:/Users/전민정/.gemini/11.경제지표모으기/run_daily.bat) 파일을 선택합니다.
8. **시작 위치(옵션)**: 프로젝트의 전체 절대 경로를 입력합니다.
   - 예: `C:\Users\전민정\.gemini\11.경제지표모으기`
9. [마침]을 누르면 설정이 완료됩니다. 매일 설정한 시각에 자동으로 수집 및 메일 발송이 구동됩니다.

---

## 💻 다른 컴퓨터에서 이어서 실행하는 방법

GitHub에서 코드를 다운로드받아 새로운 PC에서 실행하려면 아래 가이드를 순서대로 진행해 주세요.

### 1단계. 소스코드 다운로드
새로운 PC의 터미널(PowerShell 등)을 열고, 프로젝트를 저장할 폴더로 이동한 뒤 아래 명령어를 실행합니다.
```powershell
git clone https://github.com/grantjeon96/11Economicreport.git
cd 11Economicreport
```

### 2단계. 백엔드(Python) 환경 및 패키지 설치
`.venv` 폴더는 제외되었으므로, 새로운 가상환경을 생성하고 필요한 패키지들을 설치합니다.
```powershell
# 1. 파이썬 가상환경 생성 (프로젝트 루트 디렉토리에서 실행)
python -m venv .venv2

# 2. 가상환경 활성화 (Windows 기준)
.\.venv2\Scripts\activate

# 3. 필요한 핵심 패키지들 설치
pip install fastapi uvicorn yfinance pandas matplotlib python-dotenv
```

### 3단계. 환경 설정 파일(.env) 수동 작성 (★필수★)
보안 상 `.env` 파일은 GitHub에 올라가지 않았습니다. `backend/` 폴더 내부에 **`.env`** 텍스트 파일을 새로 만들고 아래 양식을 기입해 주셔야 합니다.
```env
# SMTP 이메일 설정
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=grantjeon2864@gmail.com
SMTP_PASSWORD=umutousdoatiofma  # (발급받은 구글 앱 비밀번호 16자리)
RECEIVER_EMAIL=grantjeon2864@gmail.com

# 백엔드 서버 설정
PORT=8000
HOST=127.0.0.1

# Gemini API Key (AI 스튜디오에서 받은 키)
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4단계. 프론트엔드(React) 패키지 설치
```powershell
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. npm 라이브러리들 일괄 설치
npm install
```

### 5단계. 서버 실행
이후 기존 로컬 실행 방법과 동일하게 백엔드(`backend/main.py`) 및 프론트엔드 개발 서버(`npm.cmd run dev`)를 실행합니다.

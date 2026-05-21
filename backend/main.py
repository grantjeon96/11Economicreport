import os
import json
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collector import collect_metrics
from notifier import send_email_report
from alarm import run_alarm

app = FastAPI(title="Economic Metrics Dashboard API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실 배포 시에는 구체적인 Origin을 명시하는 것이 좋으나 로컬 개발 편의를 위해 * 설정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "metrics.json")

class RefreshResponse(BaseModel):
    status: str
    message: str

@app.get("/api/metrics")
def get_metrics():
    """
    저장된 JSON 경제 지표 데이터를 반환합니다.
    """
    if not os.path.exists(DATA_PATH):
        # 만약 데이터 파일이 없으면 즉시 한 번 수집을 시도합니다.
        try:
            data = collect_metrics()
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"데이터 수집 중 오류가 발생했습니다: {str(e)}")
            
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 중 오류가 발생했습니다: {str(e)}")

def bg_collect_and_notify():
    try:
        collect_metrics()
    except Exception as e:
        print(f"[배경 수집 오류] {str(e)}")

@app.post("/api/refresh", response_model=RefreshResponse)
def refresh_metrics(background_tasks: BackgroundTasks):
    """
    최신 데이터를 백그라운드에서 다시 수집하도록 요청합니다.
    """
    background_tasks.add_task(bg_collect_and_notify)
    return {"status": "success", "message": "최신 경제 지표 데이터 수집 작업이 백그라운드에서 시작되었습니다."}

def bg_send_email():
    try:
        send_email_report()
    except Exception as e:
        print(f"[배경 메일 발송 오류] {str(e)}")

@app.post("/api/send-email", response_model=RefreshResponse)
def trigger_email(background_tasks: BackgroundTasks):
    """
    최신 요약 보고서를 이메일로 수동 발송 요청합니다.
    """
    background_tasks.add_task(bg_send_email)
    return {"status": "success", "message": "이메일 보고서 발송 작업이 백그라운드에서 시작되었습니다."}

@app.post("/api/play-alarm", response_model=RefreshResponse)
def play_alarm(background_tasks: BackgroundTasks):
    """
    아침 뉴스 브리핑 알람을 스피커로 즉시 재생합니다.
    """
    background_tasks.add_task(run_alarm)
    return {"status": "success", "message": "아침 뉴스 앵커 브리핑 알람 재생이 시작되었습니다."}

if __name__ == "__main__":
    import uvicorn
    # .env 파일에서 호스트 및 포트 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    print(f"FastAPI 서버를 {host}:{port} 에서 실행합니다...")
    uvicorn.run("main:app", host=host, port=port, reload=True)

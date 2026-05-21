import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd

# 지표 매핑 정보 (한글 이름, 카테고리 포함)
METRIC_CONFIG = {
    # 1. 주요 지수
    "^GSPC": {"name": "S&P 500", "category": "지수"},
    "^IXIC": {"name": "나스닥 종합", "category": "지수"},
    "^KS11": {"name": "코스피", "category": "지수"},
    "^SOX": {"name": "필라델피아 반도체", "category": "지수"},
    "FNG": {"name": "CNN 공포와 탐욕 지수", "category": "지수"},
    
    # 2. ETF
    "EWY": {"name": "MSCI South Korea ETF (EWY)", "category": "ETF"},
    "KORU": {"name": "MSCI South Korea Bull 3X (KORU)", "category": "ETF"},
    
    # 3. 환율 및 금리
    "USDKRW=X": {"name": "원/달러 환율", "category": "환율 & 금리"},
    "JPY=X": {"name": "엔/달러 환율", "category": "환율 & 금리"},
    "^TNX": {"name": "미국 10년물 국채 금리", "category": "환율 & 금리"},
    
    # 4. 원자재
    "GC=F": {"name": "국제 금", "category": "원자재"},
    "CL=F": {"name": "WTI 원유", "category": "원자재"},
    
    # 5. 암호화폐
    "BTC-USD": {"name": "비트코인 (USD)", "category": "암호화폐"},
    
    # 6. 해외 주식 (미국)
    "NVDA": {"name": "엔비디아 (NVDA)", "category": "해외 주식"},
    "GOOGL": {"name": "구글 (GOOGL)", "category": "해외 주식"},
    "TSLA": {"name": "테슬라 (TSLA)", "category": "해외 주식"},
    "AMZN": {"name": "아마존 (AMZN)", "category": "해외 주식"},
    
    # 7. 국내 주식
    "005930.KS": {"name": "삼성전자", "category": "국내 주식"},
    "000660.KS": {"name": "SK하이닉스", "category": "국내 주식"},
    "005380.KS": {"name": "현대자동차", "category": "국내 주식"}
}

def collect_metrics():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 경제 지표 데이터 수집 시작...")
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    result = {
        "updated_at": datetime.now().isoformat(),
        "metrics": {}
    }
    
    for ticker, info in METRIC_CONFIG.items():
        try:
            print(f"수집 중: {info['name']} ({ticker})...")
            
            if ticker == "FNG":
                # CNN Fear & Greed Index 수집
                import ssl
                import urllib.request
                
                fng_url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
                fng_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "accept": "application/json",
                    "referer": "https://www.cnn.com/markets/fear-and-greed"
                }
                
                context = ssl._create_unverified_context()
                req = urllib.request.Request(fng_url, headers=fng_headers)
                
                with urllib.request.urlopen(req, context=context, timeout=10) as res:
                    fng_data = json.loads(res.read().decode("utf-8"))
                    
                curr_score = fng_data["fear_and_greed"]["score"]
                prev_close = fng_data["fear_and_greed"]["previous_close"]
                change = curr_score - prev_close
                change_percent = (change / prev_close) * 100
                
                history_data = []
                raw_hist = fng_data.get("fear_and_greed_historical", {}).get("data", [])
                for item in raw_hist:
                    if "x" in item and "y" in item:
                        date_str = datetime.fromtimestamp(item["x"] / 1000).strftime("%Y-%m-%d")
                        history_data.append({
                            "date": date_str,
                            "value": round(float(item["y"]), 1)
                        })
                        
                result["metrics"][ticker] = {
                    "name": info["name"],
                    "category": info["category"],
                    "current": round(curr_score, 1),
                    "change": round(change, 1),
                    "change_percent": round(change_percent, 1),
                    "history": history_data
                }
                continue
                
            # 최근 1년 데이터 수집
            yt = yf.Ticker(ticker)
            df = yt.history(period="1y")
            
            if df.empty:
                print(f"경고: {ticker} 데이터가 비어있습니다.")
                continue
                
            # 결측값 처리
            df = df.ffill().bfill()
            
            # 히스토리 리스트 생성 (프론트엔드 차트용)
            # 날짜를 문자열(YYYY-MM-DD)로 변환
            history_data = []
            for date, row in df.iterrows():
                history_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": round(float(row["Close"]), 1)
                })
                
            # 최신 값 및 변동폭 계산
            if len(df) >= 2:
                current_val = float(df["Close"].iloc[-1])
                prev_val = float(df["Close"].iloc[-2])
                change = current_val - prev_val
                change_percent = (change / prev_val) * 100
            else:
                current_val = float(df["Close"].iloc[-1])
                change = 0.0
                change_percent = 0.0
                
            result["metrics"][ticker] = {
                "name": info["name"],
                "category": info["category"],
                "current": round(current_val, 1),
                "change": round(change, 1),
                "change_percent": round(change_percent, 1),
                "history": history_data
            }
            
        except Exception as e:
            print(f"오류 발생 ({ticker}): {str(e)}")
            
    # JSON 파일로 저장
    output_path = os.path.join(data_dir, "metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 수집 완료! 저장 경로: {output_path}")
    return result

if __name__ == "__main__":
    collect_metrics()

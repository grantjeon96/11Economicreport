import os
import json
import urllib.request
import urllib.parse
import subprocess
import winsound
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def generate_briefing():
    """
    metrics.json 데이터를 기반으로 Gemini API 또는 로컬 템플릿을 사용하여 아침 뉴스 브리핑 대본을 생성합니다.
    """
    backend_dir = os.path.dirname(__file__)
    data_path = os.path.join(backend_dir, "data", "metrics.json")
    if not os.path.exists(data_path):
        return "경제 지표 데이터를 찾을 수 없습니다. 수집기를 먼저 가동해 주세요."
        
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    metrics = data["metrics"]
    
    # Gemini 전송용 시황 데이터 텍스트 요약
    data_summary = []
    for ticker, info in metrics.items():
        data_summary.append(f"- {info['name']}({ticker}): 현재가 {info['current']:,}, 전일대비 {info['change']:,} ({info['change_percent']}%)")
    data_text = "\n".join(data_summary)
    
    api_key = os.getenv("GEMINI_API_KEY")
    # API 키가 기본 템플릿 값이거나 비어있으면 로컬 요약으로 대체
    if not api_key or api_key == "your_gemini_api_key_here" or api_key.strip() == "":
        print("GEMINI_API_KEY가 등록되지 않았거나 기본값입니다. 로컬 방어 템플릿으로 요약을 작성합니다.")
        return get_local_fallback_briefing(metrics)
        
    try:
        # 사용자가 요청한 gemini-3-flash의 실제 사용 가능한 최신 플래시 모델(gemini-2.0-flash) 호출
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        prompt = (
            "당신은 대한민국 대표 경제 방송의 활기차고 신뢰감 있는 아침뉴스 경제 전문 앵커입니다. "
            "오늘 아침 글로벌 금융시장 지표 요약 데이터를 읽고, 시청자(나)의 잠을 깨울 수 있는 쾌활하고 명확한 아침 뉴스 브리핑 대본을 작성해 주세요.\n\n"
            "[대본 작성 조건]\n"
            "- 친근하면서도 전문적인 앵커 톤앤매너를 사용해 주세요. (예: '안녕하십니까 시청자 여러분, 아침 6시 경제 뉴스 브리핑입니다. 상쾌한 하루 시작하고 계신가요?')\n"
            "- 시청자(나)를 기분 좋게 잠에서 깨울 수 있도록 에너지가 넘치고 다정한 말투를 사용해 주세요.\n"
            "- 가장 큰 변동폭을 보인 지표들을 콕 짚어서 핵심을 요약해 주세요.\n"
            "- 음성 TTS(Text-to-Speech)로 자연스럽게 읽힐 수 있도록 특수 기호(*, %, $ 등)나 영어 약어는 한글 발음으로 풀어서 적어주세요. (예: 'S&P 500'은 '에스앤피 오백', '%'는 '퍼센트', 'USD'는 '달러' 등)\n"
            "- 오늘 하루를 응원하는 긍정적인 마무리 멘트로 끝내 주세요.\n"
            "- 분량은 TTS로 약 1분 내외로 읽을 수 있는 크기(공백 제외 300~500자)로 해 주세요.\n\n"
            f"[오늘의 경제 지표 데이터]\n{data_text}"
        )
        
        headers = {
            "Content-Type": "application/json"
        }
        
        req_data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        req_body = json.dumps(req_data).encode("utf-8")
        req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
        
        # 15초 타임아웃
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            res_json = json.loads(res_body)
            briefing_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            # 불필요한 마크다운 문장 부호(샵, 별표 등) 정제
            briefing_text = briefing_text.replace("*", "").replace("#", "").replace("`", "")
            return briefing_text
            
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {str(e)}. 로컬 요약으로 안전하게 전환합니다.")
        return get_local_fallback_briefing(metrics)

def get_local_fallback_briefing(metrics):
    """
    Gemini API Key가 없거나 오류 시 재생할 로컬 룰 기반 브리핑 스크립트 (뉴스 앵커 멘트 스타일 고도화)
    """
    text = (
        "안녕하십니까 시청자 여러분. 아침 5시 경제 뉴스 브리핑입니다. 오늘 아침 글로벌 금융시장 주요 지표 결과를 전해드리겠습니다. "
    )
    # 주요 지표들 요약
    important = ["^GSPC", "^KS11", "USDKRW=X", "BTC-USD", "FNG"]
    summaries = []
    for ticker in important:
        if ticker in metrics:
            m = metrics[ticker]
            direction = "상승" if m["change"] > 0 else ("하락" if m["change"] < 0 else "보합")
            name_clean = m["name"].split('(')[0].strip()
            
            # 한글화 치환
            name_clean = name_clean.replace("S&P 500", "에스앤피 오백").replace("원/달러 환율", "원 달러 환율").replace("비트코인", "비트코인").replace("코스피", "코스피").replace("CNN 공포와 탐욕 지수", "시앤앤 공포와 탐욕 지수")
            
            current_val = round(float(m['current']), 1)
            change_pct = round(abs(float(m['change_percent'])), 1)
            val_str = f"{current_val:,}"
            
            if ticker == "BTC-USD":
                val_str += " 달러"
            elif ticker == "USDKRW=X":
                val_str += " 원"
            elif ticker == "FNG":
                val_str += " 포인트"
            else:
                val_str += " 포인트"
                
            summaries.append(f"먼저 {name_clean}은 현재 {val_str}로, 전일 대비 {change_pct}퍼센트 {direction}하였습니다.")
            
    text += " ".join(summaries)
    
    # 공포탐욕지수 상태 멘트 추가
    if "FNG" in metrics:
        fng_val = float(metrics["FNG"]["current"])
        if fng_val >= 75:
            status_msg = " 현재 시장은 극도의 탐욕 상태로 투자자들의 심리가 매우 과열되어 있습니다."
        elif fng_val >= 55:
            status_msg = " 현재 시장은 탐욕 상태로 긍정적인 투자 심리가 유지되고 있습니다."
        elif fng_val >= 45:
            status_msg = " 현재 시장은 중립 상태로 눈치 보기 장세가 이어지고 있습니다."
        elif fng_val >= 25:
            status_msg = " 현재 시장은 공포 상태로 투자 심리가 다소 위축되었습니다."
        else:
            status_msg = " 현재 시장은 극도의 공포 상태로 매도 압력이 매우 강한 상황입니다."
        text += status_msg
        
    text += " 이상으로 아침 경제 브리핑을 마칩니다. 든든한 아침 시작하시고, 오늘도 활기차고 성공적인 하루 보내시기 바랍니다. 감사합니다."
    return text

def play_alarm_sound():
    """
    잠을 깨울 수 있는 맑고 경쾌한 딩동댕 알림 멜로디 재생 (winsound Beep 활용)
    """
    print("딩동댕 알람음 재생 중...")
    try:
        # 도-미-솔-도 멜로디
        melody = [
            (523, 300),  # 도 (C5)
            (659, 300),  # 미 (E5)
            (784, 300),  # 솔 (G5)
            (1046, 500), # 도 (C6)
        ]
        for freq, duration in melody:
            winsound.Beep(freq, duration)
            time.sleep(0.05)
    except Exception as e:
        print(f"알람 재생 에러 (Beep): {str(e)}")

def speak_text(text):
    """
    PowerShell SpeechSynthesizer를 활용하여 로컬 스피커로 TTS 재생
    """
    print("뉴스 브리핑 한국어 음성 낭독을 시작합니다...")
    # PowerShell 스크립트 작성 (안정성을 위해 특수 기호 치환)
    escaped_text = text.replace('"', '""').replace("'", "''").replace("\n", " ").replace("\r", "")
    
    ps_script = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 6
    $synth.Speak("{escaped_text}")
    """
    
    try:
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"TTS 재생 에러: {str(e)}")

def run_alarm():
    # 1. 알람 멜로디 울림
    play_alarm_sound()
    time.sleep(0.5)
    
    # 2. 뉴스 브리핑 텍스트 생성
    briefing = generate_briefing()
    print("\n[브리핑 대본 내용]\n", briefing, "\n")
    
    # 3. 브리핑 음성 재생
    speak_text(briefing)

if __name__ == "__main__":
    run_alarm()

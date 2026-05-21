import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from alarm import generate_briefing

# .env 로드
load_dotenv()

def generate_charts(data_path, output_image_path):
    """
    사용자 정의 5대 비교 차트 그룹을 생성합니다. (Matplotlib 2중축 & 다중라인 적용)
    """
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    metrics = data["metrics"]
    
    # Matplotlib 스타일 설정 (다크 모드 및 한글 폰트 적용)
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.facecolor'] = '#121214'
    plt.rcParams['axes.facecolor'] = '#1a1a1e'
    plt.rcParams['text.color'] = '#e2e8f0'
    plt.rcParams['axes.labelcolor'] = '#a0aec0'
    plt.rcParams['xtick.color'] = '#718096'
    plt.rcParams['ytick.color'] = '#718096'
    plt.rcParams['grid.color'] = '#2d3748'
    plt.rcParams['axes.edgecolor'] = '#2d3748'
    
    # 3x2 서브플롯 생성 (총 6개 슬롯, 5개 사용하고 6번째 슬롯은 설명 영역)
    fig, axes = plt.subplots(3, 2, figsize=(15, 18), sharex=False)
    axes = axes.flatten()
    
    # Helper: 최근 30일 데이터 가져오기
    def get_history_df(ticker):
        if ticker not in metrics:
            return None
        df = pd.DataFrame(metrics[ticker]["history"])
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").tail(30)
        
    # --- 1. 환율 비교 (2중 Y축: 원/달러 vs 엔/달러) ---
    ax = axes[0]
    df1 = get_history_df("USDKRW=X")
    df2 = get_history_df("JPY=X")
    
    if df1 is not None and df2 is not None:
        # 좌측 축: 원/달러
        ax.plot(df1["date"], df1["value"], color='#4fd1c5', linewidth=2.5, label='원/달러(좌)')
        ax.set_ylabel('원/달러 환율 (KRW)', color='#4fd1c5')
        ax.tick_params(axis='y', labelcolor='#4fd1c5')
        
        # 우측 축: 엔/달러
        ax_right = ax.twinx()
        ax_right.plot(df2["date"], df2["value"], color='#f6ad55', linewidth=2.5, label='엔/달러(우)')
        ax_right.set_ylabel('엔/달러 환율 (JPY)', color='#f6ad55')
        ax_right.tick_params(axis='y', labelcolor='#f6ad55')
        ax_right.grid(False)
        
        ax.set_title('환율 비교 (2중 축)\n[원/달러 vs 엔/달러]', fontsize=12, pad=10, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax_right.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper left', framealpha=0.1)
    else:
        ax.text(0.5, 0.5, "Data Not Available", ha='center', va='center')

    # --- 2. 미국 빅테크 (다중 라인: NVDA, GOOGL, TSLA, AMZN) ---
    ax = axes[1]
    tickers_tech = ["NVDA", "GOOGL", "TSLA", "AMZN"]
    colors_tech = ['#81e6d9', '#63b3ed', '#fc8181', '#f6ad55']
    
    any_plotted = False
    for ticker, color in zip(tickers_tech, colors_tech):
        df = get_history_df(ticker)
        if df is not None:
            ax.plot(df["date"], df["value"], color=color, linewidth=2, label=metrics[ticker]["name"].split(' ')[0])
            any_plotted = True
            
    if any_plotted:
        ax.set_title('미국 빅테크 주가 추이\n[엔비디아, 구글, 테슬라, 아마존]', fontsize=12, pad=10, fontweight='bold')
        ax.set_ylabel('주가 (USD)', color='#a0aec0')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(loc='upper left', framealpha=0.1)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    else:
        ax.text(0.5, 0.5, "Data Not Available", ha='center', va='center')

    # --- 3. 글로벌 자산 비교 (다중 라인: S&P, 코스피, 금) ---
    ax = axes[2]
    tickers_global = ["^GSPC", "^KS11", "GC=F"]
    names_global = ["S&P 500", "KOSPI", "국제 금"]
    colors_global = ['#63b3ed', '#f687b3', '#ecc94b']
    
    any_plotted = False
    for ticker, color, name in zip(tickers_global, colors_global, names_global):
        df = get_history_df(ticker)
        if df is not None and not df.empty:
            first_val = df["value"].iloc[0]
            relative_val = (df["value"] / first_val) * 100
            ax.plot(df["date"], relative_val, color=color, linewidth=2, label=f"{name} (%)")
            any_plotted = True
            
    if any_plotted:
        ax.set_title('글로벌 자산 트렌드 (상대 지수)\n[S&P 500, KOSPI, 국제 금]', fontsize=12, pad=10, fontweight='bold')
        ax.set_ylabel('상대 지수 (30일 전 = 100)', color='#a0aec0')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(loc='upper left', framealpha=0.1)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    else:
        ax.text(0.5, 0.5, "Data Not Available", ha='center', va='center')

    # --- 4. 한국 ETF (2중 Y축: EWY vs KORU) ---
    ax = axes[3]
    df1 = get_history_df("EWY")
    df2 = get_history_df("KORU")
    
    if df1 is not None and df2 is not None:
        ax.plot(df1["date"], df1["value"], color='#9f7aea', linewidth=2.5, label='EWY (좌)')
        ax.set_ylabel('MSCI South Korea (EWY)', color='#9f7aea')
        ax.tick_params(axis='y', labelcolor='#9f7aea')
        
        ax_right = ax.twinx()
        ax_right.plot(df2["date"], df2["value"], color='#f687b3', linewidth=2.5, label='KORU 3X (우)')
        ax_right.set_ylabel('MSCI South Korea Bull 3X (KORU)', color='#f687b3')
        ax_right.tick_params(axis='y', labelcolor='#f687b3')
        ax_right.grid(False)
        
        ax.set_title('한국 ETF 비교 (2중 축)\n[EWY vs KORU (3X 레버리지)]', fontsize=12, pad=10, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax_right.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper left', framealpha=0.1)
    else:
        ax.text(0.5, 0.5, "Data Not Available", ha='center', va='center')

    # --- 5. 원유 & 비트코인 (2중 Y축: WTI 원유 vs 비트코인) ---
    ax = axes[4]
    df1 = get_history_df("CL=F")
    df2 = get_history_df("BTC-USD")
    
    if df1 is not None and df2 is not None:
        ax.plot(df1["date"], df1["value"], color='#fc8181', linewidth=2.5, label='WTI 원유 (좌)')
        ax.set_ylabel('WTI 원유 선물 가격 (USD)', color='#fc8181')
        ax.tick_params(axis='y', labelcolor='#fc8181')
        
        ax_right = ax.twinx()
        ax_right.plot(df2["date"], df2["value"], color='#ecc94b', linewidth=2.5, label='비트코인 (우)')
        ax_right.set_ylabel('비트코인 가격 (USD)', color='#ecc94b')
        ax_right.tick_params(axis='y', labelcolor='#ecc94b')
        ax_right.grid(False)
        
        ax.set_title('원유 & 비트코인 추이 (2중 축)\n[WTI 원유 vs 비트코인]', fontsize=12, pad=10, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax_right.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper left', framealpha=0.1)
    else:
        ax.text(0.5, 0.5, "Data Not Available", ha='center', va='center')

    # --- 6. 요약 안내 텍스트 영역 ---
    ax = axes[5]
    ax.axis('off')
    text_content = (
        "리포트 활용 안내\n\n"
        "• 환율 및 원유, 비트코인, 한국 ETF(EWY/KORU)는\n"
        "  자산간 상관관계 및 변동폭 비교를 위해\n"
        "  2중 축(Dual Y-Axis)을 적용하였습니다.\n\n"
        "• 글로벌 자산 비교는 단위 격차가 크므로\n"
        "  30일 전 기준 지수화(%)하여 나타냈습니다.\n\n"
        "• 본 요약 리포트 차트는 매일 아침 자동 생성됩니다."
    )
    ax.text(0.1, 0.2, text_content, color='#cbd5e1', fontsize=11, 
            bbox=dict(facecolor='#1e293b', edgecolor=(1, 1, 1, 0.08), boxstyle='round,pad=1.2', alpha=0.8))

    plt.tight_layout()
    
    # 디렉토리 생성 후 이미지 저장
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    plt.savefig(output_image_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"리포트용 요약 비교 차트 이미지 생성 완료: {output_image_path}")

def build_html_body(data_path):
    """
    이메일용 HTML 본문을 작성합니다.
    """
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    metrics = data["metrics"]
    updated_time = datetime.fromisoformat(data["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")
    
    # 앵커 브리핑 텍스트 생성
    try:
        briefing_text = generate_briefing()
    except Exception as e:
        briefing_text = "아침 뉴스 브리핑을 생성하는 도중 오류가 발생했습니다."
    
    # 지표 행(Row) 생성 로직
    rows_html = ""
    for ticker, val in metrics.items():
        change_class = "up" if val["change"] > 0 else ("down" if val["change"] < 0 else "neutral")
        change_sign = "+" if val["change"] > 0 else ""
        change_style = "color: #22c55e;" if change_class == "up" else ("color: #ef4444;" if change_class == "down" else "color: #94a3b8;")
        
        rows_html += f"""
        <tr style="border-bottom: 1px solid #2d3748;">
            <td style="padding: 12px; font-weight: bold; color: #f8fafc;">{val['name']}</td>
            <td style="padding: 12px; color: #cbd5e1; text-align: right;">{float(val['current']):,.1f}</td>
            <td style="padding: 12px; font-weight: bold; text-align: right; {change_style}">
                {change_sign}{float(val['change']):,.1f} ({change_sign}{float(val['change_percent']):,.1f}%)
            </td>
        </tr>
        """
        
    # HTML 이메일 템플릿 (세련된 다크 글래스 감성)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 700px;
                margin: 0 auto;
                background-color: #1e293b;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }}
            .header {{
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 2px solid #334155;
            }}
            .header h1 {{
                font-size: 24px;
                color: #f8fafc;
                margin: 0 0 10px 0;
            }}
            .header p {{
                font-size: 14px;
                color: #94a3b8;
                margin: 0;
            }}
            .table-container {{
                margin-top: 25px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background-color: #334155;
                color: #cbd5e1;
                padding: 12px;
                text-align: left;
                font-size: 14px;
            }}
            .chart-container {{
                margin-top: 30px;
                text-align: center;
            }}
            .chart-container img {{
                max-width: 100%;
                border-radius: 8px;
                border: 1px solid #334155;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                font-size: 12px;
                color: #64748b;
                border-top: 1px solid #334155;
                padding-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header" style="margin-bottom: 20px;">
                <h1>📈 일일 거시경제 & 자산 지표 리포트</h1>
                <p>수집 기준 시각: {updated_time} (KST)</p>
            </div>
            
            <!-- 아침 경제 앵커 브리핑 카드 추가 -->
            <div style="background-color: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 25px;">
                <h3 style="color: #60a5fa; margin-top: 0; margin-bottom: 12px; font-size: 16px;">🎙️ 아침 뉴스 앵커 경제 브리핑</h3>
                <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin: 0; white-space: pre-line;">{briefing_text}</p>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="border-top-left-radius: 6px; border-bottom-left-radius: 6px; padding: 12px; text-align: left;">지표명</th>
                            <th style="padding: 12px; text-align: right;">현재가</th>
                            <th style="border-top-right-radius: 6px; border-bottom-right-radius: 6px; padding: 12px; text-align: right;">전일 대비 변동</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            
            <div class="chart-container">
                <h3 style="color: #f8fafc; text-align: left; margin-bottom: 15px;">📊 핵심 지표 최근 30일 트렌드</h3>
                <img src="cid:summary_chart" alt="최근 30일 트렌드 차트">
            </div>
            
            <div class="footer">
                본 메일은 수집 스케줄러에 의해 자동으로 발송되었습니다.<br>
                © 2026 경제지표 모니터링 시스템. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email_report():
    backend_dir = os.path.dirname(__file__)
    data_path = os.path.join(backend_dir, "data", "metrics.json")
    chart_path = os.path.join(backend_dir, "data", "report_chart.png")
    
    if not os.path.exists(data_path):
        print(f"오류: 수집된 데이터 파일({data_path})을 찾을 수 없습니다. 수집기를 먼저 실행해 주세요.")
        return False
        
    # 차트 이미지 생성
    generate_charts(data_path, chart_path)
    
    # SMTP 환경 변수 읽기
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    receiver = os.getenv("RECEIVER_EMAIL")
    
    if not sender or not password or password == "your_gmail_app_password_here":
        print("경고: SMTP 계정 정보(.env)가 올바르게 기입되지 않았습니다. 메일 발송을 스킵합니다.")
        return False
        
    print(f"이메일 발송 준비 중 ({sender} -> {receiver})...")
    
    # 이메일 메시지 생성 (Multipart 'related'로 이미지 inline 삽입 지원)
    msg = MIMEMultipart("related")
    msg["Subject"] = f"🔔 [경제지표 리포트] {datetime.now().strftime('%Y-%m-%d')} 경제 지표 요약"
    msg["From"] = sender
    msg["To"] = receiver
    
    # HTML 본문
    html_content = build_html_body(data_path)
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    msg_alternative.attach(MIMEText(html_content, "html"))
    
    # 차트 이미지 첨부 (CID 매핑)
    try:
        with open(chart_path, "rb") as img_f:
            msg_image = MIMEImage(img_f.read())
            msg_image.add_header("Content-ID", "<summary_chart>")
            msg.attach(msg_image)
    except Exception as e:
        print(f"차트 첨부 중 오류: {str(e)}")
        return False
        
    # 메일 발송
    try:
        # TLS 보안 연결 설정
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("이메일 발송 성공!")
        return True
    except Exception as e:
        print(f"이메일 발송 실패: {str(e)}")
        return False

if __name__ == "__main__":
    send_email_report()

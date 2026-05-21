import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  Mail, 
  Calendar, 
  DollarSign, 
  BarChart3, 
  Info,
  CheckCircle2,
  AlertCircle,
  Volume2
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import './App.css';

// Chart.js 컴포넌트 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTicker, setSelectedTicker] = useState('^IXIC'); // 기본값 나스닥
  const [activeCategory, setActiveCategory] = useState('전체');
  const [period, setPeriod] = useState('1Y'); // 기본값 1년
  const [refreshing, setRefreshing] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [playingAlarm, setPlayingAlarm] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [viewMode, setViewMode] = useState('individual'); // 'individual' or 'comparison'

  // 토스트 메시지 생성 헬퍼
  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // 데이터 로드
  const fetchMetrics = async (showToast = false) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/metrics`);
      if (!res.ok) throw new Error('API 응답에 오류가 발생했습니다.');
      const json = await res.json();
      setData(json);
      setLoading(false);
      if (showToast) {
        addToast('최신 경제지표 데이터 로드 완료!', 'success');
      }
    } catch (err) {
      console.error(err);
      addToast('데이터를 불러오지 못했습니다. 서버 상태를 확인하세요.', 'error');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // 30초마다 데이터 폴링 (백그라운드에서 수집이 끝날 수 있으므로)
    const interval = setInterval(() => {
      fetchMetrics(false);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // 수동 수집 요청
  const handleRefresh = async () => {
    setRefreshing(true);
    addToast('최신 데이터 수집을 요청했습니다. (약 5~10초 소요)', 'info');
    try {
      const res = await fetch(`${API_BASE_URL}/api/refresh`, { method: 'POST' });
      if (!res.ok) throw new Error('수집 트리거 요청 실패');
      
      // 약 7초 후에 최신 데이터를 다시 폴링해옴
      setTimeout(async () => {
        await fetchMetrics(true);
        setRefreshing(false);
      }, 7000);
    } catch (err) {
      console.error(err);
      addToast('수집 요청에 실패했습니다.', 'error');
      setRefreshing(false);
    }
  };

  // 이메일 발송 요청
  const handleSendEmail = async () => {
    setSendingEmail(true);
    addToast('일일 요약 보고서 발송 중...', 'info');
    try {
      const res = await fetch(`${API_BASE_URL}/api/send-email`, { method: 'POST' });
      if (!res.ok) throw new Error('이메일 전송 실패');
      const json = await res.json();
      addToast('이메일 보고서 발송 완료! (SMTP 미설정 시 스킵됨)', 'success');
      setSendingEmail(false);
    } catch (err) {
      console.error(err);
      addToast('이메일 발송에 실패했습니다.', 'error');
      setSendingEmail(false);
    }
  };

  // 알람 재생 요청
  const handlePlayAlarm = async () => {
    setPlayingAlarm(true);
    addToast('아침 뉴스 앵커 브리핑 알람 재생을 요청했습니다...', 'info');
    try {
      const res = await fetch(`${API_BASE_URL}/api/play-alarm`, { method: 'POST' });
      if (!res.ok) throw new Error('알람 재생 실패');
      
      // 백그라운드 구동이므로 5초 후에 버튼 상태 해제
      setTimeout(() => {
        setPlayingAlarm(false);
      }, 5000);
    } catch (err) {
      console.error(err);
      addToast('알람 재생 요청에 실패했습니다.', 'error');
      setPlayingAlarm(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="loading-overlay">
        <div className="spinner"></div>
        <p style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>글로벌 경제 지표 데이터를 실시간으로 가져오는 중...</p>
      </div>
    );
  }

  const { metrics, updated_at } = data;
  const formattedUpdateTime = new Date(updated_at).toLocaleString('ko-KR');

  // 기간 필터에 따른 역사적 차트 데이터 자르기
  const getHistorySlice = (history) => {
    if (!history || !Array.isArray(history)) return [];
    switch (period) {
      case '1W': return history.slice(-7);
      case '1M': return history.slice(-30);
      case '3M': return history.slice(-90);
      case '1Y': return history.slice(-250);
      default: return history;
    }
  };

  // 5종 비교 차트 데이터 생성을 위한 공통 날짜 레이블 추출 함수
  const getCommonLabels = (tickers) => {
    const dates = new Set();
    tickers.forEach(ticker => {
      if (metrics[ticker]) {
        const history = getHistorySlice(metrics[ticker].history);
        if (Array.isArray(history)) {
          history.forEach(h => {
            if (h && h.date) {
              dates.add(h.date);
            }
          });
        }
      }
    });
    return Array.from(dates).sort();
  };

  // 공통 날짜 레이블에 맞추어 특정 티커의 데이터를 배열로 추출 (결측값 ffill 처리)
  const getDatasetData = (ticker, labels) => {
    if (!metrics[ticker]) return labels.map(() => 0);
    const history = metrics[ticker].history || [];
    const dataMap = new Map(history.map(h => [h.date, h.value]));
    let lastVal = metrics[ticker].current;
    
    // 첫 유효 값을 찾기 위해 정렬된 history에서 가장 오래된 값 탐색
    if (history.length > 0) {
      const sortedHist = [...history].sort((a, b) => new Date(a.date) - new Date(b.date));
      lastVal = sortedHist[0].value;
    }
    
    return labels.map(date => {
      if (dataMap.has(date)) {
        lastVal = dataMap.get(date);
        return lastVal;
      }
      return lastVal;
    });
  };

  // 상대 지수(선택 기간의 시작점 = 100%) 데이터 추출
  const getRelativeDatasetData = (ticker, labels) => {
    const rawData = getDatasetData(ticker, labels);
    const firstVal = rawData.find(v => v !== null && v !== 0 && v !== undefined);
    if (!firstVal) return rawData;
    return rawData.map(v => v ? Math.round((v / firstVal) * 100 * 100) / 100 : 100);
  };

  // 1. 환율 비교 (원/달러 vs 엔/달러)
  const exchangeLabels = getCommonLabels(['USDKRW=X', 'JPY=X']);
  const exchangeChartData = {
    labels: exchangeLabels.map(d => d.substring(5)),
    datasets: [
      {
        label: '원/달러 환율 (좌)',
        data: getDatasetData('USDKRW=X', exchangeLabels),
        borderColor: '#4fd1c5',
        backgroundColor: 'rgba(79, 209, 197, 0.05)',
        yAxisID: 'y',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: '엔/달러 환율 (우)',
        data: getDatasetData('JPY=X', exchangeLabels),
        borderColor: '#f6ad55',
        backgroundColor: 'rgba(246, 173, 85, 0.05)',
        yAxisID: 'y1',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      }
    ]
  };

  const exchangeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#cbd5e1', font: { size: 11, weight: 600 } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 9 } }
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#4fd1c5', font: { size: 9 } },
        title: { display: true, text: '원/달러 (KRW)', color: '#4fd1c5', font: { size: 10, weight: 'bold' } }
      },
      y1: {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: '#f6ad55', font: { size: 9 } },
        title: { display: true, text: '엔/달러 (JPY)', color: '#f6ad55', font: { size: 10, weight: 'bold' } }
      }
    }
  };

  // 2. 미국 빅테크 (NVDA, GOOGL, TSLA, AMZN)
  const techTickers = ['NVDA', 'GOOGL', 'TSLA', 'AMZN'];
  const techLabels = getCommonLabels(techTickers);
  const techColors = ['#81e6d9', '#63b3ed', '#fc8181', '#f6ad55'];
  const techChartData = {
    labels: techLabels.map(d => d.substring(5)),
    datasets: techTickers.map((ticker, idx) => ({
      label: metrics[ticker]?.name.split(' ')[0] || ticker,
      data: getDatasetData(ticker, techLabels),
      borderColor: techColors[idx],
      backgroundColor: 'transparent',
      borderWidth: 2,
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 4,
    }))
  };

  const techChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#cbd5e1', font: { size: 11, weight: 600 } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (item) => `${item.dataset.label}: ${parseFloat(item.parsed.y).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} USD`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 9 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#cbd5e1', font: { size: 9 } },
        title: { display: true, text: '주가 (USD)', color: '#cbd5e1', font: { size: 10, weight: 'bold' } }
      }
    }
  };

  // 3. 글로벌 자산 비교 (절대 수치: S&P, 코스피, 금)
  const globalTickers = ['^GSPC', '^KS11', 'GC=F'];
  const globalLabels = getCommonLabels(globalTickers);
  const globalColors = ['#63b3ed', '#f687b3', '#ecc94b'];
  const globalNames = ['S&P 500', 'KOSPI', '국제 금'];
  const globalChartData = {
    labels: globalLabels.map(d => d.substring(5)),
    datasets: globalTickers.map((ticker, idx) => ({
      label: globalNames[idx],
      data: getDatasetData(ticker, globalLabels),
      borderColor: globalColors[idx],
      backgroundColor: 'transparent',
      borderWidth: 2,
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 4,
    }))
  };

  const globalChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#cbd5e1', font: { size: 11, weight: 600 } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (item) => `${item.dataset.label}: ${parseFloat(item.parsed.y).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 9 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#cbd5e1', font: { size: 9 } },
        title: { display: true, text: '지수 및 가격 (Point / USD)', color: '#cbd5e1', font: { size: 10, weight: 'bold' } }
      }
    }
  };

  // 4. 한국 ETF 비교 (EWY vs KORU)
  const etfLabels = getCommonLabels(['EWY', 'KORU']);
  const etfChartData = {
    labels: etfLabels.map(d => d.substring(5)),
    datasets: [
      {
        label: 'EWY (좌)',
        data: getDatasetData('EWY', etfLabels),
        borderColor: '#9f7aea',
        backgroundColor: 'rgba(159, 122, 234, 0.05)',
        yAxisID: 'y',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: 'KORU (우)',
        data: getDatasetData('KORU', etfLabels),
        borderColor: '#f687b3',
        backgroundColor: 'rgba(246, 135, 179, 0.05)',
        yAxisID: 'y1',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      }
    ]
  };

  const etfChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#cbd5e1', font: { size: 11, weight: 600 } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 9 } }
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#9f7aea', font: { size: 9 } },
        title: { display: true, text: 'EWY (USD)', color: '#9f7aea', font: { size: 10, weight: 'bold' } }
      },
      y1: {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: '#f687b3', font: { size: 9 } },
        title: { display: true, text: 'KORU (USD)', color: '#f687b3', font: { size: 10, weight: 'bold' } }
      }
    }
  };

  // 5. 원자재 & 암호화폐 (WTI 원유 vs 비트코인)
  const comLabels = getCommonLabels(['CL=F', 'BTC-USD']);
  const comChartData = {
    labels: comLabels.map(d => d.substring(5)),
    datasets: [
      {
        label: 'WTI 원유 (좌)',
        data: getDatasetData('CL=F', comLabels),
        borderColor: '#fc8181',
        backgroundColor: 'rgba(252, 129, 129, 0.05)',
        yAxisID: 'y',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: '비트코인 (우)',
        data: getDatasetData('BTC-USD', comLabels),
        borderColor: '#ecc94b',
        backgroundColor: 'rgba(236, 201, 75, 0.05)',
        yAxisID: 'y1',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      }
    ]
  };

  const comChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#cbd5e1', font: { size: 11, weight: 600 } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 9 } }
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#fc8181', font: { size: 9 } },
        title: { display: true, text: 'WTI 원유 (USD)', color: '#fc8181', font: { size: 10, weight: 'bold' } }
      },
      y1: {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        ticks: { color: '#ecc94b', font: { size: 9 } },
        title: { display: true, text: '비트코인 (USD)', color: '#ecc94b', font: { size: 10, weight: 'bold' } }
      }
    }
  };

  // 카테고리 고유 목록 추출
  const categories = ['전체', '지수', 'ETF', '주식', '환율 & 금리', '원자재', '암호화폐'];

  // 카테고리 매핑 매치
  const getMappedCategory = (rawCat) => {
    if (rawCat === '해외 주식' || rawCat === '국내 주식') return '주식';
    return rawCat;
  };

  // 필터링된 티커 목록
  const filteredTickers = Object.keys(metrics).filter((ticker) => {
    if (activeCategory === '전체') return true;
    const cat = getMappedCategory(metrics[ticker].category);
    return cat === activeCategory;
  });

  // 선택된 메트릭 상세 정보
  const activeMetric = metrics[selectedTicker] || Object.values(metrics)[0];

  const chartHistory = getHistorySlice(activeMetric.history);

  // 차트 디자인 구성
  const isUp = activeMetric.change >= 0;
  const lineColor = isUp ? '#10b981' : '#ef4444';
  const gradientColor = isUp ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';

  const chartData = {
    labels: chartHistory.map(h => h.date.substring(5)), // MM-DD 포맷
    datasets: [
      {
        label: activeMetric.name,
        data: chartHistory.map(h => h.value),
        borderColor: lineColor,
        borderWidth: 2.5,
        backgroundColor: (context) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 380);
          gradient.addColorStop(0, gradientColor);
          gradient.addColorStop(1, 'rgba(0,0,0,0)');
          return gradient;
        },
        fill: true,
        tension: 0.2,
        pointRadius: chartHistory.length <= 15 ? 4 : 0,
        pointHoverRadius: 6,
        pointBackgroundColor: lineColor,
        pointBorderColor: '#fff',
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (item) => `현재가: ${parseFloat(item.parsed.y).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} ${selectedTicker === 'BTC-USD' || selectedTicker.includes('=F') || selectedTicker === 'NVDA' || selectedTicker === 'GOOGL' || selectedTicker === 'TSLA' || selectedTicker === 'AMZN' ? 'USD' : (selectedTicker.includes('KRW') ? 'KRW' : (selectedTicker === 'FNG' ? '포인트' : ''))}`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      }
    }
  };

  return (
    <div className="app-container">
      {/* 헤더 섹션 */}
      <header className="header-section glass-panel">
        <div className="brand-logo">
          <BarChart3 size={28} className="text-accent-blue" style={{ color: 'var(--accent-blue)' }} />
          <h1>GLOBAL MARKET PULSE</h1>
        </div>
        <div className="header-controls">
          {/* 개별/통합 탭 토글 */}
          <div className="view-mode-tabs">
            <button 
              className={`view-mode-btn ${viewMode === 'individual' ? 'active' : ''}`}
              onClick={() => setViewMode('individual')}
            >
              <DollarSign size={15} />
              개별 지표
            </button>
            <button 
              className={`view-mode-btn ${viewMode === 'comparison' ? 'active' : ''}`}
              onClick={() => setViewMode('comparison')}
            >
              <TrendingUp size={15} />
              통합 비교
            </button>
          </div>
          
          <div className="update-time">
            최종 갱신: {formattedUpdateTime}
          </div>
          <button 
            className="btn-secondary" 
            onClick={handleRefresh} 
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "pulsing" : ""} />
            {refreshing ? "수집 중..." : "지금 갱신"}
          </button>
          <button 
            className="btn-secondary" 
            onClick={handlePlayAlarm} 
            disabled={playingAlarm}
          >
            <Volume2 size={16} />
            {playingAlarm ? "알람 재생 중..." : "브리핑 알람 듣기"}
          </button>
          <button 
            className="btn-primary" 
            onClick={handleSendEmail} 
            disabled={sendingEmail}
          >
            <Mail size={16} />
            {sendingEmail ? "발송 중..." : "보고서 메일 전송"}
          </button>
        </div>
      </header>

      {/* 기간 필터링 컨트롤 */}
      <div className="global-filter-bar glass-panel">
        <div className="filter-description">
          <Calendar size={16} style={{ color: 'var(--text-secondary)' }} />
          <span>분석 기준 기간 설정 :</span>
        </div>
        <div className="period-selectors">
          {['1W', '1M', '3M', '1Y'].map((p) => (
            <button
              key={p}
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* 대시보드 메인 레이아웃 */}
      {viewMode === 'individual' ? (
        <main className="main-layout">
          {/* 좌측 메인 차트 */}
          <section className="chart-container-box glass-panel">
            <div className="chart-header">
              <div className="selected-metric-info">
                <h2>{activeMetric.name} ({selectedTicker})</h2>
                <div className="price-row">
                  <span className="current-price">
                    {parseFloat(activeMetric.current).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}
                  </span>
                  <span className={`price-change ${activeMetric.change >= 0 ? 'up' : 'down'}`}>
                    {activeMetric.change >= 0 ? <TrendingUp size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} /> : <TrendingDown size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />}
                    {activeMetric.change >= 0 ? '+' : ''}{parseFloat(activeMetric.change).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})} ({parseFloat(activeMetric.change_percent).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}%)
                  </span>
                </div>
              </div>
            </div>

            <div className="chart-wrapper">
              <Line data={chartData} options={chartOptions} />
            </div>
          </section>

          {/* 우측 사이드바: 지표 목록 */}
          <section className="sidebar-section">
            <div className="sidebar-header">경제지표 리스트</div>
            
            {/* 카테고리 필터 탭 */}
            <div className="filter-tabs">
              {categories.map((cat) => (
                <button
                  key={cat}
                  className={`tab-btn ${activeCategory === cat ? 'active' : ''}`}
                  onClick={() => {
                    setActiveCategory(cat);
                    const currentList = Object.keys(metrics).filter(t => {
                      if (cat === '전체') return true;
                      return getMappedCategory(metrics[t].category) === cat;
                    });
                    if (currentList.length > 0) {
                      setSelectedTicker(currentList[0]);
                    }
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* 지표 리스트 */}
            <div className="metrics-list glass-panel">
              {filteredTickers.map((ticker) => {
                const metric = metrics[ticker];
                return (
                  <div
                    key={ticker}
                    className={`metric-card ${selectedTicker === ticker ? 'active' : ''}`}
                    onClick={() => setSelectedTicker(ticker)}
                  >
                    <div className="card-top">
                      <div className="metric-title-box">
                        <span className="metric-title">{metric.name}</span>
                        <span className="metric-category">{metric.category}</span>
                      </div>
                      <div className="metric-value-box">
                        <span className="metric-value">
                          {parseFloat(metric.current).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}
                        </span>
                        <div className={`metric-change ${metric.change > 0 ? 'up' : (metric.change < 0 ? 'down' : 'neutral')}`}>
                          {metric.change > 0 ? '+' : ''}{parseFloat(metric.change_percent).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </main>
      ) : (
        <main className="comparison-grid-layout">
          {/* 1. 환율 비교 */}
          <div className="chart-card glass-panel">
            <div className="card-header-box">
              <h3>💵 환율 비교 (원/달러 vs 엔/달러)</h3>
              <p className="card-subtitle">2중 축 그래프 (원/달러 좌축, 엔/달러 우축)</p>
            </div>
            <div className="comparison-chart-wrapper">
              <Line data={exchangeChartData} options={exchangeChartOptions} />
            </div>
          </div>

          {/* 2. 미국 빅테크 */}
          <div className="chart-card glass-panel">
            <div className="card-header-box">
              <h3>💻 미국 주요 빅테크 주가</h3>
              <p className="card-subtitle">엔비디아, 구글, 테슬라, 아마존 (단위: USD)</p>
            </div>
            <div className="comparison-chart-wrapper">
              <Line data={techChartData} options={techChartOptions} />
            </div>
          </div>

          {/* 3. 글로벌 자산 비교 */}
          <div className="chart-card glass-panel">
            <div className="card-header-box">
              <h3>🌍 글로벌 주요 자산 트렌드</h3>
              <p className="card-subtitle">S&P 500, KOSPI, 국제 금 (절대수치 트렌드)</p>
            </div>
            <div className="comparison-chart-wrapper">
              <Line data={globalChartData} options={globalChartOptions} />
            </div>
          </div>

          {/* 4. 한국 ETF */}
          <div className="chart-card glass-panel">
            <div className="card-header-box">
              <h3>📈 한국 관련 ETF 비교</h3>
              <p className="card-subtitle">EWY (좌축) vs KORU 3X 레버리지 (우축)</p>
            </div>
            <div className="comparison-chart-wrapper">
              <Line data={etfChartData} options={etfChartOptions} />
            </div>
          </div>

          {/* 5. 원자재 & 암호화폐 */}
          <div className="chart-card glass-panel">
            <div className="card-header-box">
              <h3>🔥 원자재 및 디지털 자산</h3>
              <p className="card-subtitle">WTI 원유 (좌축) vs 비트코인 (우축)</p>
            </div>
            <div className="comparison-chart-wrapper">
              <Line data={comChartData} options={comChartOptions} />
            </div>
          </div>

          {/* 안내 정보 카드 */}
          <div className="chart-card info-card glass-panel">
            <div className="info-card-content">
              <Info size={32} className="info-icon" style={{ color: 'var(--accent-blue)', marginBottom: '16px' }} />
              <h4>💡 통합 비교 가이드</h4>
              <ul>
                <li>자산 간 스케일 차이가 클 경우 **2중 Y축(Dual Axis)**을 적용하여 트렌드를 비교하였습니다.</li>
                <li>글로벌 자산(S&P 500, KOSPI, 국제 금)은 모두 천 단위 가격을 형성하므로, 직관적인 비교를 위해 **절대 수치** 기준으로 트렌드를 나타냅니다.</li>
                <li>오른쪽 및 왼쪽 레이블 색상이 일치하는 선의 척도를 읽어 해석할 수 있습니다.</li>
              </ul>
            </div>
          </div>
        </main>
      )}

      {/* 토스트 컨테이너 */}
      <div className="toast-container">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.type === 'success' ? 'success' : 'info'}`}>
            {toast.type === 'success' ? <CheckCircle2 size={18} style={{ color: 'var(--color-up)' }} /> : <AlertCircle size={18} style={{ color: 'var(--accent-blue)' }} />}
            <span className="toast-message">{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;

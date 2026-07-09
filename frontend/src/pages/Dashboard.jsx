import { useEffect, useState } from 'react';
import axios from 'axios';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function Dashboard() {
  const [market, setMarket] = useState(null);
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/market`).then(res => setMarket(res.data)).catch(console.error);
    axios.get(`${API_BASE}/portfolio`).then(res => setPortfolio(res.data)).catch(console.error);
  }, []);

  if (!market || !portfolio) {
    return (
      <div>
        <h1 className="text-gradient-green">Dashboard</h1>
        <div className="grid-2" style={{ marginTop: '30px' }}>
          <div className="glass-panel">
            <div className="skeleton skeleton-title"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-chart" style={{ marginTop: '20px' }}></div>
          </div>
          <div className="glass-panel">
            <div className="skeleton skeleton-title"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-text"></div>
          </div>
        </div>
      </div>
    );
  }

  const k_status = market.kospi_diff > 30 ? 'status-success' : market.kospi_diff < -30 ? 'status-danger' : 'status-neutral';
  const n_status = market.nasdaq_diff > 150 ? 'status-success' : market.nasdaq_diff < -150 ? 'status-danger' : 'status-neutral';

  const kospiChartData = market.kospi_history.map((val, i) => ({ value: val, index: i }));
  const nasdaqChartData = market.nasdaq_history.map((val, i) => ({ value: val, index: i }));

  return (
    <div>
      <h1 className="text-gradient-green">Dashboard</h1>
      
      <div className="grid-2" style={{ marginTop: '30px' }}>
        <div className="glass-panel">
          <h3>Market Cycle</h3>
          <div style={{ display: 'flex', gap: '40px', marginTop: '20px' }}>
            <div style={{ flex: 1 }}>
              <div className="text-muted">KOSPI</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{market.kospi_val.toFixed(2)}</div>
              <div className={k_status}>{market.kospi_diff > 0 ? '+' : ''}{market.kospi_diff.toFixed(2)}</div>
              <div style={{ width: '100%', height: '60px', marginTop: '10px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={kospiChartData}>
                    <YAxis domain={['auto', 'auto']} hide />
                    <Area type="monotone" dataKey="value" stroke="#00d4ff" fill="rgba(0, 212, 255, 0.2)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div className="text-muted">NASDAQ</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{market.nasdaq_val.toFixed(2)}</div>
              <div className={n_status}>{market.nasdaq_diff > 0 ? '+' : ''}{market.nasdaq_diff.toFixed(2)}</div>
              <div style={{ width: '100%', height: '60px', marginTop: '10px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={nasdaqChartData}>
                    <YAxis domain={['auto', 'auto']} hide />
                    <Area type="monotone" dataKey="value" stroke="#00ff88" fill="rgba(0, 255, 136, 0.2)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
            {market.kospi_diff < -30 || market.nasdaq_diff < -150 ? 
              <span className="status-danger">📉 시장 공포 구간 - 씨앗을 뿌릴 준비가 되었는가?</span> :
             market.kospi_diff > 30 || market.nasdaq_diff > 150 ? 
              <span className="status-success">📈 시장 낙관 구간 - 수확과 현금 확보를 고려할 때인가?</span> :
              <span className="status-neutral">➖ 중립 구간 - 인내하며 관찰할 시기</span>}
          </div>
        </div>

        <div className="glass-panel">
          <h3>Portfolio Risk</h3>
          <div style={{ marginTop: '20px' }}>
            <div style={{ marginBottom: '10px' }}><span className="text-muted">Name:</span> {portfolio.name}</div>
            <div style={{ marginBottom: '10px' }}><span className="text-muted">Positions:</span> {portfolio.positions.length} / 7 
              {portfolio.positions.length >= 7 ? <span className="status-danger" style={{marginLeft: '10px'}}>Too Concentrated</span> : <span className="status-success" style={{marginLeft: '10px'}}>Optimal</span>}
            </div>
            <div style={{ marginBottom: '10px' }}><span className="text-muted">Target Cash:</span> {(portfolio.target_cash_pct * 100).toFixed(0)}%</div>
            <div style={{ marginBottom: '10px' }}>
              <span className="text-muted">Total Value:</span> <span className="text-gradient-green" style={{fontSize: '1.5rem', fontWeight: 'bold'}}>${portfolio.total_value.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

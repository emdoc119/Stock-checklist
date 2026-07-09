import { useEffect, useState } from 'react';
import axios from 'axios';
import { AreaChart, Area, ResponsiveContainer, YAxis, Tooltip } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

const ChartCard = ({ title, data, valueFormat = (v) => v.toFixed(2), color = "#00d4ff" }) => {
  if (!data || !data.current) return <div className="glass-panel skeleton"><div className="skeleton-chart"></div></div>;
  
  const history = data.history || [];
  const current = data.current;
  const prev = history.length > 1 ? history[history.length - 2].value : current;
  const diff = current - prev;
  const diffPct = (diff / prev) * 100;
  
  const isUp = diff >= 0;
  const statusColor = isUp ? "var(--neon-green)" : "var(--neon-red)";

  return (
    <div className="glass-panel">
      <h3 className="text-muted">{title}</h3>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
        <h2 style={{ margin: 0, fontSize: '2rem' }}>{valueFormat(current)}</h2>
        <span style={{ color: statusColor, fontWeight: 'bold' }}>
          {isUp ? '▲' : '▼'} {Math.abs(diff).toFixed(2)} ({Math.abs(diffPct).toFixed(2)}%)
        </span>
      </div>
      <div style={{ height: '100px', marginTop: '15px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history}>
            <defs>
              <linearGradient id={`color-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={color} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <YAxis domain={['auto', 'auto']} hide />
            <Tooltip contentStyle={{ background: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '8px' }} />
            <Area type="monotone" dataKey="value" stroke={color} fillOpacity={1} fill={`url(#color-${title})`} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default function MacroDashboard() {
  const [indices, setIndices] = useState(null);
  const [rates, setRates] = useState(null);
  const [commodities, setCommodities] = useState(null);
  const [fearGreed, setFearGreed] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/macro/indices`).then(res => setIndices(res.data));
    axios.get(`${API_BASE}/macro/rates`).then(res => setRates(res.data));
    axios.get(`${API_BASE}/macro/commodities`).then(res => setCommodities(res.data));
    axios.get(`${API_BASE}/macro/fear-greed`).then(res => setFearGreed(res.data));
  }, []);

  return (
    <div className="main-content">
      <h1 className="text-gradient-green">Macro Dashboard</h1>
      <p className="text-muted" style={{ marginBottom: '30px' }}>Global market indicators and sentiments</p>
      
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 className="text-muted">Fear & Greed Index</h3>
            {fearGreed ? (
              <h2 style={{ fontSize: '3rem', margin: 0, color: fearGreed.score < 30 ? 'var(--neon-red)' : fearGreed.score > 70 ? 'var(--neon-green)' : 'var(--neon-blue)' }}>
                {fearGreed.score}
              </h2>
            ) : (
              <div className="skeleton-title" style={{ height: '3rem' }}></div>
            )}
          </div>
          <div style={{ textAlign: 'right' }}>
            <p className="text-muted">0 = Extreme Fear</p>
            <p className="text-muted">100 = Extreme Greed</p>
          </div>
        </div>
      </div>

      <h2>Global Indices</h2>
      <div className="grid-2" style={{ marginBottom: '40px' }}>
        <ChartCard title="S&P 500" data={indices?.SP500} color="#00ff88" />
        <ChartCard title="NASDAQ" data={indices?.NASDAQ} color="#00d4ff" />
        <ChartCard title="KOSPI" data={indices?.KOSPI} color="#ff3366" />
        <ChartCard title="Samsung Elec." data={indices?.SAMSUNG} color="#00d4ff" valueFormat={(v) => `₩${v.toLocaleString()}`} />
      </div>

      <h2>Rates & Currency</h2>
      <div className="grid-2" style={{ marginBottom: '40px' }}>
        <ChartCard title="Dollar Index (DXY)" data={rates?.DXY} color="#aa00ff" />
        <ChartCard title="US 10Y Treasury" data={rates?.US10Y} color="#ffaa00" valueFormat={(v) => `${v.toFixed(3)}%`} />
        <ChartCard title="USD/KRW" data={rates?.KRW_USD} color="#00ffaa" valueFormat={(v) => `₩${v.toLocaleString()}`} />
      </div>

      <h2>Commodities & Crypto</h2>
      <div className="grid-2" style={{ marginBottom: '40px' }}>
        <ChartCard title="Gold" data={commodities?.GOLD} color="#ffd700" />
        <ChartCard title="WTI Crude Oil" data={commodities?.WTI} color="#ff3333" />
        <ChartCard title="Bitcoin" data={commodities?.BTC} color="#f7931a" valueFormat={(v) => `$${v.toLocaleString()}`} />
      </div>
    </div>
  );
}

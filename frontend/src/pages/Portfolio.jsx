import { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const API_BASE = 'http://localhost:8000/api';
const COLORS = ['#00ff88', '#00d4ff', '#ff3366', '#ffaa00', '#aa00ff', '#00ffaa', '#ff0055'];

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/portfolio`).then(res => setPortfolio(res.data)).catch(console.error);
  }, []);

  if (!portfolio) {
    return (
      <div>
        <h1 className="text-gradient-green">Portfolio</h1>
        <div className="grid-2" style={{ marginTop: '30px' }}>
          <div className="glass-panel"><div className="skeleton skeleton-chart"></div></div>
          <div className="glass-panel"><div className="skeleton skeleton-chart"></div></div>
        </div>
      </div>
    );
  }

  const data = portfolio.positions.map(p => ({ name: p.symbol, value: p.current_value }));
  const totalInvested = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div>
      <h1 className="text-gradient-green">Portfolio</h1>
      
      <div className="grid-2" style={{ marginTop: '30px' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <h3>Allocation</h3>
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data} cx="50%" cy="50%" innerRadius={70} outerRadius={90} paddingAngle={5} dataKey="value" stroke="none">
                  {data.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel">
          <h3>Positions</h3>
          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', marginTop: '20px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: '10px' }}>Symbol</th>
                <th style={{ padding: '10px' }}>Value</th>
                <th style={{ padding: '10px', width: '40%' }}>Weight</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.map((p, index) => {
                const weight = totalInvested > 0 ? (p.current_value / totalInvested) * 100 : 0;
                const color = COLORS[index % COLORS.length];
                return (
                  <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '10px', fontWeight: 'bold' }}>
                      <span style={{ display: 'inline-block', width: '10px', height: '10px', backgroundColor: color, borderRadius: '50%', marginRight: '8px' }}></span>
                      {p.symbol}
                    </td>
                    <td style={{ padding: '10px' }} className="text-gradient-green">${p.current_value.toFixed(2)}</td>
                    <td style={{ padding: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div className="progress-bg">
                          <div className="progress-fill" style={{ width: `${weight}%`, background: color }}></div>
                        </div>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{weight.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function StockEvaluation() {
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [evalData, setEvalData] = useState(null);
  const [stockInfo, setStockInfo] = useState(null);
  const [loadingInfo, setLoadingInfo] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/securities`).then(res => {
      setSymbols(res.data.map(s => s.symbol));
      if (res.data.length > 0) setSelectedSymbol(res.data[0].symbol);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      setLoadingInfo(true);
      axios.get(`${API_BASE}/evaluation/${selectedSymbol}`).then(res => {
        if (Object.keys(res.data).length === 0) {
          setEvalData({
            structural_growth_score: 3, bottleneck_score: 3, valuation_score: 3,
            financial_safety_score: 3, momentum_score: 3, sentiment_score: 3, thesis_text: ''
          });
        } else {
          setEvalData(res.data);
        }
      });
      axios.get(`${API_BASE}/info/${selectedSymbol}`).then(res => {
        setStockInfo(res.data);
        setLoadingInfo(false);
      }).catch(() => setLoadingInfo(false));
    }
  }, [selectedSymbol]);

  const handleChange = (e) => {
    const value = e.target.type === 'range' ? parseInt(e.target.value) : e.target.value;
    setEvalData({ ...evalData, [e.target.name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post(`${API_BASE}/evaluation/${selectedSymbol}`, evalData).then(res => {
      setEvalData({ ...evalData, farmer_score: res.data.farmer_score });
      alert('Evaluation saved!');
    });
  };

  const chartData = evalData ? [
    { subject: 'Growth', A: evalData.structural_growth_score, fullMark: 5 },
    { subject: 'Bottleneck', A: evalData.bottleneck_score, fullMark: 5 },
    { subject: 'Valuation', A: evalData.valuation_score, fullMark: 5 },
    { subject: 'Safety', A: evalData.financial_safety_score, fullMark: 5 },
    { subject: 'Momentum', A: evalData.momentum_score, fullMark: 5 },
    { subject: 'Sentiment', A: evalData.sentiment_score, fullMark: 5 },
  ] : [];

  const formatNumber = (num) => {
    if (!num) return 'N/A';
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    return num.toLocaleString();
  };

  return (
    <div>
      <h1 className="text-gradient-green">Stock Evaluation</h1>
      
      <div className="glass-panel" style={{ marginTop: '30px', marginBottom: '30px', display: 'flex', gap: '20px', alignItems: 'center' }}>
        <select className="input-glass" style={{ width: '200px' }} value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)}>
          {symbols.map(s => <option key={s} value={s} style={{background: '#0f1115'}}>{s}</option>)}
        </select>
        
        {loadingInfo ? (
           <div className="skeleton skeleton-text" style={{ width: '300px', margin: 0 }}></div>
        ) : stockInfo ? (
          <div style={{ display: 'flex', gap: '20px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            <div><strong>Sector:</strong> {stockInfo.sector || 'N/A'}</div>
            <div><strong>Mkt Cap:</strong> {formatNumber(stockInfo.marketCap)}</div>
            <div><strong>P/E:</strong> {stockInfo.forwardPE ? stockInfo.forwardPE.toFixed(2) : 'N/A'}</div>
            <div><strong>52W High:</strong> {stockInfo.fiftyTwoWeekHigh ? '$'+stockInfo.fiftyTwoWeekHigh.toFixed(2) : 'N/A'}</div>
            <div><strong>Div Yield:</strong> {stockInfo.dividendYield ? (stockInfo.dividendYield * 100).toFixed(2) + '%' : 'N/A'}</div>
          </div>
        ) : null}
      </div>

      {evalData ? (
        <div className="grid-2">
          <div className="glass-panel">
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {['structural_growth_score', 'bottleneck_score', 'valuation_score', 'financial_safety_score', 'momentum_score', 'sentiment_score'].map((field) => (
                <div key={field}>
                  <label className="text-muted" style={{ display: 'block', marginBottom: '5px' }}>
                    {field.replace(/_score/g, '').replace(/_/g, ' ').toUpperCase()} (1-5)
                  </label>
                  <input type="range" name={field} min="1" max="5" value={evalData[field]} onChange={handleChange} style={{ width: '100%' }} />
                  <span style={{ float: 'right' }}>{evalData[field]}</span>
                </div>
              ))}
              <div>
                <label className="text-muted" style={{ display: 'block', marginBottom: '5px' }}>Thesis</label>
                <textarea className="input-glass" name="thesis_text" value={evalData.thesis_text || ''} onChange={handleChange} rows="3"></textarea>
              </div>
              <button type="submit" className="btn-primary">Save Evaluation</button>
            </form>
          </div>

          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <h3 style={{ margin: 0 }}>Farmer Grade</h3>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', margin: '10px 0', textShadow: '0 0 20px rgba(0,255,136,0.5)' }} className="text-gradient-green">
              {evalData.farmer_score ? evalData.farmer_score.toFixed(1) : '-'}
            </div>
            {evalData.farmer_score >= 80 && <span style={{ background: 'rgba(0,255,136,0.2)', padding: '5px 15px', borderRadius: '20px', color: 'var(--neon-green)', fontWeight: 'bold', border: '1px solid var(--neon-green)' }}>EXCELLENT (A)</span>}
            {evalData.farmer_score >= 60 && evalData.farmer_score < 80 && <span style={{ background: 'rgba(0,212,255,0.2)', padding: '5px 15px', borderRadius: '20px', color: 'var(--neon-blue)', fontWeight: 'bold', border: '1px solid var(--neon-blue)' }}>GOOD (B)</span>}
            {evalData.farmer_score > 0 && evalData.farmer_score < 60 && <span style={{ background: 'rgba(255,51,102,0.2)', padding: '5px 15px', borderRadius: '20px', color: 'var(--neon-red)', fontWeight: 'bold', border: '1px solid var(--neon-red)' }}>POOR (C)</span>}

            <div style={{ width: '100%', height: '350px', marginTop: '20px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                  <PolarGrid stroke="rgba(255,255,255,0.2)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ba3af' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 5]} tick={false} axisLine={false} />
                  <Radar name="Score" dataKey="A" stroke="#00ff88" fill="#00d4ff" fillOpacity={0.4} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid-2">
          <div className="glass-panel"><div className="skeleton skeleton-chart"></div></div>
          <div className="glass-panel"><div className="skeleton skeleton-chart"></div></div>
        </div>
      )}
    </div>
  );
}

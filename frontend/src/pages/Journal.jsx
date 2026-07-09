import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function Journal() {
  const [journals, setJournals] = useState([]);
  const [formData, setFormData] = useState({ symbol: '', side: 'BUY', hypothesis_text: '', checks: {} });

  const fetchJournals = () => axios.get(`${API_BASE}/journals`).then(res => setJournals(res.data)).catch(console.error);

  useEffect(() => {
    fetchJournals();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Determine if passed
    let passed = false;
    if (formData.side === 'BUY') {
      passed = formData.checks?.q1 && formData.checks?.q2 && formData.checks?.q3 && formData.checks?.q4;
    } else {
      passed = formData.checks?.q1 || formData.checks?.q2 || formData.checks?.q3;
    }
    
    const payload = { ...formData, checklist_passed: passed };

    axios.post(`${API_BASE}/journals`, payload).then(() => {
      alert('Journal saved!');
      setFormData({ symbol: '', side: 'BUY', hypothesis_text: '', checks: {} });
      fetchJournals();
    });
  };

  return (
    <div>
      <h1 className="text-gradient-green">Reminders & Journal</h1>
      
      <div className="grid-2" style={{ marginTop: '30px' }}>
        <div className="glass-panel">
          <h3>농부의 3원칙 (Reminders)</h3>
          <ul style={{ lineHeight: '1.8', marginTop: '20px', color: 'var(--text-muted)' }}>
            <li><span className="status-success">✔️</span> <b>구조적 성장:</b> 이 기업은 10년 뒤에도 살아남아 성장할 수 있는가?</li>
            <li><span className="status-success">✔️</span> <b>리스크 대비:</b> 전체 자산의 일정 비율(예: 30%)은 항상 현금인가?</li>
            <li><span className="status-success">✔️</span> <b>인내심:</b> 시장의 공포에 사서 탐욕에 팔 준비가 되었는가?</li>
          </ul>

          <h3 style={{ marginTop: '30px' }}>New Trade Journal</h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '15px' }}>
            <input className="input-glass" placeholder="Symbol (e.g. AAPL)" value={formData.symbol} onChange={e => setFormData({...formData, symbol: e.target.value})} required />
            <select className="input-glass" value={formData.side} onChange={e => setFormData({...formData, side: e.target.value})}>
              <option value="BUY" style={{background: '#0f1115'}}>BUY</option>
              <option value="SELL" style={{background: '#0f1115'}}>SELL</option>
            </select>
            <textarea className="input-glass" placeholder="Hypothesis" value={formData.hypothesis_text} onChange={e => setFormData({...formData, hypothesis_text: e.target.value})} required rows="3"></textarea>
            
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: 'var(--text-muted)' }}>{formData.side === 'BUY' ? '매수 체크리스트' : '매도 체크리스트'}</h4>
              {formData.side === 'BUY' ? (
                <>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q1 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q1: e.target.checked}})} />
                    이 기업은 구조적 성장 궤도에 있는가?
                  </label>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q2 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q2: e.target.checked}})} />
                    현재 시장은 공포 구간인가? (VIX {'>'} 25)
                  </label>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q3 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q3: e.target.checked}})} />
                    현금 비중이 목표치 이상 확보되어 있는가?
                  </label>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q4 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q4: e.target.checked}})} />
                    최대 보유 종목 수(7개) 이하인가?
                  </label>
                </>
              ) : (
                <>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q1 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q1: e.target.checked}})} />
                    투자 논리(Thesis)가 훼손되었는가?
                  </label>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q2 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q2: e.target.checked}})} />
                    현재 시장은 탐욕 구간인가? (탐욕지수 {'>'} 75)
                  </label>
                  <label style={{ display: 'flex', gap: '10px', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={formData.checks?.q3 || false} onChange={e => setFormData({...formData, checks: {...formData.checks, q3: e.target.checked}})} />
                    목표 수익률에 도달했는가?
                  </label>
                </>
              )}
            </div>

            <button type="submit" className="btn-primary" disabled={
              formData.side === 'BUY' ? !(formData.checks?.q1 && formData.checks?.q2 && formData.checks?.q3 && formData.checks?.q4) :
              !(formData.checks?.q1 || formData.checks?.q2 || formData.checks?.q3)
            }>Record Trade</button>
          </form>
        </div>

        <div className="glass-panel" style={{ maxHeight: '600px', overflowY: 'auto' }}>
          <h3>History</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
            {journals.map(j => (
              <div key={j.id} style={{ padding: '15px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', borderLeft: `3px solid ${j.side === 'BUY' ? 'var(--neon-green)' : 'var(--neon-red)'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <strong style={{ fontSize: '1.2rem' }}>{j.symbol} <span className={j.side === 'BUY' ? 'status-success' : 'status-danger'}>{j.side}</span></strong>
                  <span className="text-muted" style={{ fontSize: '0.8rem' }}>{new Date(j.created_at).toLocaleString()}</span>
                </div>
                <p className="text-muted" style={{ margin: '0 0 10px 0' }}>{j.hypothesis_text}</p>
                {j.checklist_passed ? <span className="status-success" style={{ fontSize: '0.9rem' }}>Checklist Passed ✔️</span> : <span className="status-danger" style={{ fontSize: '0.9rem' }}>Checklist Failed ❌</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

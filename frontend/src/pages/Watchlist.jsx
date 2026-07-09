import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [history, setHistory] = useState([]);
  const [newItem, setNewItem] = useState({ symbol: '', name: '', alert_threshold_pct: 5.0 });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [wlRes, histRes] = await Promise.all([
        axios.get(`${API_BASE}/watchlist`),
        axios.get(`${API_BASE}/alerts/history`)
      ]);
      setWatchlist(wlRes.data);
      setHistory(histRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/watchlist`, newItem);
      setNewItem({ symbol: '', name: '', alert_threshold_pct: 5.0 });
      fetchData();
    } catch (e) {
      alert('Failed to add item');
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API_BASE}/watchlist/${id}`);
      fetchData();
    } catch (e) {
      alert('Failed to delete item');
    }
  };

  return (
    <div className="main-content">
      <h1 className="text-gradient-green">Watchlist & Alerts</h1>
      <p className="text-muted" style={{ marginBottom: '30px' }}>Monitor stocks and receive Telegram alerts</p>
      
      <div className="grid-2">
        <div className="glass-panel">
          <h2>Your Watchlist</h2>
          
          <form onSubmit={handleAdd} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <input 
              type="text" className="input-glass" placeholder="Symbol (e.g. AAPL)" required
              value={newItem.symbol} onChange={e => setNewItem({...newItem, symbol: e.target.value.toUpperCase()})}
            />
            <select 
              className="input-glass" style={{ width: '100px' }}
              value={newItem.alert_threshold_pct} onChange={e => setNewItem({...newItem, alert_threshold_pct: parseFloat(e.target.value)})}
            >
              <option value={5.0}>5%</option>
              <option value={10.0}>10%</option>
            </select>
            <button type="submit" className="btn-primary">Add</button>
          </form>

          {watchlist.length === 0 ? (
            <p className="text-muted">No items in watchlist.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {watchlist.map(item => (
                <li key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border-glass)' }}>
                  <span>
                    <strong>{item.symbol}</strong> ({item.alert_threshold_pct}% Alert)
                  </span>
                  <button 
                    onClick={() => handleDelete(item.id)}
                    style={{ background: 'transparent', border: '1px solid var(--neon-red)', color: 'var(--neon-red)', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="glass-panel">
          <h2>Alert History</h2>
          {history.length === 0 ? (
            <p className="text-muted">No recent alerts.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {history.map(log => (
                <li key={log.id} style={{ padding: '10px', borderBottom: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>{log.symbol}</strong>
                    <span style={{ color: log.change_pct > 0 ? 'var(--neon-green)' : 'var(--neon-red)' }}>
                      {log.change_pct > 0 ? '▲' : '▼'} {Math.abs(log.change_pct).toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-muted" style={{ fontSize: '0.85em', marginTop: '5px' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

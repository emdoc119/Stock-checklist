import { useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function Settings() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSync = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await axios.get(`${API_BASE}/broker/sync`);
      setMessage(res.data.message);
    } catch (err) {
      setMessage('Failed to sync. Make sure your API keys are in the .env file and valid.');
    }
    setLoading(false);
  };

  return (
    <div className="main-content">
      <h1 className="text-gradient-green">Settings & Integration</h1>
      <p className="text-muted" style={{ marginBottom: '30px' }}>Manage your broker and alert settings</p>
      
      <div className="grid-2">
        <div className="glass-panel">
          <h2>Broker Integration</h2>
          <p className="text-muted">Currently, API keys must be set in the `.env` file for security reasons.</p>
          
          <ul style={{ color: 'var(--text-muted)' }}>
            <li><code>KIS_APP_KEY</code> / <code>KIS_APP_SECRET</code></li>
            <li><code>TOSS_API_KEY</code> / <code>TOSS_SECRET_KEY</code></li>
          </ul>

          <button className="btn-primary" onClick={handleSync} disabled={loading} style={{ marginTop: '20px' }}>
            {loading ? 'Syncing...' : 'Sync Portfolio with Broker'}
          </button>
          
          {message && <p style={{ marginTop: '15px', color: 'var(--neon-blue)' }}>{message}</p>}
        </div>

        <div className="glass-panel">
          <h2>Telegram Alerts</h2>
          <p className="text-muted">Alert keys must also be in `.env`.</p>
          
          <ul style={{ color: 'var(--text-muted)' }}>
            <li><code>TELEGRAM_BOT_TOKEN</code></li>
            <li><code>TELEGRAM_CHAT_ID</code></li>
          </ul>
          
          <p className="text-muted" style={{ fontSize: '0.9em' }}>* Use @BotFather on Telegram to create a bot.</p>
        </div>
      </div>
    </div>
  );
}

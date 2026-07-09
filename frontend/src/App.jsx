import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Briefcase, BookOpen, Globe, Settings as SettingsIcon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import MacroDashboard from './pages/MacroDashboard';
import StockEvaluation from './pages/StockEvaluation';
import Portfolio from './pages/Portfolio';
import Journal from './pages/Journal';
import Settings from './pages/Settings';
import Watchlist from './pages/Watchlist';
import { Bell } from 'lucide-react';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <aside className="sidebar">
          <h2 className="text-gradient-green" style={{ marginBottom: '30px' }}>🌾 Farmer OS</h2>
          
          <NavLink to="/" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={20} /> Dashboard
          </NavLink>

          <NavLink to="/macro" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Globe size={20} /> Macro Dashboard
          </NavLink>
          
          <NavLink to="/evaluation" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <TrendingUp size={20} /> Stock Evaluation
          </NavLink>

          <NavLink to="/watchlist" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Bell size={20} /> Watchlist & Alerts
          </NavLink>
          
          <NavLink to="/portfolio" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Briefcase size={20} /> Portfolio
          </NavLink>
          
          <NavLink to="/journal" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <BookOpen size={20} /> Reminders & Journal
          </NavLink>

          <NavLink to="/settings" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <SettingsIcon size={20} /> Settings
          </NavLink>
        </aside>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/macro" element={<MacroDashboard />} />
            <Route path="/evaluation" element={<StockEvaluation />} />
            <Route path="/watchlist" element={<Watchlist />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Briefcase, BookOpen } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import StockEvaluation from './pages/StockEvaluation';
import Portfolio from './pages/Portfolio';
import Journal from './pages/Journal';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <aside className="sidebar">
          <h2 className="text-gradient-green" style={{ marginBottom: '30px' }}>🌾 Farmer OS</h2>
          
          <NavLink to="/" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={20} /> Dashboard
          </NavLink>
          
          <NavLink to="/evaluation" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <TrendingUp size={20} /> Stock Evaluation
          </NavLink>
          
          <NavLink to="/portfolio" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Briefcase size={20} /> Portfolio
          </NavLink>
          
          <NavLink to="/journal" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <BookOpen size={20} /> Reminders & Journal
          </NavLink>
        </aside>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/evaluation" element={<StockEvaluation />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/journal" element={<Journal />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

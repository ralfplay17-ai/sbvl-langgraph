import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Backtest } from './pages/Backtest'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface">
        {/* Navbar */}
        <nav className="bg-card border-b border-border px-6 py-4 flex items-center gap-6">
          <span className="text-white font-extrabold text-lg tracking-tight">
            BVL Multiagente
          </span>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                isActive
                  ? 'bg-[#1a3a5f] text-white border border-[#4aa3ff]'
                  : 'text-[#c7c7c2] hover:text-white'
              }`
            }
          >
            Análisis en Vivo
          </NavLink>
          <NavLink
            to="/backtest"
            className={({ isActive }) =>
              `px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                isActive
                  ? 'bg-[#1a3a5f] text-white border border-[#4aa3ff]'
                  : 'text-[#c7c7c2] hover:text-white'
              }`
            }
          >
            Backtesting
          </NavLink>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/backtest" element={<Backtest />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

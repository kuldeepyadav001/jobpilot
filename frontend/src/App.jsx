import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  LayoutDashboard, Briefcase, Kanban as KanbanIcon, FileText, Mail, BarChart2,
  Settings as SettingsIcon, Search, Bell, User, HeartPulse, GraduationCap, Sun, Moon,
} from 'lucide-react'

import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Feed from './pages/Feed'
import Kanban from './pages/Kanban'
import Resumes from './pages/Resumes'
import Responses from './pages/Responses'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import Monitoring from './pages/Monitoring'

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: false } }
})

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/feed', icon: Briefcase, label: 'Job Feed' },
  { to: '/kanban', icon: KanbanIcon, label: 'Pipeline' },
  { to: '/resumes', icon: FileText, label: 'Resumes' },
  { to: '/responses', icon: Mail, label: 'Responses' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/monitoring', icon: HeartPulse, label: 'Monitoring' },
  { to: '/settings', icon: SettingsIcon, label: 'Settings' },
]

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    if (typeof window === 'undefined') return false
    const saved = localStorage.getItem('jobpilot-theme')
    if (saved) return saved === 'dark'
    return false
  })
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('jobpilot-theme', dark ? 'dark' : 'light')
  }, [dark])
  return [dark, setDark]
}

function BrandMark() {
  return (
    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-teal-400 flex items-center justify-center shadow-lg shadow-violet-500/30">
      <GraduationCap className="w-5 h-5 text-white" />
    </div>
  )
}

function Layout({ children, dark, setDark }) {
  const [query, setQuery] = useState('')
  const loc = useLocation()

  return (
    <div className="flex h-screen bg-bg text-ink overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-line flex flex-col shrink-0">
        <Link to="/" className="h-20 flex items-center px-6 gap-3">
          <BrandMark />
          <div>
            <h1 className="text-lg font-black tracking-tight">JobPilot</h1>
            <p className="text-[10px] font-semibold text-ink-faint -mt-0.5">Automated Job Hunter</p>
          </div>
        </Link>

        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 text-[10px] font-extrabold text-ink-faint uppercase tracking-wider mb-2">Menu</p>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-brand text-white shadow-lg shadow-brand/30'
                    : 'text-ink-soft hover:bg-surface2 hover:text-ink'
                }`
              }
            >
              <item.icon className="w-[18px] h-[18px]" strokeWidth={2.2} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-line">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-teal-400 flex items-center justify-center text-white font-black text-xs shadow-sm">JP</div>
            <div className="min-w-0">
              <p className="text-xs font-extrabold truncate">Job Hunter</p>
              <p className="text-[10px] text-ink-faint font-semibold">Self-hosted</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-20 bg-surface border-b border-line flex items-center justify-between px-6 shrink-0">
          <div className="relative w-80 max-w-full">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-faint" />
            <input
              type="text"
              placeholder="Search jobs, skills, companies..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && query.trim()) { window.location.hash = `#/feed?q=${encodeURIComponent(query.trim())}`; } }}
              className="w-full bg-surface2 border border-line rounded-full py-2.5 pl-10 pr-4 text-xs font-medium text-ink placeholder:text-ink-faint focus:border-brand focus:ring-2 focus:ring-brand-soft outline-none transition"
            />
          </div>

          <div className="flex items-center gap-4">
            {/* Dark mode toggle */}
            <div className="flex items-center gap-2 bg-surface2 border border-line rounded-full px-3 py-1.5">
              {dark ? <Moon className="w-4 h-4 text-brand" /> : <Sun className="w-4 h-4 text-ink-soft" />}
              <button
                onClick={() => setDark(!dark)}
                className={`relative w-10 h-5 rounded-full transition-colors ${dark ? 'bg-brand' : 'bg-ink-faint/40'}`}
                title="Toggle theme"
              >
                <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all ${dark ? 'right-0.5' : 'left-0.5'}`} />
              </button>
              <span className="text-[11px] font-bold text-ink-soft">{dark ? 'Dark' : 'Light'}</span>
            </div>

            {/* Notifications */}
            <button className="relative p-2.5 rounded-xl text-ink-soft hover:bg-surface2 transition">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full border-2 border-surface"></span>
            </button>

            {/* User */}
            <div className="flex items-center gap-3 pl-4 border-l border-line">
              <div className="text-right hidden md:block">
                <p className="text-xs font-extrabold">Job Hunter</p>
                <p className="text-[10px] text-ink-faint font-semibold">Admin</p>
              </div>
              <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-teal-400 text-white rounded-full flex items-center justify-center font-bold text-sm shadow-sm">
                <User className="w-5 h-5" />
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">{children}</main>
      </div>
    </div>
  )
}

export default function App() {
  const [dark, setDark] = useDarkMode()
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/*" element={
            <Layout dark={dark} setDark={setDark}>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/feed" element={<Feed />} />
                <Route path="/kanban" element={<Kanban />} />
                <Route path="/resumes" element={<Resumes />} />
                <Route path="/responses" element={<Responses />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Dashboard />} />
              </Routes>
            </Layout>
          } />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

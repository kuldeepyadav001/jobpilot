import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  LayoutDashboard, Briefcase, Kanban as KanbanIcon, FileText, Mail, BarChart2,
  Settings as SettingsIcon, Search, Bell, User, HeartPulse, Compass, Sun, Moon,
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
  { to: '/monitoring', icon: HeartPulse, label: 'Health' },
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
    <div className="w-8 h-8 rounded-lg bg-brand text-white flex items-center justify-center">
      <Compass className="w-[18px] h-[18px]" strokeWidth={2.2} />
    </div>
  )
}

function Layout({ children, dark, setDark }) {
  const [query, setQuery] = useState('')
  const loc = useLocation()

  return (
    <div className="flex h-screen bg-bg text-ink overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 bg-surface border-r border-line flex flex-col shrink-0">
        <Link to="/" className="h-16 flex items-center px-5 gap-2.5 border-b border-line">
          <BrandMark />
          <div className="leading-tight">
            <h1 className="text-[15px] font-bold tracking-tight">JobPilot</h1>
            <p className="text-[11px] font-medium text-ink-faint">Automated Job Hunter</p>
          </div>
        </Link>

        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          <p className="px-3 pt-1 pb-2 text-[10px] font-semibold text-ink-faint uppercase tracking-wider">Menu</p>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-soft text-brand-strong'
                    : 'text-ink-soft hover:bg-surface2 hover:text-ink'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className="w-[18px] h-[18px]" strokeWidth={isActive ? 2.4 : 2} />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-line">
          <div className="flex items-center gap-3 px-2 py-1.5">
            <div className="w-8 h-8 rounded-lg bg-brand-soft text-brand-strong flex items-center justify-center font-bold text-[11px]">
              JP
            </div>
            <div className="min-w-0">
              <p className="text-[13px] font-semibold truncate text-ink">Self-hosted</p>
              <p className="text-[11px] text-ink-faint">Local &amp; private</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 bg-surface border-b border-line flex items-center justify-between gap-4 px-6 shrink-0">
          <div className="relative w-72 max-w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
            <input
              type="text"
              placeholder="Search jobs, skills, companies…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && query.trim()) { window.location.hash = `#/feed?q=${encodeURIComponent(query.trim())}`; } }}
              className="w-full bg-surface2 border border-line rounded-lg py-2 pl-9 pr-3 text-[13px] font-medium text-ink placeholder:text-ink-faint focus:border-brand focus:ring-2 focus:ring-brand-soft outline-none transition"
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Theme toggle */}
            <button
              onClick={() => setDark(!dark)}
              className="p-2 rounded-lg text-ink-soft hover:bg-surface2 hover:text-ink transition-colors"
              title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
              aria-label="Toggle theme"
            >
              {dark ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
            </button>

            {/* Notifications */}
            <button className="relative p-2 rounded-lg text-ink-soft hover:bg-surface2 hover:text-ink transition-colors" aria-label="Notifications">
              <Bell className="w-[18px] h-[18px]" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full ring-2 ring-surface"></span>
            </button>

            <div className="w-px h-6 bg-line mx-1"></div>

            {/* User */}
            <div className="flex items-center gap-2.5">
              <div className="text-right hidden sm:block leading-tight">
                <p className="text-[13px] font-semibold text-ink">Job Hunter</p>
                <p className="text-[11px] text-ink-faint">Admin</p>
              </div>
              <div className="w-8 h-8 rounded-lg bg-brand-soft text-brand-strong flex items-center justify-center">
                <User className="w-4 h-4" />
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">{children}</main>
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

import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LayoutDashboard, Briefcase, Kanban as KanbanIcon, FileText, Mail, BarChart2, Settings as SettingsIcon, Search, Bell, User, HeartPulse } from 'lucide-react'

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
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/feed', icon: Briefcase, label: 'Job Feed' },
  { to: '/kanban', icon: KanbanIcon, label: 'Pipeline' },
  { to: '/resumes', icon: FileText, label: 'Resumes' },
  { to: '/responses', icon: Mail, label: 'Responses' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/monitoring', icon: HeartPulse, label: 'Monitoring' },
  { to: '/settings', icon: SettingsIcon, label: 'Settings' },
]

function Layout({ children }) {
  return (
    <div className="flex h-screen bg-[#F7F8FA] font-sans text-slate-800 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-100 flex flex-col shadow-sm z-10 shrink-0">
        <div className="h-20 flex items-center px-8 border-b border-slate-50">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center mr-3 shadow-md shadow-indigo-200">
            <span className="text-white font-bold text-xl">J</span>
          </div>
          <h1 className="text-xl font-extrabold text-slate-800 tracking-tight">JobPilot</h1>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <p className="px-4 text-[10px] font-extrabold text-slate-400 uppercase tracking-wider mb-3">Main Menu</p>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  isActive 
                    ? 'bg-indigo-50 text-indigo-700 shadow-xs' 
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                }`
              }
            >
              <item.icon className="w-5 h-5" strokeWidth={2.2} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <header className="h-20 bg-white border-b border-slate-100 flex items-center justify-between px-8 shrink-0">
          <div className="relative w-96">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search jobs, skills, companies..." 
              className="w-full bg-[#F7F8FA] border border-slate-100 rounded-full py-2.5 pl-10 pr-4 text-xs font-medium text-slate-700 focus:bg-white focus:border-indigo-300 focus:ring-3 focus:ring-indigo-50 outline-none transition-all"
            />
          </div>
          <div className="flex items-center gap-5">
            <button className="relative p-2 text-slate-400 hover:text-slate-600 transition">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-white"></span>
            </button>
            <div className="flex items-center gap-3 pl-5 border-l border-slate-200">
              <div className="text-right hidden md:block">
                <p className="text-xs font-extrabold text-slate-800">Job Hunter</p>
                <p className="text-[10px] text-slate-400 font-semibold">Admin</p>
              </div>
              <div className="w-10 h-10 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center font-bold text-sm shadow-xs">
                JP
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/feed" element={<Feed />} />
            <Route path="/kanban" element={<Kanban />} />
            <Route path="/resumes" element={<Resumes />} />
            <Route path="/responses" element={<Responses />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
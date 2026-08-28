import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Feed from './pages/Feed'
import Kanban from './pages/Kanban'
import Resumes from './pages/Resumes'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import Responses from './pages/Responses'
const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } }
})

const navItems = [
  { to: '/', label: '📋 Feed' },
  { to: '/kanban', label: '📊 Kanban' },
   { to: '/responses', label: '📩 Responses' },
  { to: '/resumes', label: '📄 Resumes' },
  { to: '/analytics', label: '📈 Analytics' },
  { to: '/settings', label: '⚙️ Settings' },
 
]

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
        <h1 className="text-xl font-bold text-blue-400 mr-8">JobPilot</h1>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `px-3 py-1.5 rounded text-sm font-medium transition ${
                isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Feed />} />
            <Route path="/kanban" element={<Kanban />} />
            <Route path="/responses" element={<Responses />} />
            <Route path="/resumes" element={<Resumes />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchDashboard, triggerPipeline, fetchPipelineStatus, fetchSystemHealth } from '../api/client'
import { Briefcase, CheckCircle, Clock, TrendingUp, ChevronRight, Play, Loader2, Sparkles } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: stats, isError } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard, retry: false })
  const { data: runStatus } = useQuery({ queryKey: ['pipelineStatus'], queryFn: fetchPipelineStatus, refetchInterval: 3000, retry: false })
  const isRunning = runStatus?.running

  // Quick-glance health indicator (green = all good; red = something down).
  const { data: health } = useQuery({ queryKey: ['systemHealth'], queryFn: fetchSystemHealth, refetchInterval: 10000, retry: false })
  const healthOk = [health?.db, health?.ollama, health?.scheduler].every(c => c?.ok !== false)

  const runMutation = useMutation({
    mutationFn: triggerPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelineStatus'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (err) => alert(`Failed to start pipeline: ${err.response?.data?.detail || err.message}`),
  })
  const handleTrigger = () => { if (!isRunning) runMutation.mutate() }

  const statCards = [
    { label: 'Jobs Discovered', value: stats?.total_jobs || 0, icon: Briefcase, color: 'text-violet-500', bg: 'bg-brand-soft', to: '/feed' },
    { label: 'Applications Sent', value: stats?.total_applied || 0, icon: CheckCircle, color: 'text-teal-600', bg: 'bg-teal-50', to: '/kanban' },
    { label: 'Interviews', value: stats?.total_interviews || 0, icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50', to: '/responses' },
    { label: 'Avg Match Score', value: `${stats?.avg_match_score || 0}%`, icon: TrendingUp, color: 'text-orange-500', bg: 'bg-orange-50', to: '/analytics' },
  ]

  const mockChartData = [
    { name: 'Mon', applied: 4 }, { name: 'Tue', applied: 7 }, { name: 'Wed', applied: 2 },
    { name: 'Thu', applied: 9 }, { name: 'Fri', applied: 5 }, { name: 'Sat', applied: 0 }, { name: 'Sun', applied: 1 },
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {isError && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-100 dark:border-red-800 text-red-600 dark:text-red-300 px-4 py-3 rounded-xl text-sm font-medium flex items-center">
          <span className="mr-2">⚠️</span> Backend is currently unreachable. Start Docker to see live data.
        </div>
      )}

      {/* Hero banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-violet-500 via-purple-500 to-teal-400 p-8 text-white shadow-xl shadow-violet-500/20">
        <div className="relative z-10 max-w-lg">
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <div className="inline-flex items-center gap-2 text-xs font-bold bg-white/20 rounded-full px-3 py-1">
              <Sparkles className="w-3.5 h-3.5" /> Your automated agent
            </div>
            <button onClick={() => navigate('/monitoring')} title="Open System Health"
              className="inline-flex items-center gap-1.5 text-xs font-bold bg-white/15 hover:bg-white/25 rounded-full px-3 py-1 transition">
              <span className={`w-2 h-2 rounded-full ${healthOk ? 'bg-emerald-300' : 'bg-red-300'} animate-pulse`} />
              {healthOk ? 'All systems OK' : 'Check status'}
            </button>
          </div>
          <h2 className="text-3xl font-extrabold mb-2">Welcome Back!</h2>
          <p className="text-white/90 font-medium leading-relaxed">
            You have discovered <span className="font-bold">{stats?.total_jobs || 0} jobs</span> so far.
            Your agent is standing by for the next run.
          </p>
          <button onClick={handleTrigger} disabled={isRunning}
            className="mt-6 inline-flex items-center gap-2 bg-white text-violet-600 px-6 py-2.5 rounded-full font-bold text-sm shadow-sm hover:shadow-md transition-shadow disabled:opacity-60 disabled:cursor-not-allowed">
            {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Running Pipeline…</> : <><Play className="w-4 h-4" /> Trigger Pipeline</>}
          </button>
          {isRunning && runStatus?.step && (
            <p className="mt-3 text-[13px] font-medium text-white/90 inline-flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-300 animate-pulse" /> {runStatus.step}
            </p>
          )}
        </div>
        <div className="absolute -right-10 -top-20 w-72 h-72 bg-white opacity-10 rounded-full blur-2xl"></div>
        <div className="absolute right-24 -bottom-10 w-40 h-40 bg-teal-300 opacity-30 rounded-full blur-xl"></div>
      </div>

      {/* KPI cards — clickable */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, idx) => (
          <button key={idx} onClick={() => navigate(card.to)}
            className="group card flex items-center gap-4 p-5 text-left hover:shadow-lg hover:-translate-y-0.5 hover:border-brand/40 transition-all">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${card.bg}`}>
              <card.icon className={`w-7 h-7 ${card.color}`} strokeWidth={2} />
            </div>
            <div className="flex-1">
              <p className="text-ink-faint text-xs font-bold uppercase tracking-wider">{card.label}</p>
              <h3 className="text-2xl font-black text-ink">{card.value}</h3>
            </div>
            <ChevronRight className="w-5 h-5 text-ink-faint group-hover:text-brand transition-colors" />
          </button>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-extrabold text-ink">Weekly Activity</h3>
            <select className="bg-surface2 border border-line text-xs font-semibold rounded-lg px-3 py-1.5 text-ink-soft outline-none">
              <option>This Week</option><option>Last Week</option>
            </select>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--line)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--ink-faint)', fontSize: 12, fontWeight: 600 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--ink-faint)', fontSize: 12, fontWeight: 600 }} />
                <Tooltip cursor={{ fill: 'var(--surface2)' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="applied" radius={[6, 6, 6, 6]}>
                  {mockChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.applied > 5 ? '#6e5bf1' : '#c9bffe'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-6 flex flex-col">
          <h3 className="text-lg font-extrabold text-ink mb-2">System Status</h3>
          <p className="text-sm text-ink-soft font-medium mb-6">Your background workers</p>
          <div className="space-y-4 flex-1">
            <div className="flex items-center justify-between p-4 bg-surface2 rounded-2xl">
              <div className="flex items-center gap-3">
                <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-blue-500' : 'bg-success'} animate-pulse`}></span>
                <span className="text-sm font-bold text-ink">Pipeline</span>
              </div>
              <span className="text-xs font-semibold text-ink-faint">{isRunning ? (runStatus?.step || 'Running…') : 'Idle'}</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-surface2 rounded-2xl">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 bg-success rounded-full animate-pulse"></span>
                <span className="text-sm font-bold text-ink">Local AI (Ollama)</span>
              </div>
              <span className="text-xs font-semibold text-ink-faint">Ready</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-surface2 rounded-2xl">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 bg-success rounded-full animate-pulse"></span>
                <span className="text-sm font-bold text-ink">IMAP Scanner</span>
              </div>
              <span className="text-xs font-semibold text-ink-faint">Monitoring</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

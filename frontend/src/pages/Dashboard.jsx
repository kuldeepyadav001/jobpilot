import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchDashboard, triggerPipeline, fetchPipelineStatus, fetchSystemHealth } from '../api/client'
import { Briefcase, CheckCircle, Clock, TrendingUp, ChevronRight, Play, Loader2, AlertTriangle } from 'lucide-react'
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
    { label: 'Jobs Discovered', value: stats?.total_jobs || 0, icon: Briefcase, color: 'text-brand', bg: 'bg-brand-soft', to: '/feed' },
    { label: 'Applications Sent', value: stats?.total_applied || 0, icon: CheckCircle, color: 'text-success', bg: 'bg-success-soft', to: '/kanban' },
    { label: 'Interviews', value: stats?.total_interviews || 0, icon: Clock, color: 'text-info', bg: 'bg-info-soft', to: '/responses' },
    { label: 'Avg Match Score', value: `${stats?.avg_match_score || 0}%`, icon: TrendingUp, color: 'text-warn', bg: 'bg-warn-soft', to: '/analytics' },
  ]

  const mockChartData = [
    { name: 'Mon', applied: 4 }, { name: 'Tue', applied: 7 }, { name: 'Wed', applied: 2 },
    { name: 'Thu', applied: 9 }, { name: 'Fri', applied: 5 }, { name: 'Sat', applied: 0 }, { name: 'Sun', applied: 1 },
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {isError && (
        <div className="bg-danger-soft border border-line text-danger px-4 py-3 rounded-lg text-sm font-medium flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" /> Backend is currently unreachable. Start Docker to see live data.
        </div>
      )}

      {/* Hero banner */}
      <div className="card p-6 md:p-8">
        <div className="max-w-xl">
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <div className="inline-flex items-center gap-2 text-xs font-semibold text-brand-strong bg-brand-soft border border-line rounded-md px-2.5 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-brand" /> Automated agent
            </div>
            <button onClick={() => navigate('/monitoring')} title="Open System Health"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-ink-soft hover:text-ink bg-surface2 border border-line rounded-md px-2.5 py-1 transition-colors">
              <span className={`w-2 h-2 rounded-full ${healthOk ? 'bg-success' : 'bg-danger'} animate-pulse`} />
              {healthOk ? 'All systems OK' : 'Check status'}
            </button>
          </div>
          <h2 className="text-2xl font-bold mb-1.5">Welcome back</h2>
          <p className="text-[15px] text-ink-soft leading-relaxed">
            You've discovered <span className="num font-semibold text-ink">{stats?.total_jobs || 0} jobs</span> so far.
            Your agent is standing by for the next run.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button onClick={handleTrigger} disabled={isRunning} className="btn-primary">
              {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Running pipeline…</> : <><Play className="w-4 h-4" /> Trigger pipeline</>}
            </button>
            {isRunning && runStatus?.step && (
              <span className="text-[13px] font-medium text-ink-soft inline-flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-brand animate-pulse" /> {runStatus.step}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* KPI cards — clickable */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, idx) => (
          <button key={idx} onClick={() => navigate(card.to)}
            className="group card flex items-center gap-4 p-5 text-left hover:border-line-strong transition-colors">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${card.bg}`}>
              <card.icon className={`w-6 h-6 ${card.color}`} strokeWidth={2} />
            </div>
            <div className="flex-1">
              <p className="text-ink-faint text-[11px] font-semibold uppercase tracking-wider">{card.label}</p>
              <h3 className="num text-2xl font-semibold text-ink mt-0.5">{card.value}</h3>
            </div>
            <ChevronRight className="w-4 h-4 text-ink-faint group-hover:text-brand transition-colors" />
          </button>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-[15px] font-semibold text-ink">Weekly Activity</h3>
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
                    <Cell key={`cell-${index}`} fill={entry.applied > 5 ? 'var(--brand)' : 'var(--brand-soft)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-6 flex flex-col">
          <h3 className="text-[15px] font-semibold text-ink mb-1">System Status</h3>
          <p className="text-[13px] text-ink-soft mb-5">Your background workers</p>
          <div className="space-y-2.5 flex-1">
            <div className="flex items-center justify-between px-4 py-3 bg-surface2 rounded-lg">
              <div className="flex items-center gap-2.5">
                <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-brand' : 'bg-success'} animate-pulse`}></span>
                <span className="text-[13px] font-semibold text-ink">Pipeline</span>
              </div>
              <span className="text-xs font-medium text-ink-faint">{isRunning ? (runStatus?.step || 'Running…') : 'Idle'}</span>
            </div>
            <div className="flex items-center justify-between px-4 py-3 bg-surface2 rounded-lg">
              <div className="flex items-center gap-2.5">
                <span className="w-2 h-2 bg-success rounded-full animate-pulse"></span>
                <span className="text-[13px] font-semibold text-ink">Local AI (Ollama)</span>
              </div>
              <span className="text-xs font-medium text-ink-faint">Ready</span>
            </div>
            <div className="flex items-center justify-between px-4 py-3 bg-surface2 rounded-lg">
              <div className="flex items-center gap-2.5">
                <span className="w-2 h-2 bg-success rounded-full animate-pulse"></span>
                <span className="text-[13px] font-semibold text-ink">IMAP Scanner</span>
              </div>
              <span className="text-xs font-medium text-ink-faint">Monitoring</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

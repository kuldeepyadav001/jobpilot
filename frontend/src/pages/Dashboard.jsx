import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchDashboard, triggerPipeline, fetchPipelineStatus } from '../api/client'
import { Briefcase, CheckCircle, Clock, TrendingUp, ChevronRight, Play, Loader2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: stats, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    retry: false,
  })

  // Live pipeline state so the button reflects running/success/error truthfully.
  const { data: runStatus } = useQuery({
    queryKey: ['pipelineStatus'],
    queryFn: fetchPipelineStatus,
    refetchInterval: 3000,
    retry: false,
  })
  const isRunning = runStatus?.running

  const runMutation = useMutation({
    mutationFn: triggerPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelineStatus'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (err) => {
      alert(`Failed to start pipeline: ${err.response?.data?.detail || err.message}`)
    },
  })

  const handleTrigger = () => {
    if (isRunning) return
    runMutation.mutate()
  }

  const statCards = [
    { label: 'Jobs Discovered', value: stats?.total_jobs || 0, icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50', to: '/feed' },
    { label: 'Applications Sent', value: stats?.total_applied || 0, icon: CheckCircle, color: 'text-indigo-600', bg: 'bg-indigo-50', to: '/kanban' },
    { label: 'Interviews', value: stats?.total_interviews || 0, icon: Clock, color: 'text-emerald-600', bg: 'bg-emerald-50', to: '/responses' },
    { label: 'Avg Match Score', value: `${stats?.avg_match_score || 0}%`, icon: TrendingUp, color: 'text-orange-600', bg: 'bg-orange-50', to: '/analytics' },
  ]

  const mockChartData = [
    { name: 'Mon', applied: 4 },
    { name: 'Tue', applied: 7 },
    { name: 'Wed', applied: 2 },
    { name: 'Thu', applied: 9 },
    { name: 'Fri', applied: 5 },
    { name: 'Sat', applied: 0 },
    { name: 'Sun', applied: 1 },
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {isError && (
        <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl text-sm font-medium flex items-center">
          <span className="mr-2">⚠️</span> Backend is currently unreachable. Start Docker to see live data.
        </div>
      )}

      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-3xl p-8 text-white shadow-lg shadow-indigo-200 flex justify-between items-center relative overflow-hidden">
        <div className="relative z-10">
          <h2 className="text-3xl font-extrabold mb-2">Welcome Back!</h2>
          <p className="text-indigo-100 font-medium max-w-md leading-relaxed">
            Your automated agent is standing by. You have discovered <span className="text-white font-bold">{stats?.total_jobs || 0} jobs</span> so far.
          </p>
          <button
            onClick={handleTrigger}
            disabled={isRunning}
            className="mt-6 inline-flex items-center gap-2 bg-white text-indigo-600 px-6 py-2.5 rounded-full font-bold text-sm shadow-sm hover:shadow-md transition-shadow disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isRunning
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Running Pipeline…</>
              : <><Play className="w-4 h-4" /> Trigger Pipeline</>}
          </button>
        </div>
        <div className="absolute -right-10 -top-20 w-64 h-64 bg-white opacity-10 rounded-full blur-2xl"></div>
        <div className="absolute right-20 -bottom-10 w-40 h-40 bg-purple-400 opacity-20 rounded-full blur-xl"></div>
      </div>

      {/* KPI Cards — clickable */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, idx) => (
          <button
            key={idx}
            onClick={() => navigate(card.to)}
            className="group bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex items-center gap-5 text-left hover:shadow-md hover:border-indigo-200 transition-all"
          >
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${card.bg}`}>
              <card.icon className={`w-7 h-7 ${card.color}`} strokeWidth={2} />
            </div>
            <div className="flex-1">
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">{card.label}</p>
              <h3 className="text-2xl font-black text-slate-800">{card.value}</h3>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-indigo-500 transition-colors" />
          </button>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-extrabold text-slate-800">Weekly Activity</h3>
            <select className="bg-slate-50 border border-slate-200 text-sm font-semibold rounded-lg px-3 py-1.5 text-slate-600 outline-none">
              <option>This Week</option>
              <option>Last Week</option>
            </select>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }} />
                <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="applied" radius={[6, 6, 6, 6]}>
                  {mockChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.applied > 5 ? '#4f46e5' : '#c7d2fe'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex flex-col">
          <h3 className="text-lg font-extrabold text-slate-800 mb-2">System Status</h3>
          <p className="text-sm text-slate-500 font-medium mb-6">Your background workers</p>
          <div className="space-y-4 flex-1">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
              <div className="flex items-center gap-3">
                <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-blue-500 animate-pulse' : 'bg-green-500 animate-pulse'}`}></span>
                <span className="text-sm font-bold text-slate-700">Pipeline</span>
              </div>
              <span className="text-xs font-semibold text-slate-400">{isRunning ? 'Running…' : 'Idle'}</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-sm font-bold text-slate-700">Local AI (Ollama)</span>
              </div>
              <span className="text-xs font-semibold text-slate-400">Ready</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-sm font-bold text-slate-700">IMAP Scanner</span>
              </div>
              <span className="text-xs font-semibold text-slate-400">Monitoring</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

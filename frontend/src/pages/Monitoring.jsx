import { useQuery } from '@tanstack/react-query'
import { fetchSystemHealth, fetchMetricsText } from '../api/client'
import {
  Activity, Cpu, Database, GitBranch, Mail, RefreshCw, Server, CheckCircle2,
  AlertCircle, Gauge, HardDrive, Trash2,
} from 'lucide-react'

function Stat({ label, value, tone = 'text-slate-800' }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
      <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">{label}</p>
      <h3 className={`text-2xl font-black mt-1 ${tone}`}>{value}</h3>
    </div>
  )
}

function HealthCard({ name, icon: Icon, status }) {
  const ok = status?.ok
  return (
    <div className={`bg-white rounded-2xl p-5 shadow-sm border flex items-start gap-4 ${ok ? 'border-slate-100' : 'border-red-200'}`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${ok ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-extrabold text-slate-800 flex items-center gap-2">
          {name}
          {ok
            ? <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full"><CheckCircle2 className="w-3 h-3" />OK</span>
            : <span className="inline-flex items-center gap-1 text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full"><AlertCircle className="w-3 h-3" />DOWN</span>}
        </p>
        <p className="text-xs text-slate-500 mt-1 break-words">{status?.detail || 'N/A'}</p>
      </div>
    </div>
  )
}

function CookieBadge({ status }) {
  const map = {
    configured: ['bg-emerald-600/10 text-emerald-600', '✓ Active'],
    empty: ['bg-yellow-600/10 text-yellow-600', '⚠ Too short'],
    missing: ['bg-red-600/10 text-red-600', '✕ Missing'],
  }
  const [cls, label] = map[status] || map.missing
  return <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${cls}`}>{label}</span>
}

function formatUptime(secs) {
  if (!secs && secs !== 0) return '—'
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = secs % 60
  if (h) return `${h}h ${m}m`
  if (m) return `${m}m ${s}s`
  return `${s}s`
}

export default function Monitoring() {
  const { data: health, isLoading, refetch } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval: 5000, // live polling
  })
  const { data: metricsText } = useQuery({
    queryKey: ['metricsText'],
    queryFn: fetchMetricsText,
    refetchInterval: 15000,
  })

  const counts = health?.counts || {}

  const refreshAll = () => { refetch() }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">System Monitoring</h2>
          <p className="text-sm text-slate-400">Live health & tracking. Polling every 5s.</p>
        </div>
        <button onClick={refreshAll} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Uptime + headline counts */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Uptime" value={formatUptime(health?.uptime_seconds)} />
        <Stat label="Jobs" value={counts.total_jobs ?? '—'} />
        <Stat label="Applications" value={counts.total_applications ?? '—'} tone="text-indigo-600" />
        <Stat label="Responses" value={counts.total_responses ?? '—'} tone="text-emerald-600" />
      </div>

      {/* Component health */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <HealthCard name="Database" icon={Database} status={health?.db} />
        <HealthCard name="Local AI (Ollama)" icon={Cpu} status={health?.ollama} />
        <HealthCard name="Scheduler" icon={Server} status={health?.scheduler} />
        <HealthCard name="Pipeline" icon={GitBranch} status={health?.pipeline} />
      </div>

      {/* Cookies */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div className="flex items-center gap-2 mb-4">
          <Mail className="w-4 h-4 text-slate-400" />
          <h3 className="text-base font-bold text-slate-800">Portal Session Cookies</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(health?.cookies || {}).map(([portal, status]) => (
            <div key={portal} className="flex items-center justify-between bg-slate-50 rounded-xl p-4 border border-slate-100">
              <span className="text-sm font-semibold uppercase text-slate-700">{portal}</span>
              <CookieBadge status={status} />
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3">Expired cookies silently stop scraping. Refresh cookies in `.env` and restart the backend.</p>
      </div>

      {/* Metrics / Prometheus */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-3">
          <Gauge className="w-4 h-4 text-blue-400" />
          <h3 className="text-base font-bold text-white">Prometheus Metrics</h3>
          <span className="ml-2 text-[10px] font-bold bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded-full">/metrics</span>
        </div>
        <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-xs text-gray-300 max-h-64 overflow-auto">
          <pre className="whitespace-pre-wrap">{metricsText || 'Fetching metrics…'}</pre>
        </div>
        <p className="text-xs text-gray-500 mt-3">Open the Grafana dashboard for a full time-series view: <span className="text-blue-400">http://localhost:3001</span> (user <code className="text-gray-400">admin</code>, password <code className="text-gray-400">admin</code>).</p>
      </div>
    </div>
  )
}

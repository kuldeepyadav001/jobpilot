import { useQuery } from '@tanstack/react-query'
import { fetchSystemHealth, fetchMetricsText } from '../api/client'
import { Cpu, Database, GitBranch, Mail, RefreshCw, Server, CheckCircle2, AlertCircle, Gauge } from 'lucide-react'

function Stat({ label, value, tone = 'text-ink' }) {
  return (
    <div className="card p-5">
      <p className="label">{label}</p>
      <h3 className={`text-2xl font-black mt-1 ${tone}`}>{value}</h3>
    </div>
  )
}

function HealthCard({ name, icon: Icon, status }) {
  const ok = status?.ok
  return (
    <div className={`card flex items-start gap-4 p-5 ${ok ? '' : '!border-danger/40'}`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${ok ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-extrabold text-ink flex items-center gap-2">
          {name}
          {ok
            ? <span className="inline-flex items-center gap-1 text-[10px] font-bold text-success bg-success/10 px-2 py-0.5 rounded-full"><CheckCircle2 className="w-3 h-3" />OK</span>
            : <span className="inline-flex items-center gap-1 text-[10px] font-bold text-danger bg-danger/10 px-2 py-0.5 rounded-full"><AlertCircle className="w-3 h-3" />DOWN</span>}
        </p>
        <p className="text-xs text-ink-soft mt-1 break-words">{status?.detail || 'N/A'}</p>
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
  const { data: health, refetch } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval: 5000,
  })
  const { data: metricsText } = useQuery({
    queryKey: ['metricsText'],
    queryFn: fetchMetricsText,
    refetchInterval: 15000,
  })

  const counts = health?.counts || {}

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink">System Monitoring</h2>
          <p className="text-sm text-ink-soft">Live health &amp; tracking. Polling every 5s.</p>
        </div>
        <button onClick={() => refetch()} className="btn-primary"><RefreshCw className="w-4 h-4" /> Refresh</button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Uptime" value={formatUptime(health?.uptime_seconds)} />
        <Stat label="Jobs" value={counts.total_jobs ?? '—'} />
        <Stat label="Applications" value={counts.total_applications ?? '—'} tone="text-violet-500" />
        <Stat label="Responses" value={counts.total_responses ?? '—'} tone="text-success" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <HealthCard name="Database" icon={Database} status={health?.db} />
        <HealthCard name="Local AI (Ollama)" icon={Cpu} status={health?.ollama} />
        <HealthCard name="Scheduler" icon={Server} status={health?.scheduler} />
        <HealthCard name="Pipeline" icon={GitBranch} status={health?.pipeline} />
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Mail className="w-4 h-4 text-ink-faint" />
          <h3 className="text-base font-bold text-ink">Portal Session Cookies</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(health?.cookies || {}).map(([portal, status]) => (
            <div key={portal} className="flex items-center justify-between bg-surface2 rounded-xl p-4 border border-line">
              <span className="text-sm font-semibold uppercase text-ink">{portal}</span>
              <CookieBadge status={status} />
            </div>
          ))}
        </div>
        <p className="text-xs text-ink-faint mt-3">Expired cookies silently stop scraping. Refresh cookies in `.env` and restart the backend.</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-2 mb-3">
          <Gauge className="w-4 h-4 text-brand" />
          <h3 className="text-base font-bold text-ink">Prometheus Metrics</h3>
          <span className="ml-2 text-[10px] font-bold bg-brand-soft text-brand px-2 py-0.5 rounded-full">/metrics</span>
        </div>
        <div className="bg-surface2 border border-line rounded-lg p-4 font-mono text-xs text-ink-soft max-h-64 overflow-auto">
          <pre className="whitespace-pre-wrap">{metricsText || 'Fetching metrics…'}</pre>
        </div>
        <p className="text-xs text-ink-faint mt-3">Open the Grafana dashboard for a full time-series view: <span className="text-brand font-semibold">http://localhost:3001</span> (user <code className="text-ink-soft">admin</code>, password <code className="text-ink-soft">admin</code>).</p>
      </div>
    </div>
  )
}

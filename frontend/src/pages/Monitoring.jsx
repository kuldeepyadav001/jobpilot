import { useQuery } from '@tanstack/react-query'
import { fetchSystemHealth } from '../api/client'
import { Cpu, Database, GitBranch, Mail, RefreshCw, Server, CheckCircle2, AlertCircle, Activity, Briefcase, Send, Inbox, Trophy } from 'lucide-react'

function Stat({ label, value, tone = 'text-ink', icon: Icon }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-1.5 mb-1">
        {Icon && <Icon className="w-3.5 h-3.5 text-ink-faint" />}
        <p className="label">{label}</p>
      </div>
      <h3 className={`text-2xl font-black mt-1 ${tone}`}>{value}</h3>
    </div>
  )
}

function HealthCard({ name, icon: Icon, status }) {
  const ok = status?.ok
  return (
    <div className={`card flex items-start gap-4 p-5 ${ok === false ? '!border-danger/40' : ''}`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${ok === false ? 'bg-danger/10 text-danger' : 'bg-success/10 text-success'}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-extrabold text-ink flex items-center gap-2">
          {name}
          {ok === false
            ? <span className="inline-flex items-center gap-1 text-[10px] font-bold text-danger bg-danger/10 px-2 py-0.5 rounded-full"><AlertCircle className="w-3 h-3" />DOWN</span>
            : <span className="inline-flex items-center gap-1 text-[10px] font-bold text-success bg-success/10 px-2 py-0.5 rounded-full"><CheckCircle2 className="w-3 h-3" />OK</span>}
        </p>
        <p className="text-xs text-ink-soft mt-1 break-words">{status?.detail || 'N/A'}</p>
      </div>
    </div>
  )
}

function PipelineCard({ status }) {
  const running = status?.ok === false && /running|started/i.test(status?.detail || '')
  const cls = running ? 'bg-warn/10 text-warn' : status?.ok === false ? 'bg-danger/10 text-danger' : 'bg-success/10 text-success'
  const label = running ? 'RUNNING' : status?.ok === false ? 'ERROR' : 'READY'
  return (
    <div className={`card flex items-start gap-4 p-5 ${status?.ok === false && !running ? '!border-danger/40' : ''}`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${cls}`}>
        <GitBranch className={`w-5 h-5 ${running ? 'animate-pulse' : ''}`} />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-extrabold text-ink flex items-center gap-2">
          Pipeline
          <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${cls}`}>{label}</span>
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
  return h ? `${h}h ${m}m` : `${m}m ${secs % 60}s`
}

export default function Monitoring() {
  const { data: health, refetch } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval: 5000,
  })
  const counts = health?.counts || {}

  const critical = [health?.db, health?.ollama, health?.scheduler]
  const allOk = critical.every(c => c?.ok !== false)

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink">System Health</h2>
          <p className="text-sm text-ink-soft">Live check-up of every component. Auto-refreshes every 5s.</p>
        </div>
        <button onClick={() => refetch()} className="btn-primary"><RefreshCw className="w-4 h-4" /> Refresh</button>
      </div>

      {/* Overall status banner */}
      <div className={`rounded-2xl p-5 flex items-center gap-4 border ${allOk ? 'bg-success/10 border-success/30' : 'bg-danger/10 border-danger/30'}`}>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${allOk ? 'text-success' : 'text-danger'}`}>
          <Activity className="w-6 h-6" />
        </div>
        <div>
          <h3 className={`text-lg font-black ${allOk ? 'text-success' : 'text-danger'}`}>
            {allOk ? 'All systems healthy' : 'Attention needed'}
          </h3>
          <p className="text-xs text-ink-soft font-medium">
            {allOk
              ? "Database, local AI and scheduler are all reachable. You're good to go."
              : 'One or more components are down. See the cards below and check the backend logs.'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Uptime" value={formatUptime(health?.uptime_seconds)} icon={Activity} />
        <Stat label="Jobs" value={counts.total_jobs ?? '—'} icon={Briefcase} />
        <Stat label="Applications" value={counts.total_applications ?? '—'} tone="text-violet-500" icon={Send} />
        <Stat label="Responses" value={counts.total_responses ?? '—'} tone="text-success" icon={Inbox} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <HealthCard name="Database" icon={Database} status={health?.db} />
        <HealthCard name="Local AI (Ollama)" icon={Cpu} status={health?.ollama} />
        <HealthCard name="Scheduler" icon={Server} status={health?.scheduler} />
        <PipelineCard status={health?.pipeline} />
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
        <p className="text-xs text-ink-faint mt-3">Expired cookies silently stop scraping. Refresh them in `.env` and restart the backend.</p>
      </div>

      {/* Interviews + offers mini row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="card p-5 flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center"><Trophy className="w-5 h-5" /></div>
          <div>
            <p className="label">Interviews</p>
            <h3 className="text-2xl font-black text-ink">{counts.interviews ?? 0}</h3>
          </div>
        </div>
        <div className="card p-5 flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center"><Trophy className="w-5 h-5" /></div>
          <div>
            <p className="label">Offers</p>
            <h3 className="text-2xl font-black text-ink">{counts.offers ?? 0}</h3>
          </div>
        </div>
      </div>
    </div>
  )
}

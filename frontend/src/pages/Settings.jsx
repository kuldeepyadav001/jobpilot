import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { triggerPipeline, fetchPipelineStatus, fetchAppSettings, runScraperDiagnostics, runJobCleanup } from '../api/client'
import { fetchCookieHealth } from '../api/client'
import { Play, Loader2, KeyRound, Cpu, Database, Mail, Timer, Radar, ExternalLink, Trash2 } from 'lucide-react'

export default function Settings() {
  const [log, setLog] = useState([])
  const queryClient = useQueryClient()

  const { data: appCfg } = useQuery({ queryKey: ['appSettings'], queryFn: fetchAppSettings })
  const isRealMode = appCfg?.apply_mode === 'real'

  const { data: runStatus } = useQuery({
    queryKey: ['pipelineStatus'], queryFn: fetchPipelineStatus, refetchInterval: 3000,
  })
  const isRunning = runStatus?.running

  useEffect(() => {
    if (runStatus && (runStatus.status === 'success' || runStatus.status === 'error')) {
      const newLine = `[${new Date().toLocaleTimeString()}] ${runStatus.status.toUpperCase()}: ${runStatus.message}`
      setLog(prev => (prev[prev.length - 1] === newLine ? prev : [...prev, newLine]))
    }
  }, [runStatus])

  const runMutation = useMutation({
    mutationFn: triggerPipeline,
    onMutate: () => setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] Submitting background pipeline run...`]),
    onSuccess: (data) => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] STARTED: ${data.message}`])
      queryClient.invalidateQueries({ queryKey: ['pipelineStatus'] })
    },
    onError: (err) => setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${err.response?.data?.detail || err.message || "Failed to start pipeline run."}`]),
  })

  const { data: cookies = [] } = useQuery({ queryKey: ['cookieHealth'], queryFn: fetchCookieHealth, refetchInterval: 60000 })

  const diagMutation = useMutation({
    // Long-running: scrapes live portals but saves nothing.
    mutationFn: runScraperDiagnostics,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scraperDiag'] }),
  })

  const cleanMutation = useMutation({
    mutationFn: runJobCleanup,
    onSuccess: () => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] CLEANUP: removed ${cleanMutation.data?.deleted ?? 'some'} stale jobs`])
    },
  })

  const infoCards = [
    { icon: Cpu, label: 'Local AI Model', value: 'Ollama qwen2.5:1.5b', sub: 'URL: http://ollama:11434 (in-network)' },
    { icon: Database, label: 'Active Database', value: 'PostgreSQL 15.5', sub: 'Connection: Bounded local socket' },
    { icon: Mail, label: 'Inbox Scanner Route', value: 'IMAP Gmail SSL Mode', sub: 'Tracking: Match sender domains' },
    { icon: Timer, label: 'Scraping Loop Interval', value: 'Every 6 Hours', sub: 'Daemon: APScheduler Engine' },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-ink">System Configuration</h2>

      {/* Pipeline trigger */}
      <div className="card p-6 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-brand">Run Full Pipeline (One Click)</h3>
          <p className="text-xs text-ink-soft mt-1">
            Click once and it does everything automatically: scrape Internshala + Naukri → score against your resumes → pick the best resume → generate a cover letter → apply → scan responses → update statuses.
          </p>
          <div className="mt-2 inline-flex items-center gap-2">
            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase ${isRealMode ? 'bg-success/20 text-success' : 'bg-warn/20 text-warn'}`}>
              {appCfg ? (isRealMode ? 'Ready to apply for real' : 'Dry-run: won\u2019t submit') : '…'}
            </span>
            <span className="text-[10px] text-ink-faint">
              {isRealMode ? 'Applications will be sent to employers.' : 'Set APPLY_MODE=real in .env to send for real.'}
            </span>
          </div>
        </div>

        <button
          onClick={() => { if (isRealMode && !window.confirm("This will send REAL applications to employers. Continue?")) return; runMutation.mutate() }}
          disabled={isRunning}
          className="btn-primary">
          {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> Running Pipeline…</> : <><Play className="w-4 h-4" /> {isRealMode ? 'Run Full Pipeline (Applies)' : 'Run Full Pipeline (Dry-run)'}</>}
        </button>

        {log.length > 0 && (
          <div className="space-y-1">
            <p className="label">Execution Log Output</p>
            <div className="bg-surface2 border border-line rounded-lg p-4 font-mono text-xs text-ink-soft space-y-1 h-32 overflow-y-auto">
              {log.map((line, idx) => <p key={idx}>{line}</p>)}
            </div>
          </div>
        )}
      </div>

      {/* Cookie status */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-ink-faint" />
          <h3 className="text-base font-semibold">Portal Cookie Status</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cookies.map((c) => (
            <div key={c.portal} className="bg-surface2 p-3 border border-line rounded-xl flex items-center justify-between">
              <div>
                <p className="font-semibold text-sm uppercase text-ink">{c.portal}</p>
                <p className="text-xs text-ink-faint">Cookie length: {c.cookie_length} chars</p>
              </div>
              <span className={`text-xs font-bold px-3 py-1 rounded-full text-white ${
                c.status === 'configured' ? 'bg-success' : c.status === 'empty' ? 'bg-warn' : 'bg-danger'
              }`}>
                {c.status === 'configured' ? '✅ Active' : c.status === 'empty' ? '⚠️ Too Short' : '❌ Missing'}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-ink-faint">If a cookie shows "Missing" or "Too Short", update it in your .env file and restart the backend.</p>
      </div>

      {/* Scraper validation (dry-run) */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Radar className="w-4 h-4 text-brand" />
          <h3 className="text-base font-semibold">Validate Scrapers (Dry-run)</h3>
        </div>
        <p className="text-xs text-ink-soft">
          Scrapes Internshala + Naukri for your keywords but <strong>saves nothing</strong> — it only reports
          how many jobs each portal returned. Use this to confirm the scrapers and cookies work before going real.
          Modify keywords/location via <code className="text-ink">SEARCH_KEYWORDS</code>, <code className="text-ink">SEARCH_LOCATION</code> in .env.
        </p>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => diagMutation.mutate({})} disabled={diagMutation.isPending} className="btn-ghost">
            {diagMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Scraping…</> : <><Radar className="w-4 h-4" /> Run Scraper Test</>}
          </button>
          <button onClick={() => cleanMutation.mutate()} disabled={cleanMutation.isPending} className="btn-ghost">
            <Trash2 className="w-4 h-4" /> {cleanMutation.isPending ? 'Cleaning…' : 'Clean Up Old Jobs'}
          </button>
          <span className="text-[10px] text-ink-faint self-center">
            Auto-prunes never-applied jobs older than {appCfg?.job_retention_days ?? 30} days, weekly.
          </span>
        </div>
        {cleanMutation.data && (
          <p className="text-xs text-ink-soft bg-surface2 border border-line rounded-lg p-3">
            Cleanup ran: scanned {cleanMutation.data.scanned} stale, removed <strong className="text-success">{cleanMutation.data.deleted}</strong>.
          </p>
        )}

        {diagMutation.data && (
          <div className="bg-surface2 border border-line rounded-xl p-4 space-y-3">
            {diagMutation.data.results.map((r, i) => (
              <div key={i}>
                <div className="flex items-center gap-3 mb-1.5">
                  <span className="font-bold text-sm text-ink">{r.keyword}</span>
                  {Object.entries(r.by_portal).map(([p, n]) => (
                    <span key={p} className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${n > 0 ? 'bg-success/15 text-success' : 'bg-danger/15 text-danger'}`}>
                      {p}: {n}
                    </span>
                  ))}
                </div>
                {r.sample && r.sample.length > 0 && (
                  <ul className="text-xs text-ink-soft space-y-0.5">
                    {r.sample.map((s, j) => (
                      <li key={j} className="flex items-center gap-1.5">
                        <span className="uppercase text-[10px] text-ink-faint">{s.portal}</span>
                        <span className="font-semibold text-ink">{s.title}</span>
                        <span className="text-ink-faint">@ {s.company}</span>
                        <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-brand hover:underline"><ExternalLink className="w-3 h-3 inline" /></a>
                      </li>
                    ))}
                  </ul>
                )}
                {r.errors && r.errors.length > 0 && r.errors.map((e, j) => <p key={j} className="text-[11px] text-danger">{e}</p>)}
              </div>
            ))}
          </div>
        )}
        {diagMutation.isError && <p className="text-xs text-danger">{diagMutation.error?.response?.data?.detail || 'Scraper test failed (backend offline?).'}</p>}
      </div>

      {/* Env summary */}
      <div className="card p-6 space-y-4">
        <h3 className="text-base font-semibold">Environment Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          {infoCards.map((c, i) => (
            <div key={i} className="bg-surface2 p-3 border border-line rounded-xl space-y-1">
              <p className="text-ink-faint font-bold flex items-center gap-1.5"><c.icon className="w-3.5 h-3.5" /> {c.label}</p>
              <p className="text-brand font-semibold">{c.value}</p>
              <p className="text-[10px] text-ink-faint">{c.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

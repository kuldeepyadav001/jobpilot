import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { triggerPipeline, fetchPipelineStatus, fetchAppSettings, runScraperDiagnostics, fetchScraperDiagnosticsStatus, runJobCleanup } from '../api/client'
import { fetchCookieHealth, checkSession } from '../api/client'
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

  // Scraper dry-run runs in the BACKGROUND (it can take minutes), so we start it
  // with a POST and poll /status every 2s until it finishes.
  const diagMutation = useMutation({
    mutationFn: runScraperDiagnostics,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scraperDiagStatus'] }),
    onError: () => queryClient.invalidateQueries({ queryKey: ['scraperDiagStatus'] }),
  })
  const { data: diagStatus = { running: false, status: 'idle', results: [] } } = useQuery({
    queryKey: ['scraperDiagStatus'],
    queryFn: fetchScraperDiagnosticsStatus,
    refetchInterval: (q) => (q.state.data?.running ? 2000 : false),
  })

  const cleanMutation = useMutation({
    mutationFn: runJobCleanup,
    onSuccess: () => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] CLEANUP: removed ${cleanMutation.data?.deleted ?? 'some'} stale jobs`])
    },
  })

  // Live cookie validity test — actually logs into the portal with the cookie.
  const sessionMutation = useMutation({
    mutationFn: (portal) => checkSession(portal),
    onSuccess: (data) => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] SESSION ${data[0]?.portal?.toUpperCase()}: ${data[0]?.message}`])
    },
    onError: (err) => setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] SESSION CHECK ERROR: ${err.response?.data?.detail || err.message || 'failed'}`]),
  })
  const sessionResult = sessionMutation.data?.[0]

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
          <div className="mt-2 inline-flex items-center gap-2 flex-wrap">
            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase ${isRealMode ? 'bg-success/20 text-success' : 'bg-warn/20 text-warn'}`}>
              {appCfg ? (isRealMode ? 'Ready to apply for real' : 'Dry-run: won\u2019t submit') : '…'}
            </span>
            <span className="text-[10px] text-ink-faint">
              {isRealMode
                ? `Will send up to ${appCfg?.apply_target_count ?? 10} jobs this run (${appCfg?.daily_apply_cap ?? 25}/day/portal).`
                : 'Set APPLY_MODE=real in .env to ACTUALLY submit. Right now it only marks jobs as Applied in the dashboard without sending them.'}
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
            <div key={c.portal} className="bg-surface2 p-3 border border-line rounded-xl">
              <div className="flex items-center justify-between">
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
              <button
                onClick={() => sessionMutation.mutate(c.portal)}
                disabled={sessionMutation.isPending}
                className="btn-ghost w-full mt-2 text-xs">
                {sessionMutation.isPending ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Checking login…</> : <>Test Login (live)</>}
              </button>
              {sessionResult && sessionResult.portal === c.portal && (
                <p className={`text-[11px] font-bold mt-1 ${sessionResult.ok ? 'text-success' : 'text-danger'}`}>
                  {sessionResult.logged_in ? '✅ Logged in — cookie works.' : '❌ Not logged in — cookie invalid/expired.'}
                </p>
              )}
            </div>
          ))}
        </div>
        <p className="text-xs text-ink-faint">
          "Cookie length" only proves text is present. <strong>Test Login</strong> actually loads the portal with
          your cookie and confirms you're signed in — if it's red, refresh the cookie in .env and restart the backend.
        </p>
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
          <button onClick={() => diagMutation.mutate({})} disabled={diagMutation.isPending || diagStatus.running} className="btn-ghost">
            {diagStatus.running ? <><Loader2 className="w-4 h-4 animate-spin" /> Scraping…</> : diagMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Starting…</> : <><Radar className="w-4 h-4" /> Run Scraper Test</>}
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

        {diagStatus.running && (
          <p className="text-xs text-brand animate-pulse">
            <Loader2 className="w-3.5 h-3.5 inline animate-spin" /> Dry-run scraper running in the background (this can take a minute or two)…
          </p>
        )}
        {diagStatus.status === 'error' && <p className="text-xs text-danger">{diagStatus.message}</p>}
        {diagStatus.results && diagStatus.results.length > 0 && (
          <div className="bg-surface2 border border-line rounded-xl p-4 space-y-3">
            {diagStatus.results.map((r, i) => (
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

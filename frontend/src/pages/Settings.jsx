import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { triggerPipeline, fetchPipelineStatus } from '../api/client'
import { fetchCookieHealth, fetchAppSettings } from '../api/client'
export default function Settings() {
  const [log, setLog] = useState([])
  const queryClient = useQueryClient()

  // Current apply gate so the UI warns correctly.
  const { data: appCfg } = useQuery({
    queryKey: ['appSettings'],
    queryFn: fetchAppSettings,
  })
  const isRealMode = appCfg?.apply_mode === 'real'

  // Poll the background run status so "running → success/error" is truthful.
  const { data: runStatus } = useQuery({
    queryKey: ['pipelineStatus'],
    queryFn: fetchPipelineStatus,
    refetchInterval: 3000,
  })
  const isRunning = runStatus?.running

  // When the background task finishes, append its real final status once.
  useEffect(() => {
    if (runStatus && (runStatus.status === 'success' || runStatus.status === 'error')) {
      const newLine = `[${new Date().toLocaleTimeString()}] ${runStatus.status.toUpperCase()}: ${runStatus.message}`
      setLog(prev => (prev[prev.length - 1] === newLine ? prev : [...prev, newLine]))
    }
  }, [runStatus])

  const runMutation = useMutation({
    mutationFn: triggerPipeline,
    onMutate: () => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] Submitting background pipeline run...`])
    },
    onSuccess: (data) => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] STARTED: ${data.message}`])
      queryClient.invalidateQueries({ queryKey: ['pipelineStatus'] })
    },
    onError: (err) => {
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${err.response?.data?.detail || err.message || "Failed to start pipeline run."}`])
    },
  })

  const { data: cookies = [] } = useQuery({
  queryKey: ['cookieHealth'],
  queryFn: fetchCookieHealth,
  refetchInterval: 60000, // Refresh every minute
})

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">System Configuration</h2>

      {/* Manual Pipeline Activation Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-blue-400">Run Full Pipeline (One Click)</h3>
          <p className="text-xs text-gray-400 mt-1">
            Click once and it does everything automatically: scrape Internshala + Naukri → score against your resumes → pick the best resume → generate a cover letter → apply → scan responses → update statuses.
          </p>
          <div className="mt-2 inline-flex items-center gap-2">
            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase ${
              isRealMode ? 'bg-green-600/20 text-green-400' : 'bg-yellow-600/20 text-yellow-400'
            }`}>
              {appCfg ? (isRealMode ? 'Ready to apply for real' : 'Dry-run: won\u2019t submit') : '…'}
            </span>
            <span className="text-[10px] text-gray-500">
              {isRealMode
                ? 'Applications will be sent to employers.'
                : 'Set APPLY_MODE=real in .env to send for real.'}
            </span>
          </div>
        </div>

        <button
          onClick={() => {
            if (isRealMode && !window.confirm("This will send REAL applications to employers. Continue?")) return
            runMutation.mutate()
          }}
          disabled={isRunning}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-semibold disabled:opacity-30 transition"
        >
          {isRunning ? "Running Pipeline..." : isRealMode ? "Run Full Pipeline (Applies)" : "Run Full Pipeline (Dry-run)"}
        </button>

        {log.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-semibold text-gray-400">Execution Log Output</p>
            <div className="bg-gray-950 border border-gray-800 rounded p-4 font-mono text-xs text-gray-300 space-y-1 h-32 overflow-y-auto">
              {log.map((line, idx) => (
                <p key={idx}>{line}</p>
              ))}
            </div>
          </div>
        )}
      </div>
<div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
  <h3 className="text-base font-semibold">Portal Cookie Status</h3>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {cookies.map((c) => (
      <div key={c.portal} className="bg-gray-950 p-3 border border-gray-800 rounded flex items-center justify-between">
        <div>
          <p className="font-semibold text-sm uppercase">{c.portal}</p>
          <p className="text-xs text-gray-500">Cookie length: {c.cookie_length} chars</p>
        </div>
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${
          c.status === 'configured' ? 'bg-green-600 text-white' :
          c.status === 'empty' ? 'bg-yellow-600 text-white' :
          'bg-red-600 text-white'
        }`}>
          {c.status === 'configured' ? '✅ Active' :
           c.status === 'empty' ? '⚠️ Too Short' :
           '❌ Missing'}
        </span>
      </div>
    ))}
  </div>
  <p className="text-xs text-gray-500">
    If a cookie shows "Missing" or "Too Short", update it in your .env file and restart the backend.
  </p>
</div>
      {/* Configuration Metadata Summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
        <h3 className="text-base font-semibold">Environment Variables Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="bg-gray-950 p-3 border border-gray-800 rounded space-y-1">
            <p className="text-gray-500 font-bold">Local AI Model</p>
            <p className="text-blue-400">Ollama qwen2.5:1.5b</p>
            <p className="text-[10px] text-gray-600">URL: http://ollama:11434 (in-network)</p>
          </div>
          <div className="bg-gray-950 p-3 border border-gray-800 rounded space-y-1">
            <p className="text-gray-500 font-bold">Active Database</p>
            <p className="text-green-400">PostgreSQL 15.5</p>
            <p className="text-[10px] text-gray-600">Connection: Bounded local socket</p>
          </div>
          <div className="bg-gray-950 p-3 border border-gray-800 rounded space-y-1">
            <p className="text-gray-500 font-bold">Inbox Scanner Route</p>
            <p className="text-purple-400">IMAP Gmail SSL Mode</p>
            <p className="text-[10px] text-gray-600">Tracking: Match sender domains</p>
          </div>
          <div className="bg-gray-950 p-3 border border-gray-800 rounded space-y-1">
            <p className="text-gray-500 font-bold">Scraping Loop Interval</p>
            <p className="text-emerald-400">Every 6 Hours</p>
            <p className="text-[10px] text-gray-600">Daemon: APScheduler Engine</p>
          </div>
        </div>
      </div>
    </div>
  )
}
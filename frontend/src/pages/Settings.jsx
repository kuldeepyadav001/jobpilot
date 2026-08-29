import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { triggerPipeline } from '../api/client'
import { fetchCookieHealth } from '../api/client'
export default function Settings() {
  const [log, setLog] = useState([])
  const [isRunning, setIsRunning] = useState(false)

  const runMutation = useMutation({
    mutationFn: triggerPipeline,
    onMutate: () => {
      setIsRunning(true)
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] Initializing background scrapers and LLM engines...`])
    },
    onSuccess: (data) => {
      setIsRunning(false)
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] SUCCESS: ${data.message}`])
    },
    onError: (err) => {
      setIsRunning(false)
      setLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${err.message || "Failed to complete pipeline runs."}`])
    }
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
          <h3 className="text-lg font-semibold text-blue-400">Manual Job Run</h3>
          <p className="text-xs text-gray-400 mt-1">
            Trigger the automatic scraper loop immediately. This will login using cookies, scrape Internshala + Naukri, score listings against your resumes, run the cover letter generator, and try to apply.
          </p>
        </div>

        <button
          onClick={() => runMutation.mutate()}
          disabled={isRunning}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-semibold disabled:opacity-30 transition"
        >
          {isRunning ? "Executing Pipeline..." : "Trigger Scrape & Apply Loop"}
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
            <p className="text-[10px] text-gray-600">URL: http://host.docker.internal:11434</p>
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
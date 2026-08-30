import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchResponses, triggerEmailScan } from '../api/client'
import { RefreshCw, Mail, ExternalLink } from 'lucide-react'

const TYPE_STYLES = {
  interview: 'bg-success text-white',
  rejection: 'bg-danger text-white',
  seen: 'bg-warn text-white',
  follow_up: 'bg-purple-600 text-white',
}

export default function Responses() {
  const queryClient = useQueryClient()
  const { data: responses = [], isLoading } = useQuery({ queryKey: ['responses'], queryFn: fetchResponses })
  const scanMutation = useMutation({
    mutationFn: triggerEmailScan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['responses'] }),
  })

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-ink">Email Responses</h2>
        <button onClick={() => scanMutation.mutate()} disabled={scanMutation.isPending} className="btn-primary">
          <RefreshCw className={`w-4 h-4 ${scanMutation.isPending ? 'animate-spin' : ''}`} />
          {scanMutation.isPending ? 'Scanning Inbox...' : 'Scan Inbox Now'}
        </button>
      </div>

      <p className="text-xs text-ink-faint">
        Auto-scanned every 6 hours via scheduler. Click "Scan Inbox Now" to check immediately. Configure Gmail App Password in .env for this to work.
      </p>

      {isLoading ? (
        <p className="text-ink-soft text-sm">Loading responses...</p>
      ) : responses.length === 0 ? (
        <div className="card p-8 text-center">
          <Mail className="w-10 h-10 text-ink-faint mx-auto mb-2" />
          <p className="text-ink-soft text-sm">No email responses detected yet.</p>
          <p className="text-ink-faint text-xs mt-2">Responses will appear here once Gmail IMAP is configured and recruiters reply.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {responses.map((r) => (
            <div key={r.id} className="card p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${TYPE_STYLES[r.response_type] || 'bg-surface3 text-ink-soft'}`}>{r.response_type}</span>
                    {!r.is_read && <span className="text-[10px] bg-brand text-white px-1.5 py-0.5 rounded">NEW</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-sm text-ink">{r.job_title}</h3>
                    {r.job_url && (
                      <a href={r.job_url} target="_blank" rel="noopener noreferrer" title="Open job on portal"
                        className="p-1 -m-1 text-ink-faint hover:text-brand hover:bg-brand-soft rounded transition">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                  <p className="text-ink-soft text-xs">{r.company_name}</p>
                </div>
                <span className="text-xs text-ink-faint">{r.received_at ? new Date(r.received_at).toLocaleString() : 'N/A'}</span>
              </div>
              {r.parsed_summary && <p className="text-ink-soft text-xs mt-2 bg-surface2 p-2 rounded">{r.parsed_summary}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

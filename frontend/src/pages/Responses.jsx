import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchResponses, triggerEmailScan } from '../api/client'

const TYPE_STYLES = {
  interview: 'bg-green-600 text-white',
  rejection: 'bg-red-600 text-white',
  seen: 'bg-yellow-600 text-white',
  follow_up: 'bg-purple-600 text-white',
}

export default function Responses() {
  const queryClient = useQueryClient()

  const { data: responses = [], isLoading } = useQuery({
    queryKey: ['responses'],
    queryFn: fetchResponses,
  })

  const scanMutation = useMutation({
    mutationFn: triggerEmailScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['responses'] })
    },
  })

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Email Responses</h2>
        <button
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.isPending}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-semibold disabled:opacity-50 transition"
        >
          {scanMutation.isPending ? 'Scanning Inbox...' : 'Scan Inbox Now'}
        </button>
      </div>

      <p className="text-xs text-gray-400">
        Auto-scanned every 6 hours via scheduler. Click "Scan Inbox Now" to check immediately.
        Configure Gmail App Password in .env for this to work.
      </p>

      {isLoading ? (
        <p className="text-gray-500 text-sm">Loading responses...</p>
      ) : responses.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-500 text-sm">No email responses detected yet.</p>
          <p className="text-gray-600 text-xs mt-2">
            Responses will appear here once Gmail IMAP is configured and recruiters reply.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {responses.map((r) => (
            <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${TYPE_STYLES[r.response_type] || 'bg-gray-700 text-gray-300'}`}>
                      {r.response_type}
                    </span>
                    {!r.is_read && <span className="text-[10px] bg-blue-500 text-white px-1.5 py-0.5 rounded">NEW</span>}
                  </div>
                  <h3 className="font-semibold text-sm">{r.job_title}</h3>
                  <p className="text-gray-400 text-xs">{r.company_name}</p>
                </div>
                <span className="text-xs text-gray-500">
                  {r.received_at ? new Date(r.received_at).toLocaleString() : 'N/A'}
                </span>
              </div>
              {r.parsed_summary && (
                <p className="text-gray-400 text-xs mt-2 bg-gray-950 p-2 rounded">{r.parsed_summary}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
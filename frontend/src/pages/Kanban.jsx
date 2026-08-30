import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { fetchApplications, updateAppStatus, updateAppNotes } from '../api/client'
import { Search, X, Save, ExternalLink, Check } from 'lucide-react'

const COLUMNS = [
  { id: 'applied', title: 'Applied', color: 'border-blue-500', accent: 'text-blue-600' },
  { id: 'viewed', title: 'Viewed', color: 'border-yellow-500', accent: 'text-yellow-600' },
  { id: 'responded', title: 'Responded', color: 'border-purple-500', accent: 'text-purple-600' },
  { id: 'interview', title: 'Interview', color: 'border-green-500', accent: 'text-green-600' },
  { id: 'offer', title: 'Offer', color: 'border-emerald-400', accent: 'text-emerald-600' },
  { id: 'rejected', title: 'Rejected', color: 'border-red-500', accent: 'text-red-600' },
  { id: 'pending', title: 'Pending', color: 'border-slate-400', accent: 'text-slate-600' },
  { id: 'needs_manual_action', title: 'Needs Action', color: 'border-orange-500', accent: 'text-orange-600' },
  { id: 'failed', title: 'Failed', color: 'border-rose-500', accent: 'text-rose-600' },
]

const STATUS_ACCENT = {
  applied: 'border-blue-400', viewed: 'border-yellow-400', responded: 'border-purple-400',
  interview: 'border-green-400', offer: 'border-emerald-400', rejected: 'border-red-400',
  pending: 'border-slate-300', needs_manual_action: 'border-orange-400', failed: 'border-rose-400',
}

export default function Kanban() {
  const queryClient = useQueryClient()
  const [selectedApp, setSelectedApp] = useState(null)
  const [query, setQuery] = useState('')
  const [notesDraft, setNotesDraft] = useState({})

  const { data: applications = [], isLoading } = useQuery({ queryKey: ['applications'], queryFn: fetchApplications })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }) => updateAppStatus(id, status),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      if (selectedApp && selectedApp.id === data.id) setSelectedApp(data)
    },
  })
  const notesMutation = useMutation({
    mutationFn: ({ id, notes }) => updateAppNotes(id, notes),
    onSuccess: (data) => { if (selectedApp && selectedApp.id === data.id) setSelectedApp(data) },
  })

  const onDragEnd = (result) => {
    const { destination, source, draggableId } = result
    if (!destination) return
    if (destination.droppableId === source.droppableId && destination.index === source.index) return
    statusMutation.mutate({ id: parseInt(draggableId, 10), status: destination.droppableId })
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return applications
    return applications.filter(a =>
      (a.job_title || '').toLowerCase().includes(q) || (a.company_name || '').toLowerCase().includes(q) || (a.method || '').toLowerCase().includes(q))
  }, [applications, query])

  if (isLoading) return <p className="text-ink-soft">Loading Kanban pipeline...</p>

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col relative">
      <div className="flex items-center justify-between mb-4 gap-4 flex-wrap">
        <h2 className="text-2xl font-bold text-ink shrink-0">Application Pipeline</h2>
        <div className="relative w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter by job, company, method…"
            className="input w-full pl-9 pr-9" />
          {query && <button onClick={() => setQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink"><X className="w-4 h-4" /></button>}
        </div>
        <span className="text-sm text-ink-faint shrink-0">{filtered.length} shown / {applications.length} total</span>
      </div>

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="grid grid-cols-9 gap-3 flex-1 overflow-x-auto min-w-[1400px]">
          {COLUMNS.map((col) => {
            const colApps = filtered.filter((a) => a.status === col.id)
            return (
              <div key={col.id} className="bg-surface2 border border-line rounded-xl flex flex-col h-full">
                <div className={`px-3 py-2 border-b border-line border-t-2 rounded-t-xl ${col.color} flex justify-between items-center`}>
                  <span className="font-semibold text-sm text-ink">{col.title}</span>
                  <span className="text-xs bg-surface text-ink-soft px-2 py-0.5 rounded-full">{colApps.length}</span>
                </div>
                <Droppable droppableId={col.id}>
                  {(provided, snapshot) => (
                    <div ref={provided.innerRef} {...provided.droppableProps}
                      className={`p-2 flex-1 overflow-y-auto space-y-2 transition-colors rounded-b-xl ${snapshot.isDraggingOver ? 'bg-brand-soft/60' : ''}`}>
                      {colApps.map((app, index) => (
                        <Draggable key={app.id} draggableId={String(app.id)} index={index}>
                          {(provided, snapshot) => (
                            <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}
                              onClick={() => { setSelectedApp(app); setNotesDraft({ [app.id]: app.notes || '' }) }}
                              className={`bg-surface border ${STATUS_ACCENT[app.status] || 'border-line'} rounded-lg p-3 text-xs shadow-sm hover:border-brand transition cursor-pointer ${snapshot.isDragging ? 'shadow-lg border-brand' : ''}`}>
                              <p className="font-bold text-ink mb-1 line-clamp-1">{app.job_title}</p>
                              <p className="text-ink-soft mb-2">{app.company_name}</p>
                              <div className="flex justify-between items-center text-[10px] text-ink-faint pt-1 border-t border-line">
                                <span className="uppercase">{app.method}</span>
                                <span>{new Date(app.applied_at).toLocaleDateString()}</span>
                              </div>
                              {app.status === 'needs_manual_action' && (
                                <div className="flex gap-1.5 pt-2" onClick={(e) => e.stopPropagation()}>
                                  {app.job_url && (
                                    <a href={app.job_url} target="_blank" rel="noopener noreferrer"
                                      className="flex-1 inline-flex items-center justify-center gap-1 px-1.5 py-1 bg-brand text-white rounded-md text-[10px] font-bold hover:bg-brand-strong transition">
                                      <ExternalLink className="w-3 h-3" /> Apply
                                    </a>
                                  )}
                                  <button onClick={() => statusMutation.mutate({ id: app.id, status: 'applied' })}
                                    className="flex-1 inline-flex items-center justify-center gap-1 px-1.5 py-1 bg-success/15 text-success rounded-md text-[10px] font-bold hover:bg-success/25 transition">
                                    <Check className="w-3 h-3" /> Done
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            )
          })}
        </div>
      </DragDropContext>

      {selectedApp && (
        <div className="fixed inset-0 bg-black/60 dark:bg-black/75 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="card w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-5 border-b border-line flex justify-between items-start bg-surface2">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-brand">Application Details</span>
                <h3 className="text-xl font-bold text-ink mt-1">{selectedApp.job_title}</h3>
                <p className="text-sm text-ink-soft">{selectedApp.company_name}</p>
              </div>
              <button onClick={() => setSelectedApp(null)} className="text-ink-faint hover:text-ink text-xl font-bold bg-surface3 hover:bg-surface2 w-8 h-8 rounded-full flex items-center justify-center transition">×</button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-sm">
              {selectedApp.status === 'needs_manual_action' && (
                <div className="bg-warn/10 border border-warn/30 text-warn rounded-xl p-3.5 text-xs leading-relaxed">
                  <strong className="font-bold">Needs your action.</strong> JobPilot couldn't auto-apply to this one
                  (it links out to an external/company site, or that portal's auto-apply isn't built yet).
                  Open the job, apply manually, then click <strong>Mark Applied</strong> to move it out of "Needs Action".
                </div>
              )}
              <div className="grid grid-cols-3 gap-4 bg-surface2 p-3.5 border border-line rounded-lg">
                <div>
                  <p className="label">Channel</p>
                  <p className="text-sm font-semibold text-ink mt-0.5 uppercase">{selectedApp.method}</p>
                </div>
                <div>
                  <p className="label">Applied</p>
                  <p className="text-sm font-semibold text-ink mt-0.5">{new Date(selectedApp.applied_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="label">Status</p>
                  <select value={selectedApp.status}
                    onChange={(e) => statusMutation.mutate({ id: selectedApp.id, status: e.target.value })}
                    className="input mt-0.5 w-full text-xs">
                    {COLUMNS.map(col => <option key={col.id} value={col.id}>{col.title}</option>)}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <p className="label uppercase tracking-wide">Cover Letter</p>
                <div className="bg-surface2 border border-line rounded-lg p-4 font-mono text-xs text-ink-soft leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {selectedApp.cover_letter || "No cover letter recorded."}
                </div>
              </div>

              <div className="space-y-1.5">
                <p className="label uppercase tracking-wide">Notes</p>
                <textarea value={notesDraft[selectedApp.id] ?? selectedApp.notes ?? ''}
                  onChange={(e) => setNotesDraft(prev => ({ ...prev, [selectedApp.id]: e.target.value }))}
                  rows={3} placeholder="Add notes about this application…"
                  className="input w-full" />
                <button onClick={() => notesMutation.mutate({ id: selectedApp.id, notes: notesDraft[selectedApp.id] ?? '' })}
                  className="btn-primary text-xs">
                  <Save className="w-3.5 h-3.5" /> Save Notes
                </button>
              </div>
            </div>

            <div className="p-4 bg-surface2 border-t border-line flex items-center justify-between">
              <div className="flex gap-2">
                {selectedApp.job_url && (
                  <a href={selectedApp.job_url} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs">
                    <ExternalLink className="w-3.5 h-3.5" /> Open Job
                  </a>
                )}
                {selectedApp.status === 'needs_manual_action' && (
                  <button onClick={() => statusMutation.mutate({ id: selectedApp.id, status: 'applied' })}
                    className="btn-primary text-xs"><Check className="w-3.5 h-3.5" /> Mark Applied</button>
                )}
              </div>
              <button onClick={() => setSelectedApp(null)} className="btn-ghost text-xs">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

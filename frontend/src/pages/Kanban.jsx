import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { fetchApplications, updateAppStatus, updateAppNotes } from '../api/client'
import { Search, X, Save } from 'lucide-react'

const COLUMNS = [
  { id: 'applied', title: 'Applied', color: 'border-blue-500', bg: 'bg-blue-50/60', accent: 'text-blue-600' },
  { id: 'viewed', title: 'Viewed', color: 'border-yellow-500', bg: 'bg-yellow-50/60', accent: 'text-yellow-600' },
  { id: 'responded', title: 'Responded', color: 'border-purple-500', bg: 'bg-purple-50/60', accent: 'text-purple-600' },
  { id: 'interview', title: 'Interview', color: 'border-green-500', bg: 'bg-green-50/60', accent: 'text-green-600' },
  { id: 'offer', title: 'Offer', color: 'border-emerald-400', bg: 'bg-emerald-50/60', accent: 'text-emerald-600' },
  { id: 'rejected', title: 'Rejected', color: 'border-red-500', bg: 'bg-red-50/60', accent: 'text-red-600' },
  { id: 'pending', title: 'Pending', color: 'border-slate-500', bg: 'bg-slate-50/60', accent: 'text-slate-600' },
  { id: 'needs_manual_action', title: 'Needs Action', color: 'border-orange-500', bg: 'bg-orange-50/60', accent: 'text-orange-600' },
  { id: 'failed', title: 'Failed', color: 'border-rose-500', bg: 'bg-rose-50/60', accent: 'text-rose-600' },
]

const STATUS_ACCENT = {
  applied: 'border-blue-400',
  viewed: 'border-yellow-400',
  responded: 'border-purple-400',
  interview: 'border-green-400',
  offer: 'border-emerald-400',
  rejected: 'border-red-400',
  pending: 'border-slate-300',
  needs_manual_action: 'border-orange-400',
  failed: 'border-rose-400',
}

export default function Kanban() {
  const queryClient = useQueryClient()
  const [selectedApp, setSelectedApp] = useState(null)
  const [query, setQuery] = useState('')
  const [notesDraft, setNotesDraft] = useState({})

  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: fetchApplications,
  })

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
    onSuccess: (data) => {
      if (selectedApp && selectedApp.id === data.id) setSelectedApp(data)
    },
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
      (a.job_title || '').toLowerCase().includes(q) ||
      (a.company_name || '').toLowerCase().includes(q) ||
      (a.method || '').toLowerCase().includes(q)
    )
  }, [applications, query])

  if (isLoading) return <p className="text-gray-500">Loading Kanban pipeline...</p>

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col relative">
      <div className="flex items-center justify-between mb-4 gap-4">
        <h2 className="text-2xl font-bold text-slate-800 shrink-0">Application Pipeline</h2>
        <div className="relative w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by job, company, method…"
            className="w-full bg-white border border-slate-200 rounded-full py-2 pl-9 pr-9 text-xs font-medium text-slate-700 focus:border-indigo-300 focus:ring-3 focus:ring-indigo-50 outline-none"
          />
          {query && <button onClick={() => setQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500"><X className="w-4 h-4" /></button>}
        </div>
        <span className="text-sm text-slate-400 shrink-0">{filtered.length} shown / {applications.length} total</span>
      </div>

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="grid grid-cols-9 gap-3 flex-1 overflow-x-auto min-w-[1400px]">
          {COLUMNS.map((col) => {
            const colApps = filtered.filter((a) => a.status === col.id)
            return (
              <div key={col.id} className={`bg-gray-900 border border-gray-800 rounded-lg flex flex-col h-full`}>
                <div className={`px-3 py-2 border-b border-gray-800 border-t-2 ${col.color} flex justify-between items-center`}>
                  <span className="font-semibold text-sm text-gray-100">{col.title}</span>
                  <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">{colApps.length}</span>
                </div>
                <Droppable droppableId={col.id}>
                  {(provided, snapshot) => (
                    <div ref={provided.innerRef} {...provided.droppableProps}
                      className={`p-2 flex-1 overflow-y-auto space-y-2 transition-colors ${snapshot.isDraggingOver ? 'bg-gray-800/50' : ''}`}>
                      {colApps.map((app, index) => (
                        <Draggable key={app.id} draggableId={String(app.id)} index={index}>
                          {(provided, snapshot) => (
                            <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}
                              onClick={() => { setSelectedApp(app); setNotesDraft({ [app.id]: app.notes || '' }) }}
                              className={`bg-gray-950 border ${STATUS_ACCENT[app.status] || 'border-gray-800'} rounded p-3 text-xs shadow-sm hover:border-gray-500 transition cursor-pointer ${snapshot.isDragging ? 'shadow-lg border-blue-500' : ''}`}>
                              <p className="font-bold text-gray-100 mb-1 line-clamp-1">{app.job_title}</p>
                              <p className="text-gray-400 mb-2">{app.company_name}</p>
                              <div className="flex justify-between items-center text-[10px] text-gray-500 pt-1 border-t border-gray-900">
                                <span className="uppercase">{app.method}</span>
                                <span>{new Date(app.applied_at).toLocaleDateString()}</span>
                              </div>
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
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh] text-slate-800">
            <div className="p-5 border-b border-slate-200 flex justify-between items-start bg-slate-50">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-indigo-500">Application Details</span>
                <h3 className="text-xl font-bold mt-1">{selectedApp.job_title}</h3>
                <p className="text-sm text-slate-500">{selectedApp.company_name}</p>
              </div>
              <button onClick={() => setSelectedApp(null)}
                className="text-slate-400 hover:text-slate-700 text-xl font-bold bg-slate-100 hover:bg-slate-200 w-8 h-8 rounded-full flex items-center justify-center transition">×</button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-sm">
              <div className="grid grid-cols-3 gap-4 bg-slate-50 p-3.5 border border-slate-200 rounded">
                <div>
                  <p className="text-xs text-slate-400 uppercase font-semibold">Channel</p>
                  <p className="text-sm font-semibold text-slate-700 mt-0.5 uppercase">{selectedApp.method}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 uppercase font-semibold">Applied</p>
                  <p className="text-sm font-semibold text-slate-700 mt-0.5">{new Date(selectedApp.applied_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 uppercase font-semibold">Status</p>
                  <select value={selectedApp.status}
                    onChange={(e) => statusMutation.mutate({ id: selectedApp.id, status: e.target.value })}
                    className="bg-white border border-slate-200 text-xs text-indigo-600 font-semibold rounded px-2.5 py-1 focus:outline-none focus:border-indigo-400 mt-0.5 w-full">
                    {COLUMNS.map(col => <option key={col.id} value={col.id}>{col.title}</option>)}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">Cover Letter</p>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-xs text-slate-600 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {selectedApp.cover_letter || "No cover letter recorded."}
                </div>
              </div>

              <div className="space-y-1.5">
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">Notes</p>
                <textarea
                  value={notesDraft[selectedApp.id] ?? selectedApp.notes ?? ''}
                  onChange={(e) => setNotesDraft(prev => ({ ...prev, [selectedApp.id]: e.target.value }))}
                  rows={3}
                  placeholder="Add notes about this application…"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700 focus:border-indigo-300 outline-none"
                />
                <button
                  onClick={() => notesMutation.mutate({ id: selectedApp.id, notes: notesDraft[selectedApp.id] ?? '' })}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold">
                  <Save className="w-3.5 h-3.5" /> Save Notes
                </button>
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button onClick={() => setSelectedApp(null)}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded text-xs font-semibold transition">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

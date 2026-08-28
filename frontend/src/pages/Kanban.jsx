import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { fetchApplications, updateAppStatus } from '../api/client'

const COLUMNS = [
  { id: 'applied', title: 'Applied', color: 'border-blue-500' },
  { id: 'viewed', title: 'Viewed', color: 'border-yellow-500' },
  { id: 'responded', title: 'Responded', color: 'border-purple-500' },
  { id: 'interview', title: 'Interview', color: 'border-green-500' },
  { id: 'offer', title: 'Offer', color: 'border-emerald-400' },
  { id: 'rejected', title: 'Rejected', color: 'border-red-500' },
]

export default function Kanban() {
  const queryClient = useQueryClient()
  const [selectedApp, setSelectedApp] = useState(null)

  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: fetchApplications,
  })

  const mutation = useMutation({
    mutationFn: ({ id, status }) => updateAppStatus(id, status),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      // Keep modal in sync if updated from inside
      if (selectedApp && selectedApp.id === data.id) {
        setSelectedApp(data)
      }
    },
  })

  const onDragEnd = (result) => {
    const { destination, source, draggableId } = result
    if (!destination) return
    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return
    }

    const appId = parseInt(draggableId, 10)
    const newStatus = destination.droppableId

    mutation.mutate({ id: appId, status: newStatus })
  }

  if (isLoading) {
    return <p className="text-gray-500">Loading Kanban pipeline...</p>
  }

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col relative">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Application Pipeline</h2>
        <span className="text-sm text-gray-400">
          Total Applications: {applications.length}
        </span>
      </div>

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="grid grid-cols-6 gap-3 flex-1 overflow-x-auto min-w-[1000px]">
          {COLUMNS.map((col) => {
            const colApps = applications.filter((a) => a.status === col.id)
            return (
              <div
                key={col.id}
                className="bg-gray-900 border border-gray-800 rounded-lg flex flex-col h-full"
              >
                {/* Column Header */}
                <div
                  className={`px-3 py-2 border-b border-gray-800 border-t-2 ${col.color} flex justify-between items-center`}
                >
                  <span className="font-semibold text-sm">{col.title}</span>
                  <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                    {colApps.length}
                  </span>
                </div>

                {/* Drop Area */}
                <Droppable droppableId={col.id}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={`p-2 flex-1 overflow-y-auto space-y-2 transition-colors ${
                        snapshot.isDraggingOver ? 'bg-gray-800/50' : ''
                      }`}
                    >
                      {colApps.map((app, index) => (
                        <Draggable
                          key={app.id}
                          draggableId={String(app.id)}
                          index={index}
                        >
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              onClick={() => setSelectedApp(app)} // OPEN DETAIL MODAL ON CLICK
                              className={`bg-gray-950 border border-gray-800 rounded p-3 text-xs shadow-sm hover:border-gray-600 transition cursor-pointer ${
                                snapshot.isDragging ? 'shadow-lg border-blue-500' : ''
                              }`}
                            >
                              <p className="font-bold text-gray-100 mb-1 line-clamp-1">
                                {app.job_title}
                              </p>
                              <p className="text-gray-400 mb-2">{app.company_name}</p>
                              <div className="flex justify-between items-center text-[10px] text-gray-500 pt-1 border-t border-gray-900">
                                <span className="uppercase">{app.method}</span>
                                <span>
                                  {new Date(app.applied_at).toLocaleDateString()}
                                </span>
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

      {/* --- APPLICATION DETAIL OVERLAY MODAL --- */}
      {selectedApp && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50 p-4 backdrop-blur-xs">
          <div className="bg-gray-900 border border-gray-800 rounded-lg w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh]">
            {/* Header */}
            <div className="p-5 border-b border-gray-800 flex justify-between items-start">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-blue-400">Application Details</span>
                <h3 className="text-xl font-bold text-gray-100 mt-1">{selectedApp.job_title}</h3>
                <p className="text-sm text-gray-400">{selectedApp.company_name}</p>
              </div>
              <button
                onClick={() => setSelectedApp(null)}
                className="text-gray-400 hover:text-white text-xl font-bold bg-gray-800 hover:bg-gray-700 w-8 h-8 rounded-full flex items-center justify-center transition"
              >
                ×
              </button>
            </div>

            {/* Scrollable Body content */}
            <div className="p-6 overflow-y-auto space-y-5 text-sm">
              <div className="grid grid-cols-3 gap-4 bg-gray-950 p-3.5 border border-gray-800 rounded">
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold">Applied Channel</p>
                  <p className="text-sm font-semibold text-gray-200 mt-0.5 uppercase">{selectedApp.method}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold">Applied Date</p>
                  <p className="text-sm font-semibold text-gray-200 mt-0.5">
                    {new Date(selectedApp.applied_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold">Change Status</p>
                  <select
                    value={selectedApp.status}
                    onChange={(e) => mutation.mutate({ id: selectedApp.id, status: e.target.value })}
                    className="bg-gray-900 border border-gray-800 text-xs text-blue-400 font-semibold rounded px-2.5 py-1 focus:outline-none focus:border-blue-500 mt-0.5"
                  >
                    {COLUMNS.map(col => (
                      <option key={col.id} value={col.id}>{col.title}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Generated Cover Letter section */}
              <div className="space-y-1.5">
                <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide">Tailored Cover Letter Generated</p>
                <div className="bg-gray-950 border border-gray-800/80 rounded-lg p-4 font-mono text-xs text-gray-300 leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap">
                  {selectedApp.cover_letter || "No cover letter was recorded for this application."}
                </div>
              </div>
            </div>

            {/* Footer actions */}
            <div className="p-4 bg-gray-950 border-t border-gray-800 flex justify-end">
              <button
                onClick={() => setSelectedApp(null)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded text-xs font-semibold transition"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchResumes, uploadResume, deleteResume } from '../api/client'
import { FileText, Upload, Trash2 } from 'lucide-react'

export default function Resumes() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [tags, setTags] = useState('')
  const [file, setFile] = useState(null)
  const [uploadError, setUploadError] = useState('')

  const { data: resumes = [], isLoading } = useQuery({ queryKey: ['resumes'], queryFn: fetchResumes })

  const uploadMutation = useMutation({
    mutationFn: (formData) => uploadResume(formData),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['resumes'] }); setName(''); setTags(''); setFile(null); setUploadError('') },
    onError: (err) => setUploadError(err.response?.data?.detail || 'Failed to upload resume'),
  })
  const deleteMutation = useMutation({
    mutationFn: (id) => deleteResume(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resumes'] }),
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!file || !name.trim()) { setUploadError('Please provide a resume name and select a file.'); return }
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    formData.append('tags', tags)
    uploadMutation.mutate(formData)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <h2 className="text-2xl font-bold text-ink">Resume Management</h2>

      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4 text-brand">Upload New Resume</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label mb-1 block">Resume Name / Target Role</label>
              <input type="text" placeholder="e.g. Python Backend Engineer" value={name} onChange={(e) => setName(e.target.value)} className="input w-full" />
            </div>
            <div>
              <label className="label mb-1 block">Tags (comma-separated)</label>
              <input type="text" placeholder="python, fastapi, backend, postgres" value={tags} onChange={(e) => setTags(e.target.value)} className="input w-full" />
            </div>
          </div>

          <div>
            <label className="label mb-1 block">Resume File (.pdf, .docx)</label>
            <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-sm text-ink-soft file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand file:text-white hover:file:bg-brand-strong cursor-pointer file:transition" />
          </div>

          {uploadError && <p className="text-xs text-danger">{uploadError}</p>}

          <button type="submit" disabled={uploadMutation.isPending} className="btn-primary">
            <Upload className="w-4 h-4" /> {uploadMutation.isPending ? 'Uploading & Parsing...' : 'Upload & Parse Resume'}
          </button>
        </form>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4 text-ink">Active Resumes ({resumes.length})</h3>
        {isLoading ? (
          <p className="text-ink-soft text-sm">Loading resumes...</p>
        ) : resumes.length === 0 ? (
          <p className="text-ink-soft text-sm">No resumes uploaded yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resumes.map((resume) => (
              <div key={resume.id} className="card p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-base text-ink flex items-center gap-2">
                      <FileText className="w-4 h-4 text-brand" /> {resume.name}
                    </span>
                    <span className="text-[10px] uppercase bg-surface3 text-ink-soft px-2 py-0.5 rounded font-mono">{resume.file_type}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {resume.tags && resume.tags.map((t, idx) => <span key={idx} className="tag">{t}</span>)}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-ink-faint pt-3 border-t border-line">
                  <span>Uploaded: {new Date(resume.created_at).toLocaleDateString()}</span>
                  <button onClick={() => deleteMutation.mutate(resume.id)} className="text-danger hover:text-danger/80 hover:underline flex items-center gap-1">
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

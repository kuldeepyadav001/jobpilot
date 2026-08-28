import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchResumes, uploadResume, deleteResume } from '../api/client'

export default function Resumes() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [tags, setTags] = useState('')
  const [file, setFile] = useState(null)
  const [uploadError, setUploadError] = useState('')

  const { data: resumes = [], isLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: fetchResumes,
  })

  const uploadMutation = useMutation({
    mutationFn: (formData) => uploadResume(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      setName('')
      setTags('')
      setFile(null)
      setUploadError('')
    },
    onError: (err) => {
      setUploadError(err.response?.data?.detail || 'Failed to upload resume')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!file || !name.trim()) {
      setUploadError('Please provide a resume name and select a file.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    formData.append('tags', tags)

    uploadMutation.mutate(formData)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <h2 className="text-2xl font-bold">Resume Management</h2>

      {/* Upload Section */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-blue-400">Upload New Resume</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Resume Name / Target Role</label>
              <input
                type="text"
                placeholder="e.g. Python Backend Engineer"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                placeholder="python, fastapi, backend, postgres"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Resume File (.pdf, .docx)</label>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
            />
          </div>

          {uploadError && <p className="text-xs text-red-500">{uploadError}</p>}

          <button
            type="submit"
            disabled={uploadMutation.isPending}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition disabled:opacity-50"
          >
            {uploadMutation.isPending ? 'Uploading & Parsing...' : 'Upload & Parse Resume'}
          </button>
        </form>
      </div>

      {/* Resume List */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Active Resumes ({resumes.length})</h3>
        {isLoading ? (
          <p className="text-gray-500 text-sm">Loading resumes...</p>
        ) : resumes.length === 0 ? (
          <p className="text-gray-500 text-sm">No resumes uploaded yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-base text-gray-100">{resume.name}</span>
                    <span className="text-[10px] uppercase bg-gray-800 text-gray-400 px-2 py-0.5 rounded font-mono">
                      {resume.file_type}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {resume.tags && resume.tags.map((t, idx) => (
                      <span key={idx} className="text-[10px] bg-blue-950 text-blue-400 border border-blue-800/40 px-2 py-0.5 rounded-full">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-800">
                  <span>Uploaded: {new Date(resume.created_at).toLocaleDateString()}</span>
                  <button
                    onClick={() => deleteMutation.mutate(resume.id)}
                    className="text-red-400 hover:text-red-300 hover:underline"
                  >
                    Delete
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
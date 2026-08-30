import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})
export const fetchCookieHealth = () => api.get('/settings/cookie-health').then(r => r.data)
export const fetchAppSettings = () => api.get('/settings/app').then(r => r.data)
export const fetchJobs = (params) => api.get('/jobs', { params }).then(r => r.data)
export const fetchApplications = () => api.get('/applications').then(r => r.data)
export const updateAppStatus = (id, status) => api.patch(`/applications/${id}/status`, { status }).then(r => r.data)
export const updateAppNotes = (id, notes) => api.patch(`/applications/${id}/notes`, { notes }).then(r => r.data)
export const fetchResumes = () => api.get('/resumes').then(r => r.data)
export const uploadResume = (formData) => api.post('/resumes', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
export const deleteResume = (id) => api.delete(`/resumes/${id}`)
export const fetchDashboard = () => api.get('/analytics/dashboard').then(r => r.data)
export const fetchSnapshots = () => api.get('/analytics/snapshots').then(r => r.data)
export const fetchSystemHealth = () => api.get('/system/health').then(r => r.data)
export const fetchMetricsText = () => api.get('/metrics').then(r => r.data)
export const fetchResponses = () => api.get('/responses').then(r => r.data)
export const triggerEmailScan = () => api.post('/responses/scan').then(r => r.data)
// Pipeline now runs in the background; POST returns immediately, GET polls status.
export const triggerPipeline = () => api.post('/pipeline/run').then(r => r.data)
export const fetchPipelineStatus = () => api.get('/pipeline/status').then(r => r.data)

export default api
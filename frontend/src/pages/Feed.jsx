import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { fetchJobs } from '../api/client'
import { Search, ExternalLink, CheckCircle, ChevronDown, ChevronUp, MapPin, Building2, DollarSign } from 'lucide-react'

function ScoreBadge({ score }) {
  if (score == null) return <span className="text-xs text-ink-faint bg-surface2 px-2 py-1 rounded-md font-semibold">N/A</span>
  const color = score >= 40 ? 'bg-success/10 text-success border-success/30' : score >= 20 ? 'bg-warn/10 text-warn border-warn/30' : 'bg-danger/10 text-danger border-danger/30'
  return <span className={`text-xs px-2.5 py-1 rounded-lg border font-black flex items-center gap-1 ${color}`}>
    <span>{score}%</span><span className="text-[10px] font-semibold opacity-75">match</span>
  </span>
}

export default function Feed() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState(searchParams.get('q') || '')
  const [portal, setPortal] = useState('')
  const [minScore, setMinScore] = useState('')
  const [expandedJobId, setExpandedJobId] = useState(null)

  useEffect(() => {
    const q = searchParams.get('q')
    if (q != null) { setSearch(q); setPage(1) }
  }, [searchParams])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['jobs', page, search, portal, minScore],
    queryFn: () => fetchJobs({
      page, page_size: 15,
      search: search || undefined, portal: portal || undefined,
      min_score: minScore ? parseFloat(minScore) : undefined,
    }),
    retry: false,
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-black text-ink tracking-tight">Job Feed</h2>
          <p className="text-xs font-semibold text-ink-faint mt-0.5">
            {data?.total ? `${data.total} total jobs discovered across all portals` : 'Browse and inspect scraped opportunities'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
            <input type="text" placeholder="Search keyword..." value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="input pl-9 w-48" />
          </div>
          <select value={portal} onChange={e => { setPortal(e.target.value); setPage(1) }} className="input cursor-pointer">
            <option value="">All Portals</option>
            <option value="internshala">Internshala</option>
            <option value="naukri">Naukri</option>
          </select>
          <select value={minScore} onChange={e => { setMinScore(e.target.value); setPage(1) }} className="input cursor-pointer">
            <option value="">All Match Scores</option>
            <option value="20">20%+ Match</option>
            <option value="40">40%+ Match</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(n => (
            <div key={n} className="card p-6 animate-pulse space-y-3">
              <div className="h-4 bg-surface3 rounded w-1/3"></div>
              <div className="h-3 bg-surface3 rounded w-1/4"></div>
              <div className="h-12 bg-surface2 rounded"></div>
            </div>
          ))}
        </div>
      ) : isError || !data?.jobs || data.jobs.length === 0 ? (
        <div className="card p-12 text-center">
          <Building2 className="w-12 h-12 text-ink-faint mx-auto mb-3" />
          <h3 className="text-base font-bold text-ink">No Jobs Found</h3>
          <p className="text-xs text-ink-faint mt-1 max-w-sm mx-auto">
            {isError ? "Backend is offline. Start Docker to load live jobs." : "Try adjusting your search filters or trigger a new scraping run in Settings."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.jobs.map(job => {
            const isExpanded = expandedJobId === job.id
            return (
              <div key={job.id} className="card p-6 hover:shadow-lg hover:-translate-y-0.5 hover:border-brand/40 transition-all duration-200">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-4 min-w-0">
                    <div className="w-12 h-12 bg-brand-soft rounded-xl flex items-center justify-center shrink-0">
                      <span className="text-xs font-black uppercase text-brand tracking-wider">{job.portal === 'internshala' ? 'IS' : 'NK'}</span>
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <ScoreBadge score={job.match_score} />
                        <span className="text-[10px] uppercase font-bold text-ink-faint bg-surface2 px-2 py-0.5 rounded">{job.portal}</span>
                        {job.is_applied && (
                          <span className="text-[10px] font-bold bg-brand-soft text-brand px-2 py-0.5 rounded-full flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> Applied
                          </span>
                        )}
                      </div>
                      <h3 className="font-extrabold text-base text-ink">{job.title}</h3>
                      <div className="flex items-center gap-4 text-xs font-semibold text-ink-faint mt-1 flex-wrap">
                        <span className="flex items-center gap-1 text-ink"><Building2 className="w-3.5 h-3.5 text-ink-faint" /> {job.company_name}</span>
                        <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-ink-faint" /> {job.location || 'Remote'}</span>
                        {job.salary_min && (
                          <span className="flex items-center gap-1 text-success font-bold">
                            <DollarSign className="w-3.5 h-3.5" /> ₹{job.salary_min.toLocaleString()} {job.salary_max ? `- ₹${job.salary_max.toLocaleString()}` : ''}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <a href={job.url} target="_blank" rel="noopener noreferrer" className="p-2 text-ink-faint hover:text-brand hover:bg-brand-soft rounded-xl transition-all" title="Open on Portal">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {job.description && (
                  <div className="mt-4 pt-4 border-t border-line">
                    <p className={`text-xs text-ink-soft font-medium leading-relaxed ${!isExpanded ? 'line-clamp-2' : ''}`}>{job.description}</p>
                    <button onClick={() => setExpandedJobId(isExpanded ? null : job.id)} className="mt-2 text-brand hover:text-brand-strong text-xs font-bold flex items-center gap-1">
                      {isExpanded ? <>Show Less <ChevronUp className="w-3.5 h-3.5" /></> : <>Read Full Description <ChevronDown className="w-3.5 h-3.5" /></>}
                    </button>
                  </div>
                )}
              </div>
            )
          })}

          <div className="flex items-center justify-between pt-6">
            <p className="text-xs font-bold text-ink-faint">Showing Page {page} of {Math.ceil((data?.total || 0) / 15)}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-ghost">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 15 >= (data?.total || 0)} className="btn-ghost">Next</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

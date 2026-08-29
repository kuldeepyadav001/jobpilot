import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchJobs } from '../api/client'
import { Search, Filter, ExternalLink, CheckCircle, ArrowUpDown, ChevronDown, ChevronUp, MapPin, Building2, DollarSign } from 'lucide-react'

function ScoreBadge({ score }) {
  if (score == null) return <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded-md font-semibold">N/A</span>
  const color = score >= 40 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : score >= 20 ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-rose-50 text-rose-700 border-rose-200'
  return (
    <span className={`text-xs px-2.5 py-1 rounded-lg border font-black flex items-center gap-1 ${color}`}>
      <span>{score}%</span>
      <span className="text-[10px] font-semibold opacity-75">match</span>
    </span>
  )
}

export default function Feed() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [portal, setPortal] = useState('')
  const [minScore, setMinScore] = useState('')
  const [expandedJobId, setExpandedJobId] = useState(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['jobs', page, search, portal, minScore],
    queryFn: () => fetchJobs({ 
      page, 
      page_size: 15, 
      search: search || undefined, 
      portal: portal || undefined,
      min_score: minScore ? parseFloat(minScore) : undefined
    }),
    retry: false
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 tracking-tight">Job Feed</h2>
          <p className="text-xs font-semibold text-slate-400 mt-0.5">
            {data?.total ? `${data.total} total jobs discovered across all portals` : 'Browse and inspect scraped opportunities'}
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search keyword..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="bg-white border border-slate-200 rounded-xl py-2 pl-9 pr-3 text-xs font-semibold text-slate-700 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none w-48 shadow-2xs"
            />
          </div>

          <select
            value={portal}
            onChange={e => { setPortal(e.target.value); setPage(1) }}
            className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:border-indigo-500 outline-none shadow-2xs cursor-pointer"
          >
            <option value="">All Portals</option>
            <option value="internshala">Internshala</option>
            <option value="naukri">Naukri</option>
          </select>

          <select
            value={minScore}
            onChange={e => { setMinScore(e.target.value); setPage(1) }}
            className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:border-indigo-500 outline-none shadow-2xs cursor-pointer"
          >
            <option value="">All Match Scores</option>
            <option value="20">20%+ Match</option>
            <option value="40">40%+ Match</option>
          </select>
        </div>
      </div>

      {/* Job Cards Stream */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(n => (
            <div key={n} className="bg-white rounded-2xl p-6 shadow-2xs border border-slate-100 animate-pulse space-y-3">
              <div className="h-4 bg-slate-100 rounded w-1/3"></div>
              <div className="h-3 bg-slate-100 rounded w-1/4"></div>
              <div className="h-12 bg-slate-50 rounded"></div>
            </div>
          ))}
        </div>
      ) : isError || !data?.jobs || data.jobs.length === 0 ? (
        <div className="bg-white border border-slate-100 rounded-2xl p-12 text-center shadow-2xs">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-700">No Jobs Found</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            {isError ? "Backend is offline. Start Docker to load live jobs." : "Try adjusting your search filters or trigger a new scraping run in Settings."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.jobs.map(job => {
            const isExpanded = expandedJobId === job.id
            return (
              <div 
                key={job.id} 
                className="bg-white border border-slate-100 hover:border-indigo-100 rounded-2xl p-6 shadow-2xs hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-4">
                    {/* Portal Logo Box */}
                    <div className="w-12 h-12 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-center shrink-0">
                      <span className="text-xs font-black uppercase text-indigo-600 tracking-wider">
                        {job.portal === 'internshala' ? 'IS' : 'NK'}
                      </span>
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <ScoreBadge score={job.match_score} />
                        <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-50 px-2 py-0.5 rounded">
                          {job.portal}
                        </span>
                        {job.is_applied && (
                          <span className="text-[10px] font-bold bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> Applied
                          </span>
                        )}
                      </div>

                      <h3 className="font-extrabold text-base text-slate-800 hover:text-indigo-600 transition-colors">
                        {job.title}
                      </h3>

                      <div className="flex items-center gap-4 text-xs font-semibold text-slate-500 mt-1">
                        <span className="flex items-center gap-1 text-slate-700">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" /> {job.company_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" /> {job.location || 'Remote'}
                        </span>
                        {job.salary_min && (
                          <span className="flex items-center gap-1 text-emerald-600 font-bold">
                            <DollarSign className="w-3.5 h-3.5" /> ₹{job.salary_min.toLocaleString()} {job.salary_max ? `- ₹${job.salary_max.toLocaleString()}` : ''}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                      title="Open on Portal"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {/* Job Description Expandable */}
                {job.description && (
                  <div className="mt-4 pt-4 border-t border-slate-50">
                    <p className={`text-xs text-slate-500 font-medium leading-relaxed ${!isExpanded ? 'line-clamp-2' : ''}`}>
                      {job.description}
                    </p>
                    <button
                      onClick={() => setExpandedJobId(isExpanded ? null : job.id)}
                      className="mt-2 text-indigo-600 hover:text-indigo-700 text-xs font-bold flex items-center gap-1"
                    >
                      {isExpanded ? <>Show Less <ChevronUp className="w-3.5 h-3.5" /></> : <>Read Full Description <ChevronDown className="w-3.5 h-3.5" /></>}
                    </button>
                  </div>
                )}
              </div>
            )
          })}

          {/* Pagination */}
          <div className="flex items-center justify-between pt-6">
            <p className="text-xs font-bold text-slate-400">
              Showing Page {page} of {Math.ceil((data?.total || 0) / 15)}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 disabled:opacity-40 hover:bg-slate-50 transition"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 15 >= (data?.total || 0)}
                className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 disabled:opacity-40 hover:bg-slate-50 transition"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchJobs } from '../api/client'

function ScoreBadge({ score }) {
  if (score == null) return <span className="text-gray-500 text-xs">N/A</span>
  const color = score >= 50 ? 'bg-green-600' : score >= 25 ? 'bg-yellow-600' : 'bg-red-600'
  return <span className={`${color} text-white text-xs px-2 py-0.5 rounded-full font-bold`}>{score}%</span>
}

export default function Feed() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [portal, setPortal] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['jobs', page, search, portal],
    queryFn: () => fetchJobs({ page, page_size: 15, search: search || undefined, portal: portal || undefined }),
  })

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-2xl font-bold">Job Feed</h2>
        <input
          type="text"
          placeholder="Search jobs..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:border-blue-500"
        />
        <select
          value={portal}
          onChange={e => { setPortal(e.target.value); setPage(1) }}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none"
        >
          <option value="">All Portals</option>
          <option value="internshala">Internshala</option>
          <option value="naukri">Naukri</option>
        </select>
      </div>

      {isLoading ? (
        <p className="text-gray-500">Loading jobs...</p>
      ) : (
        <>
          <p className="text-sm text-gray-400 mb-4">{data?.total} jobs found</p>
          <div className="space-y-3">
            {data?.jobs?.map(job => (
              <div key={job.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <ScoreBadge score={job.match_score} />
                      <span className="text-xs text-gray-500 uppercase">{job.portal}</span>
                      {job.is_applied && <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded">Applied</span>}
                    </div>
                    <h3 className="font-semibold text-lg">{job.title}</h3>
                    <p className="text-gray-400 text-sm">{job.company_name} · {job.location}</p>
                    {job.salary_min && (
                      <p className="text-green-400 text-sm mt-1">₹{job.salary_min.toLocaleString()} - ₹{job.salary_max?.toLocaleString()}</p>
                    )}
                  </div>
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 text-sm hover:underline shrink-0 ml-4"
                  >
                    View →
                  </a>
                </div>
                {job.description && (
                  <p className="text-gray-500 text-xs mt-2 line-clamp-2">{job.description}</p>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-4 mt-6 justify-center">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-gray-800 rounded disabled:opacity-30 hover:bg-gray-700 text-sm"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-400">Page {page} of {Math.ceil((data?.total || 0) / 15)}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 15 >= (data?.total || 0)}
              className="px-4 py-2 bg-gray-800 rounded disabled:opacity-30 hover:bg-gray-700 text-sm"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  )
}
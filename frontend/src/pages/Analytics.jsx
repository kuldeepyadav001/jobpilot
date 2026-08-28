import { useQuery } from '@tanstack/react-query'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { fetchDashboard, fetchSnapshots } from '../api/client'

const PIE_COLORS = ['#3b82f6', '#10b981']

export default function Analytics() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
  })

  const { data: snapshots = [], isLoading: snapshotsLoading } = useQuery({
    queryKey: ['snapshots'],
    queryFn: fetchSnapshots,
  })

  if (statsLoading || snapshotsLoading) {
    return <p className="text-gray-500 text-sm">Generating analytics dashboard...</p>
  }

  // Calculate Success Rate
  const appliedCount = stats?.total_applied || 0
  const interviewCount = stats?.total_interviews || 0
  const successRate = appliedCount > 0 ? ((interviewCount / appliedCount) * 100).toFixed(1) : '0.0'

  // Prepare Portal Pie Chart Data
  const portalData = Object.entries(stats?.portal_breakdown || {}).map(([key, val]) => ({
    name: key.toUpperCase(),
    value: val,
  }))

  // Format historical snapshots for chronological timeline display
  const timelineData = [...snapshots].reverse().map(s => ({
    date: new Date(s.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    Applied: s.total_applied,
    Interviews: s.total_interviews,
  }))

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Analytics & Metrics</h2>

      {/* Grid KPI Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Jobs Discovered</p>
          <p className="text-2xl font-bold text-gray-100 mt-1">{stats?.total_jobs}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Total Applied</p>
          <p className="text-2xl font-bold text-blue-500 mt-1">{stats?.total_applied}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Interviews</p>
          <p className="text-2xl font-bold text-green-500 mt-1">{stats?.total_interviews}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Interview Rate</p>
          <p className="text-2xl font-bold text-purple-500 mt-1">{successRate}%</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 col-span-2 md:col-span-1">
          <p className="text-xs text-gray-500 uppercase font-semibold">Avg Match Score</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{stats?.avg_match_score}%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Line Chart Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase">Application Activity Timeline</h3>
          <div className="h-64">
            {timelineData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-600 text-xs">
                Not enough pipeline history. Daily snapshots will accumulate over time.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData}>
                  <XAxis dataKey="date" stroke="#6b7280" fontSize={10} />
                  <YAxis stroke="#6b7280" fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line type="monotone" dataKey="Applied" stroke="#3b82f6" strokeWidth={2} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Interviews" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Portal Pie Chart Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase">Portal Breakdown</h3>
            <div className="h-48 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={portalData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {portalData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="flex justify-around text-xs mt-4">
            {portalData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[index] }} />
                <span className="text-gray-400 font-medium">
                  {entry.name}: <strong className="text-gray-100">{entry.value}</strong>
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
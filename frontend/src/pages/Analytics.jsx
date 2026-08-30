import { useQuery } from '@tanstack/react-query'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, PieChart, Pie, Cell,
} from 'recharts'
import { fetchDashboard, fetchSnapshots } from '../api/client'

const PIE_COLORS = ['#6e5bf1', '#12b886', '#3b82f6', '#ef476f', '#f59e0b']

export default function Analytics() {
  const { data: stats, isLoading: statsLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })
  const { data: snapshots = [], isLoading: snapshotsLoading } = useQuery({ queryKey: ['snapshots'], queryFn: fetchSnapshots })

  if (statsLoading || snapshotsLoading) return <p className="text-ink-soft text-sm">Generating analytics dashboard...</p>

  const appliedCount = stats?.total_applied || 0
  const interviewCount = stats?.total_interviews || 0
  const successRate = appliedCount > 0 ? ((interviewCount / appliedCount) * 100).toFixed(1) : '0.0'

  const portalData = Object.entries(stats?.portal_breakdown || {}).map(([key, val]) => ({ name: key.toUpperCase(), value: val }))

  const timelineData = [...snapshots].reverse().map(s => ({
    date: new Date(s.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    Applied: s.total_applied,
    Interviews: s.total_interviews,
  }))

  const statsGrid = [
    { label: 'Jobs Discovered', value: stats?.total_jobs, color: 'text-ink' },
    { label: 'Total Applied', value: stats?.total_applied, color: 'text-violet-500' },
    { label: 'Interviews', value: stats?.total_interviews, color: 'text-success' },
    { label: 'Interview Rate', value: `${successRate}%`, color: 'text-purple-500' },
    { label: 'Avg Match Score', value: `${stats?.avg_match_score}%`, color: 'text-emerald-500' },
  ]

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <h2 className="text-2xl font-bold text-ink">Analytics &amp; Metrics</h2>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statsGrid.map((s, i) => (
          <div key={i} className="card p-4">
            <p className="label uppercase">{s.label}</p>
            <p className={`text-2xl font-black text-ink mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-ink-soft mb-4 uppercase">Application Activity Timeline</h3>
          <div className="h-64">
            {timelineData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-ink-faint text-xs">
                Not enough pipeline history. Daily snapshots will accumulate over time.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData}>
                  <XAxis dataKey="date" stroke="var(--ink-faint)" fontSize={10} />
                  <YAxis stroke="var(--ink-faint)" fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--line)', color: 'var(--ink)' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: 'var(--ink-soft)' }} />
                  <Line type="monotone" dataKey="Applied" stroke="#6e5bf1" strokeWidth={2.5} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Interviews" stroke="#12b886" strokeWidth={2.5} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="card p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-ink-soft mb-4 uppercase">Portal Breakdown</h3>
            <div className="h-48 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={portalData} cx="50%" cy="50%" innerRadius={48} outerRadius={72} paddingAngle={3} dataKey="value">
                    {portalData.map((entry, index) => <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--line)', color: 'var(--ink)' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="flex flex-wrap justify-center gap-4 text-xs mt-4">
            {portalData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                <span className="text-ink-soft font-medium">{entry.name}: <strong className="text-ink">{entry.value}</strong></span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

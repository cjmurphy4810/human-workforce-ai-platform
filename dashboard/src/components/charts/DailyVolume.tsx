import { useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useArticles } from '../../hooks/useArticles'
import { PageSpinner } from '../ui/Spinner'
import ErrorState from '../ui/ErrorState'

interface TooltipPayload {
  name: string
  value: number
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs">
      <div className="text-slate-300 font-medium mb-1">{label}</div>
      <div className="text-blue-400">{payload[0].value} articles</div>
    </div>
  )
}

export default function DailyVolume() {
  const { data, isLoading, isError } = useArticles({ limit: 200 })

  const chartData = useMemo(() => {
    if (!data) return []
    const byDate: Record<string, number> = {}
    for (const article of data.items) {
      const date = article.published_at.slice(0, 10)
      byDate[date] = (byDate[date] ?? 0) + 1
    }
    return Object.entries(byDate)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-21)
      .map(([date, count]) => ({
        date: date.slice(5).replace('-', '/'),
        count,
      }))
  }, [data])

  if (isLoading) return <PageSpinner />
  if (isError || !data) return <ErrorState compact />

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#64748b', fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: '#1e293b' }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#334155' }} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#volumeGradient)"
          dot={false}
          activeDot={{ r: 4, fill: '#3b82f6', stroke: '#1e3a8a', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

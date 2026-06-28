import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
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
      <div className="text-slate-300 font-medium mb-1">Score {label}</div>
      <div className="text-blue-400">{payload[0].value} articles</div>
    </div>
  )
}

const BUCKET_COLORS = [
  '#334155', '#334155', '#475569',
  '#3b82f6', '#2563eb',
  '#22c55e', '#16a34a',
  '#22c55e', '#16a34a', '#15803d',
]

export default function ScoreDistribution() {
  const { data, isLoading, isError } = useArticles({ limit: 200 })

  const chartData = useMemo(() => {
    if (!data) return []
    const buckets = Array.from({ length: 10 }, (_, i) => ({
      range: `${(i * 0.1).toFixed(1)}–${((i + 1) * 0.1).toFixed(1)}`,
      count: 0,
    }))
    for (const article of data.items) {
      const idx = Math.min(9, Math.floor(article.score.overall * 10))
      buckets[idx].count++
    }
    return buckets
  }, [data])

  if (isLoading) return <PageSpinner />
  if (isError || !data) return <ErrorState compact />

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="range"
          tick={{ fill: '#64748b', fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: '#1e293b' }}
          interval={0}
        />
        <YAxis
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b' }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={BUCKET_COLORS[i]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

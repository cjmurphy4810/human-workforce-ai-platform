import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useSources } from '../../hooks/useSources'
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

export default function ArticlesBySource() {
  const { data, isLoading, isError } = useSources()

  if (isLoading) return <PageSpinner />
  if (isError || !data) return <ErrorState compact />

  const chartData = [...data.items]
    .sort((a, b) => b.article_count - a.article_count)
    .slice(0, 10)
    .map((s) => ({
      name: s.name.split(' ').slice(0, 2).join(' '),
      fullName: s.name,
      count: s.article_count,
    }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 8, left: 60, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: '#1e293b' }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={60}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b' }} />
        <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

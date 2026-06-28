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
import { useTopics } from '../../hooks/useTopics'
import { PageSpinner } from '../ui/Spinner'
import ErrorState from '../ui/ErrorState'

const COLORS = ['#3b82f6', '#60a5fa', '#93c5fd', '#1d4ed8', '#2563eb']

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

export default function ArticlesByTopic() {
  const { data, isLoading, isError } = useTopics(30)

  if (isLoading) return <PageSpinner />
  if (isError || !data) return <ErrorState compact />

  const chartData = data.items.map((t) => ({
    label: t.label.replace(' ', '\n'),
    count: t.article_count,
    name: t.label,
  }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="name"
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: '#1e293b' }}
          interval={0}
          tickFormatter={(v: string) => v.split(' ')[0]}
        />
        <YAxis
          tick={{ fill: '#64748b', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b' }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

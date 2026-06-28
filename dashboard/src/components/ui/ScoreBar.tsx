interface ScoreBarProps {
  value: number
  label?: string
  showValue?: boolean
  height?: 'sm' | 'md'
}

function scoreColor(v: number) {
  if (v >= 0.65) return 'bg-green-500'
  if (v >= 0.40) return 'bg-blue-500'
  return 'bg-slate-600'
}

export default function ScoreBar({ value, label, showValue = true, height = 'sm' }: ScoreBarProps) {
  const pct = Math.min(100, Math.max(0, value * 100))
  const h = height === 'sm' ? 'h-1.5' : 'h-2'

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-xs text-slate-500">{label}</span>}
          {showValue && (
            <span className="text-xs font-mono text-slate-400 ml-auto">{value.toFixed(2)}</span>
          )}
        </div>
      )}
      <div className={`w-full bg-slate-800 rounded-full ${h}`}>
        <div
          className={`${h} rounded-full transition-all duration-300 ${scoreColor(value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

interface DimensionScoresProps {
  score: {
    business_impact: number
    executive_interest: number
    consulting_opportunity: number
    podcast_potential: number
    urgency: number
    overall: number
  }
}

const DIMENSION_LABELS: Record<string, string> = {
  business_impact: 'Business Impact',
  executive_interest: 'Executive Interest',
  consulting_opportunity: 'Consulting',
  podcast_potential: 'Podcast Potential',
  urgency: 'Urgency',
}

export function DimensionScores({ score }: DimensionScoresProps) {
  const dims = Object.entries(DIMENSION_LABELS) as [keyof typeof DIMENSION_LABELS, string][]
  return (
    <div className="space-y-2.5">
      {dims.map(([key, label]) => (
        <ScoreBar key={key} value={score[key as keyof typeof score] as number} label={label} />
      ))}
    </div>
  )
}

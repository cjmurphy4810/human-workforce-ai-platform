interface BadgeProps {
  children: React.ReactNode
  variant?: 'blue' | 'green' | 'amber' | 'red' | 'slate'
  size?: 'sm' | 'md'
}

const variants = {
  blue:  'bg-blue-500/15 text-blue-400 border-blue-500/25',
  green: 'bg-green-500/15 text-green-400 border-green-500/25',
  amber: 'bg-amber-500/15 text-amber-400 border-amber-500/25',
  red:   'bg-red-500/15 text-red-400 border-red-500/25',
  slate: 'bg-slate-700/50 text-slate-400 border-slate-700',
}

const sizes = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
}

export default function Badge({ children, variant = 'slate', size = 'sm' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-md border font-medium ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  )
}

export function ScoreBadge({ score }: { score: number }) {
  const variant =
    score >= 0.65 ? 'green' :
    score >= 0.40 ? 'amber' :
    'slate'

  return (
    <Badge variant={variant} size="md">
      {score.toFixed(2)}
    </Badge>
  )
}

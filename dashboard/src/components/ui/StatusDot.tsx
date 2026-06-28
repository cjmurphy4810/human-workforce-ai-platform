type Status = 'ok' | 'warn' | 'error' | 'unknown'

interface StatusDotProps {
  status: Status
  label?: string
  size?: 'sm' | 'md'
}

const colors: Record<Status, string> = {
  ok:      'bg-green-500',
  warn:    'bg-amber-500',
  error:   'bg-red-500',
  unknown: 'bg-slate-600',
}

const glows: Record<Status, string> = {
  ok:      'shadow-green-500/50',
  warn:    'shadow-amber-500/50',
  error:   'shadow-red-500/50',
  unknown: '',
}

export default function StatusDot({ status, label, size = 'sm' }: StatusDotProps) {
  const dotSize = size === 'sm' ? 'w-2 h-2' : 'w-2.5 h-2.5'
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`${dotSize} rounded-full shadow-sm ${colors[status]} ${glows[status]}`}
      />
      {label && <span className="text-sm text-slate-300">{label}</span>}
    </span>
  )
}

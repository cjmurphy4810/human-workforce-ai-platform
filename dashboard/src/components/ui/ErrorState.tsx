import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  message?: string
  compact?: boolean
}

export default function ErrorState({
  message = 'Unable to load data. Ensure the API is running.',
  compact = false,
}: ErrorStateProps) {
  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-400">
        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
        <span>{message}</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center h-48 gap-3 text-center">
      <AlertTriangle className="w-8 h-8 text-red-500/60" />
      <p className="text-sm text-slate-500 max-w-xs">{message}</p>
    </div>
  )
}

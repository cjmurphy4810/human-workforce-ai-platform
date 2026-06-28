import { useState } from 'react'
import { PlayCircle, RefreshCw, ExternalLink } from 'lucide-react'
import { useHealth } from '../hooks/useHealth'
import { useStats } from '../hooks/useStats'
import { useSources } from '../hooks/useSources'
import { usePipeline } from '../hooks/usePipeline'
import Card, { CardHeader } from '../components/ui/Card'
import StatusDot from '../components/ui/StatusDot'
import ScoreBar from '../components/ui/ScoreBar'
import { PageSpinner } from '../components/ui/Spinner'
import ErrorState from '../components/ui/ErrorState'
import type { RunResponse } from '../types/api'

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function formatDuration(sec: number) {
  return sec < 60 ? `${sec.toFixed(1)}s` : `${(sec / 60).toFixed(1)}m`
}

export default function System() {
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useHealth()
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: sources, isLoading: sourcesLoading } = useSources()
  const { mutate: runPipeline, isPending: isRunning, data: lastRun } = usePipeline()
  const [showRunResult, setShowRunResult] = useState(false)

  function handleRun() {
    setShowRunResult(true)
    runPipeline()
  }

  const healthStatus =
    health?.status === 'healthy'  ? 'ok'   :
    health?.status === 'degraded' ? 'warn' :
    health                        ? 'error': 'unknown'

  const dbStatus =
    health?.database === 'connected' ? 'ok' :
    health                           ? 'error' : 'unknown'

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">System</h1>
          <p className="text-sm text-slate-500 mt-0.5">API, database, and pipeline status</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => void refetchHealth()}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
          >
            <PlayCircle className="w-4 h-4" />
            {isRunning ? 'Running…' : 'Run Pipeline'}
          </button>
        </div>
      </div>

      {/* Health + Database */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="API Health" />
          {healthLoading && <PageSpinner />}
          {!healthLoading && !health && <ErrorState compact />}
          {health && (
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Status</span>
                <StatusDot status={healthStatus} label={health.status} />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Version</span>
                <span className="text-sm font-mono text-slate-300">v{health.version}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Sources Configured</span>
                <span className="text-sm font-semibold text-slate-200">{health.sources_configured}</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-xs text-slate-500">Last Checked</span>
                <span className="text-xs text-slate-400">{formatDateTime(health.timestamp)}</span>
              </div>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Database" />
          {statsLoading && <PageSpinner />}
          {!statsLoading && !stats && <ErrorState compact />}
          {health && stats && (
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Connection</span>
                <StatusDot status={dbStatus} label={health.database} />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Total Articles</span>
                <span className="text-sm font-semibold text-slate-200">{stats.total_articles.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Last 7 Days</span>
                <span className="text-sm font-semibold text-slate-200">{stats.articles_last_7_days.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-xs text-slate-500">Last 30 Days</span>
                <span className="text-sm font-semibold text-slate-200">{stats.articles_last_30_days.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-xs text-slate-500">Last Fetch</span>
                <span className="text-xs text-slate-400">
                  {stats.last_fetch ? formatDateTime(stats.last_fetch) : '—'}
                </span>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Last Pipeline Run result */}
      {showRunResult && (
        <Card>
          <CardHeader title="Last Execution" />
          {isRunning && (
            <div className="flex items-center gap-3 py-4">
              <PageSpinner />
              <span className="text-sm text-slate-400">Pipeline is running… this may take 10–30 seconds</span>
            </div>
          )}
          {!isRunning && lastRun && <RunResultDetail run={lastRun} />}
        </Card>
      )}

      {/* Sources (Configuration Status) */}
      <Card padding={false}>
        <div className="px-5 pt-5 pb-3 border-b border-slate-800">
          <CardHeader
            title="Configured Sources"
            subtitle={`${sources?.total ?? '—'} RSS feeds`}
          />
        </div>
        {sourcesLoading && <div className="p-5"><PageSpinner /></div>}
        {!sourcesLoading && !sources && <div className="p-5"><ErrorState compact /></div>}
        {sources && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-5 py-3 text-left text-slate-500 font-semibold uppercase tracking-wider">Source</th>
                  <th className="px-5 py-3 text-right text-slate-500 font-semibold uppercase tracking-wider">Weight</th>
                  <th className="px-5 py-3 text-right text-slate-500 font-semibold uppercase tracking-wider">Articles</th>
                  <th className="px-5 py-3 text-left text-slate-500 font-semibold uppercase tracking-wider w-40">Avg Score</th>
                  <th className="px-5 py-3 text-left text-slate-500 font-semibold uppercase tracking-wider">Link</th>
                </tr>
              </thead>
              <tbody>
                {sources.items.map((src, i) => (
                  <tr key={src.name} className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-900/30'}`}>
                    <td className="px-5 py-3 font-medium text-slate-200">{src.name}</td>
                    <td className="px-5 py-3 text-right font-mono text-slate-400">{src.weight.toFixed(1)}</td>
                    <td className="px-5 py-3 text-right text-slate-300">{src.article_count.toLocaleString()}</td>
                    <td className="px-5 py-3 w-40">
                      {src.article_count > 0 ? (
                        <ScoreBar value={src.avg_score} />
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-blue-500 hover:text-blue-400 transition-colors"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Feed
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Application logs note */}
      <Card>
        <CardHeader title="Application Logs" />
        <p className="text-sm text-slate-500">
          Runtime logs are written to <code className="font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded text-xs">logs/</code> at the project root.
          They are not exposed via the REST API. To stream live output, run:{' '}
          <code className="font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded text-xs">make dev</code> in one terminal and
          {' '}<code className="font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded text-xs">tail -f logs/*.log</code> in another.
        </p>
      </Card>
    </div>
  )
}

function RunResultDetail({ run }: { run: RunResponse }) {
  const statusColor = run.status === 'completed' ? 'text-green-400' : 'text-red-400'
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className={`text-sm font-semibold capitalize ${statusColor}`}>{run.status}</span>
        <span className="text-xs text-slate-500">{formatDateTime(run.timestamp)}</span>
        <span className="text-xs text-slate-500">·</span>
        <span className="text-xs text-slate-500">{formatDuration(run.duration_seconds)}</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Fetched', value: run.articles_fetched },
          { label: 'New', value: run.articles_new },
          { label: 'Saved', value: run.articles_saved },
          { label: `Sources (${run.sources_succeeded}/${run.sources_attempted})`, value: run.sources_succeeded },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 rounded-lg p-3">
            <div className="text-xs text-slate-500 mb-1">{label}</div>
            <div className="text-lg font-bold text-slate-100">{value}</div>
          </div>
        ))}
      </div>
      {run.source_errors.length > 0 && (
        <div className="mt-2">
          <div className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Source Errors</div>
          <div className="space-y-1">
            {run.source_errors.map((e, i) => (
              <div key={i} className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
                <span className="font-medium">{e.source}:</span> {e.error}
              </div>
            ))}
          </div>
        </div>
      )}
      {run.brief_path && (
        <div className="text-xs text-slate-500">
          Brief saved to: <code className="font-mono text-slate-400 bg-slate-800 px-1 py-0.5 rounded">{run.brief_path}</code>
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { ExternalLink, PlayCircle, FileText, X, ChevronRight } from 'lucide-react'
import { useHealth } from '../hooks/useHealth'
import { useStats } from '../hooks/useStats'
import { useBrief } from '../hooks/useBrief'
import { useArticles } from '../hooks/useArticles'
import { usePipeline } from '../hooks/usePipeline'
import Card, { CardHeader } from '../components/ui/Card'
import StatusDot from '../components/ui/StatusDot'
import ScoreBar, { DimensionScores } from '../components/ui/ScoreBar'
import { ScoreBadge } from '../components/ui/Badge'
import { PageSpinner } from '../components/ui/Spinner'
import ErrorState from '../components/ui/ErrorState'
import type { Article } from '../types/api'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function renderBriefMarkdown(content: string) {
  const lines = content.split('\n')
  return lines.map((line, i) => {
    if (line.startsWith('## '))
      return <h2 key={i} className="text-base font-semibold text-slate-100 mt-5 mb-2 pb-1.5 border-b border-slate-800">{line.slice(3)}</h2>
    if (line.startsWith('### '))
      return <h3 key={i} className="text-sm font-semibold text-slate-200 mt-3 mb-1">{line.slice(4)}</h3>
    if (line.startsWith('# '))
      return <h1 key={i} className="text-lg font-bold text-slate-100 mb-3">{line.slice(2)}</h1>
    if (line.startsWith('| ') && line.includes('|')) {
      const cols = line.split('|').filter(c => c.trim())
      const isSep = cols.every(c => /^[-:\s]+$/.test(c))
      if (isSep) return null
      return (
        <div key={i} className="grid gap-2 text-xs text-slate-400 py-1 border-b border-slate-800/50" style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))` }}>
          {cols.map((c, j) => <span key={j}>{c.trim()}</span>)}
        </div>
      )
    }
    if (line.startsWith('- ') || line.startsWith('* '))
      return <li key={i} className="text-sm text-slate-400 ml-4 mb-0.5 list-disc">{line.slice(2)}</li>
    if (line.startsWith('---') || line.startsWith('___'))
      return <hr key={i} className="border-slate-800 my-3" />
    if (line.trim() === '')
      return <div key={i} className="h-1" />
    const bold = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-slate-200">$1</strong>')
    return (
      <p key={i} className="text-sm text-slate-400 mb-1" dangerouslySetInnerHTML={{ __html: bold }} />
    )
  })
}

function ArticleCard({ article, onClick }: { article: Article; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg transition-all group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200 group-hover:text-white line-clamp-2 leading-snug">
            {article.title}
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-xs text-slate-500">{article.source_name}</span>
            <span className="text-slate-700">·</span>
            <span className="text-xs text-slate-500">{formatDate(article.published_at)}</span>
          </div>
        </div>
        <div className="flex-shrink-0 flex items-center gap-2">
          <ScoreBadge score={article.score.overall} />
          <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 transition-colors" />
        </div>
      </div>
      <div className="mt-2.5">
        <ScoreBar value={article.score.overall} showValue={false} />
      </div>
    </button>
  )
}

function ArticleDetailModal({ article, onClose }: { article: Article; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg h-full bg-slate-900 border-l border-slate-800 overflow-y-auto shadow-2xl">
        <div className="sticky top-0 bg-slate-900 border-b border-slate-800 px-5 py-4 flex items-center justify-between z-10">
          <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Article Detail</span>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-5">
          <div>
            <h2 className="text-base font-semibold text-slate-100 leading-snug mb-3">{article.title}</h2>
            <div className="flex flex-wrap gap-2 text-xs text-slate-500">
              <span className="bg-slate-800 px-2 py-1 rounded">{article.source_name}</span>
              <span className="bg-slate-800 px-2 py-1 rounded">{formatDate(article.published_at)}</span>
            </div>
          </div>

          {article.summary && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Summary</div>
              <p className="text-sm text-slate-400 leading-relaxed">{article.summary}</p>
            </div>
          )}

          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Overall Score
            </div>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl font-bold text-slate-100">{article.score.overall.toFixed(2)}</span>
              <ScoreBadge score={article.score.overall} />
            </div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Dimension Scores
            </div>
            <DimensionScores score={article.score} />
          </div>

          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 w-full justify-center px-4 py-2.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/30 text-blue-400 hover:text-blue-300 text-sm font-medium rounded-lg transition-all"
          >
            <ExternalLink className="w-4 h-4" />
            Read Full Article
          </a>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const { data: health } = useHealth()
  const { data: stats } = useStats()
  const { data: brief, isLoading: briefLoading } = useBrief()
  const { data: topStories, isLoading: storiesLoading } = useArticles({ limit: 10 })
  const { data: topConsulting } = useArticles({ topic: 'consulting_opportunity', limit: 5 })
  const { data: topPodcast } = useArticles({ topic: 'podcast_potential', limit: 5 })
  const [briefOpen, setBriefOpen] = useState(false)
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const { mutate: runPipeline, isPending: isRunning } = usePipeline()

  const healthStatus =
    health?.status === 'healthy' ? 'ok' :
    health?.status === 'degraded' ? 'warn' :
    health ? 'error' : 'unknown'

  const dbStatus =
    health?.database === 'connected' ? 'ok' :
    health ? 'error' : 'unknown'

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Human Workforce Intelligence</h1>
          <p className="text-sm text-slate-500 mt-0.5">Executive Research Dashboard</p>
        </div>
        <button
          onClick={() => runPipeline()}
          disabled={isRunning}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
        >
          <PlayCircle className="w-4 h-4" />
          {isRunning ? 'Running…' : 'Run Pipeline'}
        </button>
      </div>

      {/* Status row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">API Health</div>
          <StatusDot status={healthStatus} label={health?.status ?? 'Unknown'} size="md" />
        </Card>
        <Card>
          <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Database</div>
          <StatusDot status={dbStatus} label={health?.database ?? 'Unknown'} size="md" />
        </Card>
        <Card>
          <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Total Articles</div>
          <div className="text-2xl font-bold text-slate-100">
            {stats?.total_articles?.toLocaleString() ?? '—'}
          </div>
        </Card>
        <Card>
          <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Last Fetch</div>
          <div className="text-sm font-medium text-slate-200">
            {stats?.last_fetch ? formatDateTime(stats.last_fetch) : '—'}
          </div>
        </Card>
      </div>

      {/* Executive Brief */}
      <Card padding={false}>
        <div className="px-5 pt-5 pb-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600/15 border border-blue-600/25 rounded-lg flex items-center justify-center">
              <FileText className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-100">Executive Brief</div>
              {brief && (
                <div className="text-xs text-slate-500 mt-0.5">
                  {brief.date} · {brief.word_count.toLocaleString()} words
                </div>
              )}
            </div>
          </div>
          {brief && (
            <button
              onClick={() => setBriefOpen(true)}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors"
            >
              View Full Brief →
            </button>
          )}
        </div>
        <div className="p-5">
          {briefLoading && <PageSpinner />}
          {!briefLoading && !brief && (
            <ErrorState message="No executive brief available. Run the pipeline to generate one." />
          )}
          {brief && (
            <div className="max-h-72 overflow-y-auto pr-1 space-y-0.5">
              {renderBriefMarkdown(brief.content.slice(0, 2000))}
              {brief.content.length > 2000 && (
                <button
                  onClick={() => setBriefOpen(true)}
                  className="text-xs text-blue-400 hover:text-blue-300 mt-3 block transition-colors"
                >
                  + {Math.round((brief.content.length - 2000) / 5)} more lines — click to expand
                </button>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Top Stories */}
      <Card padding={false}>
        <div className="px-5 pt-5 pb-3 border-b border-slate-800">
          <CardHeader title="Top Stories" subtitle="Highest overall scores from this cycle" />
        </div>
        <div className="p-3 space-y-2">
          {storiesLoading && <PageSpinner />}
          {!storiesLoading && !topStories && <ErrorState compact />}
          {topStories?.items.map((article, i) => (
            <ArticleCard
              key={`${article.url}-${i}`}
              article={article}
              onClick={() => setSelectedArticle(article)}
            />
          ))}
        </div>
      </Card>

      {/* Consulting + Podcast */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card padding={false}>
          <div className="px-5 pt-5 pb-3 border-b border-slate-800">
            <CardHeader
              title="Top Consulting Opportunities"
              subtitle="Highest consulting opportunity scores"
            />
          </div>
          <div className="p-3 space-y-2">
            {!topConsulting && <PageSpinner />}
            {topConsulting?.items.map((article, i) => (
              <ArticleCard
                key={`consulting-${article.url}-${i}`}
                article={article}
                onClick={() => setSelectedArticle(article)}
              />
            ))}
          </div>
        </Card>

        <Card padding={false}>
          <div className="px-5 pt-5 pb-3 border-b border-slate-800">
            <CardHeader
              title="Top Podcast Ideas"
              subtitle="Highest podcast potential scores"
            />
          </div>
          <div className="p-3 space-y-2">
            {!topPodcast && <PageSpinner />}
            {topPodcast?.items.map((article, i) => (
              <ArticleCard
                key={`podcast-${article.url}-${i}`}
                article={article}
                onClick={() => setSelectedArticle(article)}
              />
            ))}
          </div>
        </Card>
      </div>

      {/* Full Brief Modal */}
      {briefOpen && brief && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setBriefOpen(false)} />
          <div className="relative w-full max-w-3xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
              <div>
                <h2 className="text-sm font-semibold text-slate-100">Executive Brief</h2>
                <p className="text-xs text-slate-500 mt-0.5">{brief.date} · {brief.word_count.toLocaleString()} words</p>
              </div>
              <button onClick={() => setBriefOpen(false)} className="text-slate-500 hover:text-slate-300 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="overflow-y-auto p-6 space-y-0.5 flex-1">
              {renderBriefMarkdown(brief.content)}
            </div>
          </div>
        </div>
      )}

      {/* Article Detail */}
      {selectedArticle && (
        <ArticleDetailModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      )}
    </div>
  )
}

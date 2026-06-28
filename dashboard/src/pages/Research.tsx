import { useState, useMemo } from 'react'
import { Search, X, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react'
import { useArticles } from '../hooks/useArticles'
import { useSources } from '../hooks/useSources'
import Card from '../components/ui/Card'
import { ScoreBadge } from '../components/ui/Badge'
import { DimensionScores } from '../components/ui/ScoreBar'
import { PageSpinner } from '../components/ui/Spinner'
import ErrorState from '../components/ui/ErrorState'
import type { Article, ArticleFilters } from '../types/api'

const TOPICS = [
  { value: '', label: 'All Topics' },
  { value: 'business_impact',       label: 'Business Impact' },
  { value: 'executive_interest',    label: 'Executive Interest' },
  { value: 'consulting_opportunity',label: 'Consulting Opportunity' },
  { value: 'podcast_potential',     label: 'Podcast Potential' },
  { value: 'urgency',               label: 'Urgency' },
]

const PAGE_SIZE = 20

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function ArticleDrawer({ article, onClose }: { article: Article; onClose: () => void }) {
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
            <div className="flex items-center gap-3 mb-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Overall Score</div>
                <span className="text-3xl font-bold text-slate-100">{article.score.overall.toFixed(2)}</span>
              </div>
              <ScoreBadge score={article.score.overall} />
            </div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Dimensions</div>
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

export default function Research() {
  const [query, setQuery] = useState('')
  const [topic, setTopic] = useState('')
  const [source, setSource] = useState('')
  const [date, setDate] = useState('')
  const [minScore, setMinScore] = useState<number | ''>('')
  const [page, setPage] = useState(0)
  const [selected, setSelected] = useState<Article | null>(null)

  const { data: sourceList } = useSources()

  const apiFilters: ArticleFilters = useMemo(() => ({
    ...(topic ? { topic } : {}),
    ...(source ? { source } : {}),
    ...(date ? { date } : {}),
    ...(minScore !== '' ? { min_score: minScore } : {}),
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  }), [topic, source, date, minScore, page])

  const { data, isLoading, isError } = useArticles(apiFilters)

  const filtered = useMemo(() => {
    if (!data) return []
    if (!query.trim()) return data.items
    const q = query.toLowerCase()
    return data.items.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.summary.toLowerCase().includes(q) ||
        a.source_name.toLowerCase().includes(q)
    )
  }, [data, query])

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0

  function resetFilters() {
    setQuery('')
    setTopic('')
    setSource('')
    setDate('')
    setMinScore('')
    setPage(0)
  }

  function handleFilterChange(fn: () => void) {
    setPage(0)
    fn()
  }

  return (
    <div className="p-6 space-y-5 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-100">Research</h1>
        <p className="text-sm text-slate-500 mt-0.5">Search and filter collected articles</p>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
          {/* Text search */}
          <div className="xl:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search title, summary, source…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          {/* Topic */}
          <select
            value={topic}
            onChange={(e) => handleFilterChange(() => setTopic(e.target.value))}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
          >
            {TOPICS.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>

          {/* Source */}
          <select
            value={source}
            onChange={(e) => handleFilterChange(() => setSource(e.target.value))}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
          >
            <option value="">All Sources</option>
            {sourceList?.items.map((s) => (
              <option key={s.name} value={s.name}>{s.name}</option>
            ))}
          </select>

          {/* Date */}
          <input
            type="date"
            value={date}
            onChange={(e) => handleFilterChange(() => setDate(e.target.value))}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Score filter */}
        <div className="mt-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500 whitespace-nowrap">Min Score</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={minScore === '' ? 0 : minScore}
              onChange={(e) => handleFilterChange(() => setMinScore(parseFloat(e.target.value) || ''))}
              className="w-32 accent-blue-500"
            />
            <span className="text-xs font-mono text-slate-400 w-8">
              {minScore === '' ? '0.00' : minScore.toFixed(2)}
            </span>
          </div>
          <button
            onClick={resetFilters}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            Clear filters
          </button>
        </div>
      </Card>

      {/* Results */}
      <div>
        {data && (
          <div className="text-xs text-slate-500 mb-3">
            Showing {filtered.length} of {data.total.toLocaleString()} articles
          </div>
        )}

        {isLoading && <PageSpinner />}
        {isError && <ErrorState />}

        {!isLoading && !isError && (
          <div className="space-y-1.5">
            {filtered.length === 0 && (
              <div className="text-center text-sm text-slate-500 py-16">No articles match the current filters.</div>
            )}
            {filtered.map((article, i) => (
              <button
                key={`${article.url}-${i}`}
                onClick={() => setSelected(article)}
                className="w-full text-left px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-lg transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 group-hover:text-white truncate">
                      {article.title}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-slate-500">{article.source_name}</span>
                      <span className="text-slate-700">·</span>
                      <span className="text-xs text-slate-500">{formatDate(article.published_at)}</span>
                      {article.summary && (
                        <>
                          <span className="text-slate-700">·</span>
                          <span className="text-xs text-slate-600 truncate max-w-xs">{article.summary.slice(0, 80)}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <ScoreBadge score={article.score.overall} />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-800">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <span className="text-xs text-slate-500">
              Page {page + 1} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {selected && (
        <ArticleDrawer article={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}

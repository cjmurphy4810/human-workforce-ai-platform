import Card, { CardHeader } from '../components/ui/Card'
import ArticlesByTopic from '../components/charts/ArticlesByTopic'
import ArticlesBySource from '../components/charts/ArticlesBySource'
import ScoreDistribution from '../components/charts/ScoreDistribution'
import DailyVolume from '../components/charts/DailyVolume'

export default function Charts() {
  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-100">Analytics</h1>
        <p className="text-sm text-slate-500 mt-0.5">Article volume, sources, and scoring distribution</p>
      </div>

      {/* 2×2 chart grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <CardHeader
            title="Articles by Topic"
            subtitle="Article count per scoring dimension (last 30 days)"
          />
          <ArticlesByTopic />
        </Card>

        <Card>
          <CardHeader
            title="Articles by Source"
            subtitle="Article count per RSS source"
          />
          <ArticlesBySource />
        </Card>

        <Card>
          <CardHeader
            title="Score Distribution"
            subtitle="Overall score histogram across 200 most recent articles"
          />
          <ScoreDistribution />
        </Card>

        <Card>
          <CardHeader
            title="Daily Volume"
            subtitle="Published articles per day (last 21 days)"
          />
          <DailyVolume />
        </Card>
      </div>
    </div>
  )
}

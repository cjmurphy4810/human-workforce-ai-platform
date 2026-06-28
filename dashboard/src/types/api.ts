export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy'
export type DbStatus = 'connected' | 'disconnected'

export interface HealthResponse {
  status: HealthStatus
  version: string
  timestamp: string
  database: DbStatus
  sources_configured: number
}

export interface StatsResponse {
  total_articles: number
  articles_last_7_days: number
  articles_last_30_days: number
  sources_configured: number
  last_fetch: string | null
}

export interface BriefResponse {
  date: string
  path: string
  content: string
  word_count: number
  character_count: number
}

export interface SourceError {
  source: string
  error: string
}

export interface RunResponse {
  status: 'completed' | 'failed'
  timestamp: string
  articles_fetched: number
  articles_new: number
  articles_saved: number
  sources_attempted: number
  sources_succeeded: number
  source_errors: SourceError[]
  save_errors: string[]
  brief_path: string
  duration_seconds: number
}

export interface ArticleScore {
  business_impact: number
  executive_interest: number
  consulting_opportunity: number
  podcast_potential: number
  urgency: number
  overall: number
}

export interface Article {
  title: string
  url: string
  source_name: string
  published_at: string
  fetched_at: string
  summary: string
  score: ArticleScore
}

export interface ArticleListResponse {
  items: Article[]
  total: number
  limit: number
  offset: number
}

export interface ArticleFilters {
  date?: string
  source?: string
  min_score?: number
  topic?: string
  limit?: number
  offset?: number
}

export type TopicId =
  | 'business_impact'
  | 'executive_interest'
  | 'consulting_opportunity'
  | 'podcast_potential'
  | 'urgency'

export interface TopicItem {
  id: string
  label: string
  article_count: number
  avg_score: number
  top_article: Article | null
}

export interface TopicListResponse {
  items: TopicItem[]
  since_days: number
}

export interface SourceItem {
  name: string
  url: string
  weight: number
  article_count: number
  avg_score: number
  latest_article_date: string | null
}

export interface SourceListResponse {
  items: SourceItem[]
  total: number
}

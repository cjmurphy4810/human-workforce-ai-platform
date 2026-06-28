import apiClient from './client'
import type {
  HealthResponse,
  StatsResponse,
  BriefResponse,
  RunResponse,
  ArticleListResponse,
  ArticleFilters,
  TopicListResponse,
  SourceListResponse,
} from '../types/api'

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

export async function fetchStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get<StatsResponse>('/stats')
  return data
}

export async function fetchBrief(): Promise<BriefResponse> {
  const { data } = await apiClient.get<BriefResponse>('/brief/latest')
  return data
}

export async function fetchArticles(filters: ArticleFilters = {}): Promise<ArticleListResponse> {
  const params = new URLSearchParams()
  if (filters.date) params.set('date', filters.date)
  if (filters.source) params.set('source', filters.source)
  if (filters.min_score !== undefined) params.set('min_score', String(filters.min_score))
  if (filters.topic) params.set('topic', filters.topic)
  if (filters.limit !== undefined) params.set('limit', String(filters.limit))
  if (filters.offset !== undefined) params.set('offset', String(filters.offset))
  const { data } = await apiClient.get<ArticleListResponse>(`/articles?${params}`)
  return data
}

export async function fetchTopics(since_days = 30): Promise<TopicListResponse> {
  const { data } = await apiClient.get<TopicListResponse>(`/topics?since_days=${since_days}`)
  return data
}

export async function fetchSources(): Promise<SourceListResponse> {
  const { data } = await apiClient.get<SourceListResponse>('/sources')
  return data
}

export async function runPipeline(): Promise<RunResponse> {
  const { data } = await apiClient.post<RunResponse>('/run')
  return data
}

import { useQuery } from '@tanstack/react-query'
import { fetchArticles } from '../api'
import type { ArticleFilters } from '../types/api'

export function useArticles(filters: ArticleFilters = {}) {
  return useQuery({
    queryKey: ['articles', filters],
    queryFn: () => fetchArticles(filters),
  })
}

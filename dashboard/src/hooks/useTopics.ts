import { useQuery } from '@tanstack/react-query'
import { fetchTopics } from '../api'

export function useTopics(since_days = 30) {
  return useQuery({
    queryKey: ['topics', since_days],
    queryFn: () => fetchTopics(since_days),
  })
}

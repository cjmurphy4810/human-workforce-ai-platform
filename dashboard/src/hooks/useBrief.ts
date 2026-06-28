import { useQuery } from '@tanstack/react-query'
import { fetchBrief } from '../api'

export function useBrief() {
  return useQuery({
    queryKey: ['brief'],
    queryFn: fetchBrief,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })
}

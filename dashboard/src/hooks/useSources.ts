import { useQuery } from '@tanstack/react-query'
import { fetchSources } from '../api'

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
  })
}

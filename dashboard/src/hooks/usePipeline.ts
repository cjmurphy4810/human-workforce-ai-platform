import { useMutation, useQueryClient } from '@tanstack/react-query'
import { runPipeline } from '../api'

export function usePipeline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: runPipeline,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['articles'] })
      void queryClient.invalidateQueries({ queryKey: ['stats'] })
      void queryClient.invalidateQueries({ queryKey: ['brief'] })
      void queryClient.invalidateQueries({ queryKey: ['topics'] })
      void queryClient.invalidateQueries({ queryKey: ['sources'] })
      void queryClient.invalidateQueries({ queryKey: ['health'] })
    },
  })
}

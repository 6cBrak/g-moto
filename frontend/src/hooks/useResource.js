import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

export function useResourceList(resource, params = {}, options = {}) {
  return useQuery({
    queryKey: [resource, 'list', params],
    queryFn: async () => {
      const { data } = await apiClient.get(`/${resource}/`, { params })
      return data.results ?? data
    },
    ...options,
  })
}

export function useResourceMutations(resource) {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: [resource] })

  const create = useMutation({
    mutationFn: (payload) => apiClient.post(`/${resource}/`, payload),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, payload }) => apiClient.patch(`/${resource}/${id}/`, payload),
    onSuccess: invalidate,
  })

  const remove = useMutation({
    mutationFn: (id) => apiClient.delete(`/${resource}/${id}/`),
    onSuccess: invalidate,
  })

  return { create, update, remove }
}

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

// Comme useResourceList, mais conserve les metadonnees de pagination DRF
// (count/next/previous) pour les listes trop volumineuses pour tenir sur une page.
export function useResourceListPaged(resource, params = {}, options = {}) {
  return useQuery({
    queryKey: [resource, 'list-paged', params],
    queryFn: async () => {
      const { data } = await apiClient.get(`/${resource}/`, { params })
      if (data && Array.isArray(data.results)) {
        return { results: data.results, count: data.count ?? data.results.length }
      }
      const results = Array.isArray(data) ? data : []
      return { results, count: results.length }
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

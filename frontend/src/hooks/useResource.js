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

// Pour peupler un menu deroulant : recupere TOUTES les pages, quel que soit
// le nombre total d'elements. A utiliser a la place de useResourceList des
// qu'on a besoin de l'integralite d'une liste de reference (types de moto,
// clients, motos...), plutot qu'un page_size fixe qui finirait par etre
// depasse un jour et referait disparaitre silencieusement des options.
export function useResourceListAll(resource, params = {}, options = {}) {
  return useQuery({
    queryKey: [resource, 'list-all', params],
    queryFn: async () => {
      let resultats = []
      let page = 1
      for (;;) {
        const { data } = await apiClient.get(`/${resource}/`, { params: { ...params, page, page_size: 500 } })
        if (!data || !Array.isArray(data.results)) {
          return Array.isArray(data) ? data : []
        }
        resultats = resultats.concat(data.results)
        if (!data.next) break
        page += 1
      }
      return resultats
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

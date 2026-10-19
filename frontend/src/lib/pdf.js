import { apiClient } from '../api/client'

export async function ouvrirPdf(url, params) {
  const response = await apiClient.get(url, { responseType: 'blob', params })
  const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  window.open(blobUrl, '_blank')
}

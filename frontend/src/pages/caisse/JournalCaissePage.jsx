import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceList } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import { useUiStore } from '../../store/uiStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import { formatMontant } from '../../lib/format'

export default function JournalCaissePage() {
  const user = useAuthStore((state) => state.user)
  const agenceFiltre = useUiStore((state) => state.agenceFiltre)
  const { data: agences } = useResourceList('agences', { page_size: 1000 }, { enabled: user?.role === 'admin' && !agenceFiltre })
  const [filtres, setFiltres] = useState({})

  const { data, isLoading } = useQuery({
    queryKey: ['caisse', 'journal', agenceFiltre, filtres],
    queryFn: async () => (await apiClient.get('/caisse/journal/', {
      params: { agence: agenceFiltre || undefined, ...filtres },
    })).data,
  })

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'Description' },
    { name: 'date_debut', label: 'Du', type: 'date' },
    { name: 'date_fin', label: 'Au', type: 'date' },
    ...(user?.role === 'admin' && !agenceFiltre ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Journal de caisse</h1>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value || undefined }))}
      />

      <DataTable
        isLoading={isLoading}
        rows={data}
        columns={[
          { key: 'date', label: 'Date' },
          { key: 'type', label: 'Type' },
          { key: 'agence', label: 'Agence' },
          { key: 'description', label: 'Description' },
          { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
        ]}
      />
    </div>
  )
}

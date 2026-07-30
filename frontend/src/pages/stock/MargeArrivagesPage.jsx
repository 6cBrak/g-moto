import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useUiStore } from '../../store/uiStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import { formatDate, formatMontant } from '../../lib/format'

export default function MargeArrivagesPage() {
  const agenceFiltre = useUiStore((state) => state.agenceFiltre)
  const [filtres, setFiltres] = useState({})

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'marge-arrivages', agenceFiltre, filtres],
    queryFn: async () => (await apiClient.get('/dashboard/marge-arrivages/', {
      params: { agence: agenceFiltre || undefined, ...filtres },
    })).data,
  })

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'N° bon ou fournisseur' },
    { name: 'date_debut', label: 'Du', type: 'date' },
    { name: 'date_fin', label: 'Au', type: 'date' },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Marge par arrivage</h1>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value || undefined }))}
      />

      <DataTable
        isLoading={isLoading}
        rows={data}
        columns={[
          { key: 'numero_bon', label: 'N° bon' },
          { key: 'date_arrivage', label: 'Date', render: (r) => formatDate(r.date_arrivage) },
          { key: 'agence', label: 'Agence' },
          { key: 'fournisseur', label: 'Fournisseur' },
          { key: 'nb_motos', label: 'Nb motos' },
          { key: 'total_revient', label: 'Total revient', render: (r) => `${formatMontant(r.total_revient)} F` },
          { key: 'total_vente', label: 'Total vente', render: (r) => `${formatMontant(r.total_vente)} F` },
          { key: 'total_marge', label: 'Marge', render: (r) => `${formatMontant(r.total_marge)} F` },
        ]}
      />
    </div>
  )
}

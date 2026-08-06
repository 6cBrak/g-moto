import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useResourceList } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import { formatDateTime, formatMontant } from '../../lib/format'

const STATUTS = [
  { value: 'validee', label: 'Validee' },
  { value: 'annulee', label: 'Annulee' },
]

export default function FacturesListPage() {
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceList('agences', { page_size: 1000 }, { enabled: user?.role === 'admin' })
  const [filtres, setFiltres] = useState({})

  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))
  const { data: factures, isLoading } = useResourceList('factures', params)

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'N° facture ou client' },
    { name: 'date_debut', label: 'Du', type: 'date' },
    { name: 'date_fin', label: 'Au', type: 'date' },
    { name: 'statut', label: 'Statut', type: 'select', options: STATUTS },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Factures</h1>
        <Link to="/factures/nouvelle" className="px-4 py-2 text-sm bg-slate-800 text-white rounded">
          + Nouvelle facture
        </Link>
      </div>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value }))}
      />

      <DataTable
        isLoading={isLoading}
        rows={factures}
        columns={[
          { key: 'numero_facture', label: 'N° facture' },
          { key: 'client_nom', label: 'Client' },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'date_facture', label: 'Date', render: (r) => formatDateTime(r.date_facture) },
          { key: 'total', label: 'Total', render: (r) => `${formatMontant(r.total)} F` },
          { key: 'statut', label: 'Statut' },
        ]}
        actions={(row) => (
          <Link to={`/factures/${row.id}`} className="text-slate-600 hover:text-slate-900 text-sm">
            Voir
          </Link>
        )}
      />
    </div>
  )
}

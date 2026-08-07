import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceListAll, useResourceListPaged, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import FormModal from '../../components/FormModal'
import Pagination from '../../components/Pagination'
import { formatDate } from '../../lib/format'

const TYPES = [
  { value: 'vidange', label: 'Vidange' },
  { value: 'revision_generale', label: 'Revision generale' },
  { value: 'controle', label: 'Controle' },
  { value: 'autre', label: 'Autre' },
]

const STATUT_OPTIONS = [
  { value: 'a_faire', label: 'A faire' },
  { value: 'realise', label: 'Realise' },
]

export default function EntretiensPage() {
  const user = useAuthStore((state) => state.user)
  const [filtres, setFiltres] = useState({})
  const [page, setPage] = useState(1)
  const params = { ...Object.fromEntries(Object.entries(filtres).filter(([, v]) => v)), page, page_size: 10 }
  const { data: entretiensPage, isLoading } = useResourceListPaged('entretiens', params)
  const entretiens = entretiensPage?.results
  const { data: motos } = useResourceListAll('motos')
  const { data: agences } = useResourceListAll('agences', {}, { enabled: user?.role === 'admin' })
  const { create } = useResourceMutations('entretiens')
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)

  const marquerRealise = async (id) => {
    await apiClient.post(`/entretiens/${id}/realiser/`)
    queryClient.invalidateQueries({ queryKey: ['entretiens'] })
  }

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'N° serie moto' },
    { name: 'date_debut', label: 'Prevu du', type: 'date' },
    { name: 'date_fin', label: 'Prevu au', type: 'date' },
    { name: 'statut', label: 'Statut', type: 'select', options: STATUT_OPTIONS },
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
        <h1 className="text-xl font-semibold text-slate-800">Entretiens / Revisions</h1>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 text-sm bg-slate-800 text-white rounded">
          + Planifier un entretien
        </button>
      </div>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => { setFiltres((prev) => ({ ...prev, [name]: value })); setPage(1) }}
      />

      <DataTable
        isLoading={isLoading}
        rows={entretiens}
        columns={[
          { key: 'moto_numero_serie', label: 'Moto' },
          { key: 'type_entretien', label: 'Type' },
          { key: 'date_prevue', label: 'Date prevue', render: (r) => formatDate(r.date_prevue) },
          { key: 'date_realisee', label: 'Date realisee', render: (r) => formatDate(r.date_realisee) },
          { key: 'realise', label: 'Statut', render: (r) => (r.realise ? 'Realise' : 'A faire') },
        ]}
        actions={(row) => !row.realise && (
          <button onClick={() => marquerRealise(row.id)} className="text-slate-600 hover:text-slate-900 text-sm">
            Marquer realise
          </button>
        )}
      />
      <Pagination page={page} onPageChange={setPage} count={entretiensPage?.count ?? 0} pageSize={10} />

      {showCreate && (
        <FormModal
          title="Planifier un entretien"
          fields={[
            {
              name: 'moto',
              label: 'Moto',
              type: 'select',
              required: true,
              options: (motos ?? []).map((m) => ({ value: m.id, label: m.numero_serie })),
            },
            { name: 'type_entretien', label: 'Type', type: 'select', required: true, options: TYPES },
            { name: 'date_prevue', label: 'Date prevue', type: 'date', required: true },
            { name: 'kilometrage', label: 'Kilometrage', type: 'number' },
            { name: 'commentaire', label: 'Commentaire', type: 'textarea' },
          ]}
          onSubmit={(values) => create.mutateAsync(values)}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  )
}

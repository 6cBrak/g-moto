import { useState } from 'react'
import { useResourceListPaged } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import Pagination from '../../components/Pagination'
import { formatDateTime } from '../../lib/format'

const METHODES = {
  creation: 'Creation',
  modification: 'Modification',
  suppression: 'Suppression',
  action: 'Action',
}

const METHODE_OPTIONS = [
  { value: 'creation', label: 'Creation' },
  { value: 'modification', label: 'Modification' },
  { value: 'suppression', label: 'Suppression' },
  { value: 'action', label: 'Action' },
]

export default function JournalActivitePage() {
  const user = useAuthStore((state) => state.user)
  const [filtres, setFiltres] = useState({})
  const [page, setPage] = useState(1)
  const params = { ...Object.fromEntries(Object.entries(filtres).filter(([, v]) => v)), page }
  const { data: journalPage, isLoading } = useResourceListPaged('journal-activite', params)
  const entries = journalPage?.results

  const filterFields = [
    { name: 'utilisateur', label: 'Utilisateur', placeholder: 'Nom d\'utilisateur' },
    { name: 'ressource', label: 'Ressource', placeholder: 'ex: factures' },
    { name: 'methode', label: 'Methode', type: 'select', options: METHODE_OPTIONS },
    { name: 'date_debut', label: 'Du', type: 'date' },
    { name: 'date_fin', label: 'Au', type: 'date' },
  ]

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Journal d'activite</h1>
      <p className="text-slate-500 text-sm mb-4">
        Trace automatiquement chaque creation, modification, suppression et action sur l'application.
      </p>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => { setFiltres((prev) => ({ ...prev, [name]: value })); setPage(1) }}
      />

      <DataTable
        isLoading={isLoading}
        rows={entries}
        emptyMessage="Aucune activite enregistree."
        columns={[
          { key: 'date_action', label: 'Date', render: (r) => formatDateTime(r.date_action) },
          { key: 'utilisateur_username', label: 'Utilisateur' },
          ...(user?.role === 'admin' ? [{ key: 'agence_nom', label: 'Agence', render: (r) => r.agence_nom || '-' }] : []),
          { key: 'methode', label: 'Methode', render: (r) => METHODES[r.methode] ?? r.methode },
          { key: 'ressource', label: 'Ressource' },
          { key: 'objet_id', label: 'ID', render: (r) => r.objet_id || '-' },
          { key: 'chemin', label: 'Chemin' },
        ]}
      />
      <Pagination page={page} onPageChange={setPage} count={journalPage?.count ?? 0} />
    </div>
  )
}

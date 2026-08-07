import { useState } from 'react'
import { useResourceListAll, useResourceListPaged, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import FormModal from '../../components/FormModal'
import Pagination from '../../components/Pagination'
import { formatDateTime, formatMontant } from '../../lib/format'

const MOTIFS = [
  { value: 'versement_banque', label: 'Versement en banque' },
  { value: 'reglement_fournisseur', label: 'Reglement fournisseur' },
  { value: 'autre', label: 'Autre' },
]

export default function SortiesCaissePage() {
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceListAll('agences', {}, { enabled: user?.role === 'admin' })
  const { data: fournisseurs } = useResourceListAll('fournisseurs')
  const [filtres, setFiltres] = useState({})
  const [page, setPage] = useState(1)
  const params = { ...Object.fromEntries(Object.entries(filtres).filter(([, v]) => v)), page, page_size: 10 }
  const { data: sortiesPage, isLoading } = useResourceListPaged('sorties-caisse', params)
  const sorties = sortiesPage?.results
  const { create } = useResourceMutations('sorties-caisse')
  const [showCreate, setShowCreate] = useState(false)

  const fields = [
    { name: 'montant', label: 'Montant', type: 'number', step: '0.01', required: true },
    { name: 'motif', label: 'Motif', type: 'select', required: true, options: MOTIFS },
    {
      name: 'fournisseur',
      label: 'Fournisseur (si reglement fournisseur)',
      type: 'select',
      options: (fournisseurs ?? []).map((f) => ({ value: f.id, label: f.nom })),
    },
    { name: 'description', label: 'Description' },
  ]
  if (user?.role === 'admin') {
    fields.unshift({
      name: 'agence',
      label: 'Agence',
      type: 'select',
      required: true,
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    })
  }

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'Description' },
    { name: 'date_debut', label: 'Du', type: 'date' },
    { name: 'date_fin', label: 'Au', type: 'date' },
    { name: 'motif', label: 'Motif', type: 'select', options: MOTIFS },
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
        <h1 className="text-xl font-semibold text-slate-800">Sorties de caisse</h1>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 text-sm bg-slate-800 text-white rounded">
          + Nouvelle sortie
        </button>
      </div>
      <p className="text-slate-500 text-sm mb-4">
        Pour un mouvement d'argent qui sort physiquement de la caisse hors depense classee (ex : versement en banque).
      </p>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => { setFiltres((prev) => ({ ...prev, [name]: value })); setPage(1) }}
      />

      <DataTable
        isLoading={isLoading}
        rows={sorties}
        emptyMessage="Aucune sortie de caisse."
        columns={[
          { key: 'date_sortie', label: 'Date', render: (r) => formatDateTime(r.date_sortie) },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'motif', label: 'Motif', render: (r) => MOTIFS.find((m) => m.value === r.motif)?.label ?? r.motif },
          { key: 'fournisseur_nom', label: 'Fournisseur', render: (r) => r.fournisseur_nom || '-' },
          { key: 'description', label: 'Description', render: (r) => r.description || '-' },
          { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
          { key: 'cree_par_username', label: 'Cree par' },
        ]}
      />
      <Pagination page={page} onPageChange={setPage} count={sortiesPage?.count ?? 0} pageSize={10} />

      {showCreate && (
        <FormModal
          title="Nouvelle sortie de caisse"
          fields={fields}
          onSubmit={(values) => create.mutateAsync(values)}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  )
}

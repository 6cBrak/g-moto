import { useState } from 'react'
import { useResourceList, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import FormModal from '../../components/FormModal'
import { formatDateTime, formatMontant } from '../../lib/format'

const MOTIFS = [
  { value: 'versement_banque', label: 'Versement en banque' },
  { value: 'autre', label: 'Autre' },
]

export default function SortiesCaissePage() {
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceList('agences', {}, { enabled: user?.role === 'admin' })
  const [filtres, setFiltres] = useState({})
  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))
  const { data: sorties, isLoading } = useResourceList('sorties-caisse', params)
  const { create } = useResourceMutations('sorties-caisse')
  const [showCreate, setShowCreate] = useState(false)

  const fields = [
    { name: 'montant', label: 'Montant', type: 'number', step: '0.01', required: true },
    { name: 'motif', label: 'Motif', type: 'select', required: true, options: MOTIFS },
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
      <div className="flex justify-between items-center mb-4">
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
        onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value }))}
      />

      <DataTable
        isLoading={isLoading}
        rows={sorties}
        emptyMessage="Aucune sortie de caisse."
        columns={[
          { key: 'date_sortie', label: 'Date', render: (r) => formatDateTime(r.date_sortie) },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'motif', label: 'Motif', render: (r) => MOTIFS.find((m) => m.value === r.motif)?.label ?? r.motif },
          { key: 'description', label: 'Description', render: (r) => r.description || '-' },
          { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
          { key: 'cree_par_username', label: 'Cree par' },
        ]}
      />

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

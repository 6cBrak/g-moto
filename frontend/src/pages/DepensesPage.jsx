import { useState } from 'react'
import CrudPage from '../components/CrudPage'
import FilterBar from '../components/FilterBar'
import { useResourceList } from '../hooks/useResource'
import { useAuthStore } from '../store/authStore'
import { formatMontant, formatDate } from '../lib/format'

export default function DepensesPage() {
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceList('agences', {}, { enabled: user?.role === 'admin' })
  const { data: categories } = useResourceList('categories-depense')
  const [filtres, setFiltres] = useState({})
  const [showCategories, setShowCategories] = useState(false)

  const canWrite = user?.role === 'admin' || user?.role === 'gerant'
  const categorieOptions = (categories ?? [])
    .filter((c) => c.actif)
    .map((c) => ({ value: c.id, label: c.nom }))

  const fields = [
    { name: 'categorie', label: 'Categorie', type: 'select', required: true, options: categorieOptions },
    { name: 'montant', label: 'Montant', type: 'number', step: '0.01', required: true },
    { name: 'date_depense', label: 'Date', type: 'date', required: true },
    { name: 'description', label: 'Description' },
    { name: 'justificatif', label: 'Justificatif (optionnel)', type: 'file' },
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
    { name: 'categorie', label: 'Categorie', type: 'select', options: categorieOptions },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]
  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))

  return (
    <div>
      <div className="flex justify-end mb-3">
        <button
          onClick={() => setShowCategories((v) => !v)}
          className="text-sm text-slate-600 hover:text-slate-900 underline"
        >
          {showCategories ? 'Fermer la gestion des categories' : 'Gerer les categories'}
        </button>
      </div>

      {showCategories && (
        <div className="mb-8 border border-slate-200 rounded-lg p-4">
          <CrudPage
            resource="categories-depense"
            title="Categories de depense"
            canWrite={canWrite}
            columns={[
              { key: 'nom', label: 'Nom' },
              { key: 'actif', label: 'Actif', render: (r) => (r.actif ? 'Oui' : 'Non') },
            ]}
            fields={[
              { name: 'nom', label: 'Nom', required: true },
              { name: 'actif', label: 'Actif', type: 'checkbox' },
            ]}
          />
        </div>
      )}

      <CrudPage
        resource="depenses"
        title="Depenses"
        extraParams={params}
        filterBar={(
          <FilterBar
            filters={filterFields}
            values={filtres}
            onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value }))}
          />
        )}
        columns={[
          { key: 'date_depense', label: 'Date', render: (r) => formatDate(r.date_depense) },
          { key: 'categorie_nom', label: 'Categorie' },
          { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
          { key: 'description', label: 'Description' },
          { key: 'agence_nom', label: 'Agence' },
        ]}
        fields={fields}
      />
    </div>
  )
}

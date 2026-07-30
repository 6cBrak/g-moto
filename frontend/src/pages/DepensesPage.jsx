import { useState } from 'react'
import CrudPage from '../components/CrudPage'
import FilterBar from '../components/FilterBar'
import { useResourceList } from '../hooks/useResource'
import { useAuthStore } from '../store/authStore'
import { formatMontant, formatDate } from '../lib/format'

const CATEGORIES = [
  { value: 'loyer', label: 'Loyer' },
  { value: 'salaire', label: 'Salaire' },
  { value: 'carburant', label: 'Carburant' },
  { value: 'entretien', label: 'Entretien' },
  { value: 'fourniture', label: 'Fourniture' },
  { value: 'transport', label: 'Transport' },
  { value: 'autre', label: 'Autre' },
]

export default function DepensesPage() {
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceList('agences', {}, { enabled: user?.role === 'admin' })
  const [filtres, setFiltres] = useState({})

  const fields = [
    { name: 'categorie', label: 'Categorie', type: 'select', required: true, options: CATEGORIES },
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
    { name: 'categorie', label: 'Categorie', type: 'select', options: CATEGORIES },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]
  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))

  return (
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
        { key: 'categorie', label: 'Categorie' },
        { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
        { key: 'description', label: 'Description' },
        { key: 'agence_nom', label: 'Agence' },
      ]}
      fields={fields}
    />
  )
}

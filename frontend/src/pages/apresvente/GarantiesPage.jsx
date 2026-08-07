import { useState } from 'react'
import CrudPage from '../../components/CrudPage'
import FilterBar from '../../components/FilterBar'
import { useResourceListAll } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import { formatDate } from '../../lib/format'

export default function GarantiesPage() {
  const user = useAuthStore((state) => state.user)
  const { data: motos } = useResourceListAll('motos')
  const { data: agences } = useResourceListAll('agences', {}, { enabled: user?.role === 'admin' })
  const [filtres, setFiltres] = useState({})
  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'N° serie moto' },
    { name: 'date_debut', label: 'Debut du', type: 'date' },
    { name: 'date_fin', label: 'Debut au', type: 'date' },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]

  return (
    <CrudPage
      resource="garanties"
      title="Garanties"
      extraParams={params}
      filterBar={(
        <FilterBar
          filters={filterFields}
          values={filtres}
          onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value }))}
        />
      )}
      columns={[
        { key: 'moto_numero_serie', label: 'Moto' },
        { key: 'date_debut', label: 'Debut', render: (r) => formatDate(r.date_debut) },
        { key: 'duree_mois', label: 'Duree (mois)' },
        { key: 'date_fin', label: 'Fin', render: (r) => formatDate(r.date_fin) },
        { key: 'active', label: 'Statut', render: (r) => (r.active ? 'Active' : 'Expiree') },
      ]}
      fields={[
        {
          name: 'moto',
          label: 'Moto',
          type: 'select',
          required: true,
          options: (motos ?? []).map((m) => ({ value: m.id, label: m.numero_serie })),
        },
        { name: 'date_debut', label: 'Date debut', type: 'date', required: true },
        { name: 'duree_mois', label: 'Duree (mois)', type: 'number', required: true },
        { name: 'commentaire', label: 'Commentaire', type: 'textarea' },
      ]}
    />
  )
}

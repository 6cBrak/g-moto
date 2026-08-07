import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceListAll, useResourceListPaged, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import FormModal from '../../components/FormModal'
import Modal from '../../components/Modal'
import Pagination from '../../components/Pagination'
import { formatDateTime, formatMontant } from '../../lib/format'

const STATUTS = {
  en_stock: 'En stock',
  vendue: 'Vendue',
  transferee: 'Transferee',
  en_depot: 'En depot',
}

const STATUT_OPTIONS = [
  { value: 'en_stock', label: 'En stock' },
  { value: 'vendue', label: 'Vendue' },
  { value: 'transferee', label: 'Transferee' },
  { value: 'en_depot', label: 'En depot' },
]

function TransfererModal({ moto, onClose }) {
  const { data: agences } = useResourceListAll('agences')
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (payload) => apiClient.post(`/motos/${moto.id}/transferer/`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['motos'] })
      onClose()
    },
  })

  return (
    <FormModal
      title={`Transferer ${moto.numero_serie}`}
      submitLabel="Transferer"
      fields={[
        {
          name: 'agence_destination',
          label: 'Agence destination',
          type: 'select',
          required: true,
          options: (agences ?? []).filter((a) => a.id !== moto.agence).map((a) => ({ value: a.id, label: a.nom })),
        },
        { name: 'commentaire', label: 'Commentaire', type: 'textarea' },
      ]}
      onSubmit={(values) => mutation.mutateAsync(values)}
      onClose={onClose}
    />
  )
}

function HistoriqueModal({ moto, onClose }) {
  const { data, isLoading } = useQuery({
    queryKey: ['motos', moto.id, 'historique'],
    queryFn: async () => {
      const { data } = await apiClient.get(`/motos/${moto.id}/historique/`)
      return data
    },
  })

  return (
    <Modal title={`Historique ${moto.numero_serie}`} onClose={onClose} wide>
      <DataTable
        isLoading={isLoading}
        rows={data}
        columns={[
          { key: 'type_evenement', label: 'Evenement' },
          { key: 'agence_source_nom', label: 'Agence source' },
          { key: 'agence_destination_nom', label: 'Agence destination' },
          { key: 'utilisateur_username', label: 'Utilisateur' },
          { key: 'date_evenement', label: 'Date', render: (r) => formatDateTime(r.date_evenement) },
          { key: 'commentaire', label: 'Commentaire' },
        ]}
      />
    </Modal>
  )
}

export default function MotosPage() {
  const user = useAuthStore((state) => state.user)
  const [filtres, setFiltres] = useState({})
  const [page, setPage] = useState(1)
  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))
  const { data: motosPage, isLoading } = useResourceListPaged('motos', { ...params, page, page_size: 10 })
  const motos = motosPage?.results
  const { data: typesMoto } = useResourceListAll('types-moto')
  const { data: couleurs } = useResourceListAll('couleurs')
  const { data: arrivages } = useResourceListAll('arrivages')
  const { data: agences } = useResourceListAll('agences', {}, { enabled: user?.role === 'admin' })
  const { create } = useResourceMutations('motos')

  const [showCreate, setShowCreate] = useState(false)
  const [transferTarget, setTransferTarget] = useState(null)
  const [historiqueTarget, setHistoriqueTarget] = useState(null)

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'N° serie ou immatriculation' },
    { name: 'date_debut', label: 'Du', type: 'date' },
    { name: 'date_fin', label: 'Au', type: 'date' },
    { name: 'statut', label: 'Statut', type: 'select', options: STATUT_OPTIONS },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]

  const peutTransferer = user?.role === 'admin' || user?.role === 'gerant'

  const fields = [
    { name: 'numero_serie', label: 'Numero de serie', required: true },
    {
      name: 'type_moto',
      label: 'Type de moto',
      type: 'select',
      required: true,
      options: (typesMoto ?? []).map((t) => ({ value: t.id, label: `${t.marque_nom} ${t.nom}` })),
      onChange: (value, prev) => {
        if (prev.numero_serie) return null
        const type = (typesMoto ?? []).find((t) => String(t.id) === String(value))
        return type?.code ? { numero_serie: type.code } : null
      },
    },
    {
      name: 'couleur',
      label: 'Couleur',
      type: 'select',
      required: true,
      options: (couleurs ?? []).map((c) => ({ value: c.id, label: c.nom })),
    },
    {
      name: 'arrivage',
      label: 'Arrivage',
      type: 'select',
      required: true,
      options: (arrivages ?? []).map((a) => ({ value: a.id, label: `${a.numero_bon} (${a.agence_nom})` })),
    },
    { name: 'prix_achat', label: 'Prix achat', type: 'number', step: '0.01' },
    { name: 'immatriculation', label: 'Immatriculation' },
  ]

  if (user?.role === 'admin') {
    fields.push({
      name: 'agence',
      label: 'Agence',
      type: 'select',
      required: true,
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    })
  }

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Motos</h1>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 text-sm bg-slate-800 text-white rounded">
          + Nouvelle moto
        </button>
      </div>

      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => { setFiltres((prev) => ({ ...prev, [name]: value })); setPage(1) }}
      />

      <DataTable
        isLoading={isLoading}
        rows={motos}
        rowClassName={(row) => (row.statut === 'vendue' ? 'bg-amber-50' : row.statut === 'en_depot' ? 'bg-blue-50' : '')}
        columns={[
          { key: 'numero_serie', label: 'N° serie' },
          { key: 'type_moto_label', label: 'Type' },
          { key: 'couleur_nom', label: 'Couleur' },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'arrivage_numero_bon', label: 'Arrivage', render: (r) => r.arrivage_numero_bon || '-' },
          { key: 'immatriculation', label: 'Immatriculation', render: (r) => r.immatriculation || '-' },
          { key: 'prix_achat', label: 'Prix revient', render: (r) => (r.prix_achat != null ? `${formatMontant(r.prix_achat)} F` : '-') },
          {
            key: 'statut',
            label: 'Statut',
            render: (r) => (
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                r.statut === 'vendue' ? 'bg-amber-200 text-amber-800'
                  : r.statut === 'transferee' ? 'bg-blue-100 text-blue-700'
                    : r.statut === 'en_depot' ? 'bg-purple-100 text-purple-700'
                      : 'bg-green-100 text-green-700'
              }`}>
                {STATUTS[r.statut] ?? r.statut}{r.statut === 'en_depot' && r.depot_client_nom ? ` (${r.depot_client_nom})` : ''}
              </span>
            ),
          },
        ]}
        actions={(row) => (
          <>
            <button onClick={() => setHistoriqueTarget(row)} className="text-slate-600 hover:text-slate-900 text-sm">
              Historique
            </button>
            {peutTransferer && row.statut === 'en_stock' && (
              <button onClick={() => setTransferTarget(row)} className="text-slate-600 hover:text-slate-900 text-sm">
                Transferer
              </button>
            )}
          </>
        )}
      />
      <Pagination page={page} onPageChange={setPage} count={motosPage?.count ?? 0} pageSize={10} />

      {showCreate && (
        <FormModal
          title="Nouvelle moto"
          fields={fields}
          onSubmit={(values) => create.mutateAsync(values)}
          onClose={() => setShowCreate(false)}
        />
      )}
      {transferTarget && <TransfererModal moto={transferTarget} onClose={() => setTransferTarget(null)} />}
      {historiqueTarget && <HistoriqueModal moto={historiqueTarget} onClose={() => setHistoriqueTarget(null)} />}
    </div>
  )
}

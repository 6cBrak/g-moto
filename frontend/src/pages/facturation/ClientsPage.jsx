import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '../../api/client'
import { useResourceList, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FilterBar from '../../components/FilterBar'
import FormModal from '../../components/FormModal'
import Modal from '../../components/Modal'
import { formatMontant } from '../../lib/format'

const SEGMENTS = [
  { value: 'standard', label: 'Standard' },
  { value: 'vip', label: 'VIP' },
  { value: 'revendeur', label: 'Revendeur' },
]

function HistoriqueClientModal({ client, onClose }) {
  const { data, isLoading } = useQuery({
    queryKey: ['clients', client.id, 'historique'],
    queryFn: async () => (await apiClient.get(`/clients/${client.id}/historique/`)).data,
  })
  const { data: depots, isLoading: loadingDepots } = useQuery({
    queryKey: ['clients', client.id, 'depots-en-cours'],
    queryFn: async () => (await apiClient.get(`/clients/${client.id}/depots_en_cours/`)).data,
  })

  return (
    <Modal title={`Historique de ${client.nom}`} onClose={onClose} wide>
      <DataTable
        isLoading={isLoading}
        rows={data?.factures}
        columns={[
          { key: 'numero_facture', label: 'Facture' },
          { key: 'date_facture', label: 'Date' },
          { key: 'total', label: 'Total', render: (r) => `${formatMontant(r.total)} F` },
          { key: 'total_verse', label: 'Verse', render: (r) => `${formatMontant(r.total_verse)} F` },
          { key: 'solde', label: 'Solde', render: (r) => `${formatMontant(r.solde)} F` },
          { key: 'carte_grise_retiree', label: 'Carte grise retiree', render: (r) => (r.carte_grise_retiree === null ? '-' : r.carte_grise_retiree ? 'Oui' : 'Non') },
        ]}
      />

      <h3 className="text-sm font-medium text-slate-700 mt-6 mb-2">Motos actuellement en depot</h3>
      <DataTable
        isLoading={loadingDepots}
        rows={depots}
        emptyMessage="Aucune moto en depot chez ce client."
        columns={[
          { key: 'moto_numero_serie', label: 'N° serie' },
          { key: 'moto_type_label', label: 'Type' },
          { key: 'moto_couleur_nom', label: 'Couleur' },
        ]}
      />
    </Modal>
  )
}

function ClientsDebiteursPanel() {
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceList('agences', {}, { enabled: user?.role === 'admin' })
  const [filtres, setFiltres] = useState({})
  const params = Object.fromEntries(Object.entries(filtres).filter(([, v]) => v))

  const { data, isLoading } = useQuery({
    queryKey: ['caisse', 'clients-debiteurs', params],
    queryFn: async () => (await apiClient.get('/caisse/clients-debiteurs/', { params })).data,
  })

  const filterFields = [
    { name: 'q', label: 'Recherche', placeholder: 'Nom du client' },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Clients debiteurs (reste a payer)</h2>
      <FilterBar
        filters={filterFields}
        values={filtres}
        onChange={(name, value) => setFiltres((prev) => ({ ...prev, [name]: value }))}
      />
      <DataTable
        isLoading={isLoading}
        rows={data}
        emptyMessage="Aucun client debiteur."
        columns={[
          { key: 'client_nom', label: 'Client' },
          { key: 'agence', label: 'Agence' },
          { key: 'total_facture', label: 'Total facture', render: (r) => `${formatMontant(r.total_facture)} F` },
          { key: 'total_verse', label: 'Total verse', render: (r) => `${formatMontant(r.total_verse)} F` },
          { key: 'solde', label: 'Reste a payer', render: (r) => `${formatMontant(r.solde)} F` },
        ]}
      />
    </div>
  )
}

function RelancesPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['clients', 'relances'],
    queryFn: async () => (await apiClient.get('/clients/relances/')).data,
  })

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold text-slate-800 mb-3">Relances (cartes grises / quittances en attente)</h2>
      <DataTable
        isLoading={isLoading}
        rows={data}
        emptyMessage="Aucune relance en attente."
        columns={[
          { key: 'type', label: 'Type' },
          { key: 'client', label: 'Client' },
          { key: 'facture', label: 'Facture' },
          { key: 'agence', label: 'Agence' },
          { key: 'jours_en_attente', label: 'Jours en attente' },
        ]}
      />
    </div>
  )
}

export default function ClientsPage() {
  const [segment, setSegment] = useState('')
  const { data: clients, isLoading } = useResourceList('clients', segment ? { segment } : {})
  const { create, update } = useResourceMutations('clients')
  const [modalMode, setModalMode] = useState(null)
  const [editing, setEditing] = useState(null)
  const [historiqueTarget, setHistoriqueTarget] = useState(null)
  const user = useAuthStore((state) => state.user)
  const { data: agences } = useResourceList('agences', {}, { enabled: user?.role === 'admin' })

  const clientFields = [
    { name: 'nom', label: 'Nom', required: true },
    { name: 'telephone', label: 'Telephone' },
    { name: 'email', label: 'Email', type: 'email' },
    { name: 'adresse', label: 'Adresse' },
    { name: 'segment', label: 'Segment', type: 'select', options: SEGMENTS },
    ...(user?.role === 'admin' ? [{
      name: 'agence',
      label: 'Agence',
      type: 'select',
      required: true,
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    }] : []),
  ]

  const handleSubmit = async (values) => {
    if (modalMode === 'create') {
      await create.mutateAsync(values)
    } else {
      await update.mutateAsync({ id: editing.id, payload: values })
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Clients</h1>
        <div className="flex items-center gap-3">
          <select value={segment} onChange={(e) => setSegment(e.target.value)} className="border border-slate-300 rounded px-2 py-1 text-sm">
            <option value="">Tous les segments</option>
            {SEGMENTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <button onClick={() => { setEditing(null); setModalMode('create') }} className="px-4 py-2 text-sm bg-slate-800 text-white rounded">
            + Nouveau client
          </button>
        </div>
      </div>

      <DataTable
        isLoading={isLoading}
        rows={clients}
        columns={[
          { key: 'nom', label: 'Nom' },
          { key: 'telephone', label: 'Telephone' },
          { key: 'segment', label: 'Segment' },
          { key: 'agence_nom', label: 'Agence' },
        ]}
        actions={(row) => (
          <>
            <Link to={`/factures/nouvelle?client=${row.id}`} className="text-slate-600 hover:text-slate-900 text-sm">
              Facturer
            </Link>
            <button onClick={() => setHistoriqueTarget(row)} className="text-slate-600 hover:text-slate-900 text-sm">
              Historique
            </button>
            <button onClick={() => { setEditing(row); setModalMode('edit') }} className="text-slate-600 hover:text-slate-900 text-sm">
              Modifier
            </button>
          </>
        )}
      />

      {modalMode && (
        <FormModal
          title={modalMode === 'create' ? 'Nouveau client' : 'Modifier client'}
          fields={clientFields}
          initialValues={editing ?? {}}
          onSubmit={handleSubmit}
          onClose={() => setModalMode(null)}
        />
      )}
      {historiqueTarget && <HistoriqueClientModal client={historiqueTarget} onClose={() => setHistoriqueTarget(null)} />}

      <ClientsDebiteursPanel />
      <RelancesPanel />
    </div>
  )
}

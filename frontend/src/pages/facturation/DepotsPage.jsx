import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceListAll, useResourceListPaged, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import Pagination from '../../components/Pagination'
import { formatDateTime } from '../../lib/format'
import { ouvrirPdf } from '../../lib/pdf'

const STATUTS_DEPOT = {
  en_cours: 'En cours',
  retournee: 'Retournee',
  vendue: 'Vendue',
}

function EnvoiDepotPanel({ envoi, onClose }) {
  const queryClient = useQueryClient()
  const retourner = useMutation({
    mutationFn: (ligneId) => apiClient.post(`/depots/${ligneId}/retourner/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['envois-depot'] }),
  })

  return (
    <div className="mt-6 border-t border-slate-200 pt-4">
      <div className="flex flex-wrap justify-between items-center gap-2 mb-3">
        <h2 className="text-lg font-semibold text-slate-800">
          Depot chez {envoi.client_nom} du {formatDateTime(envoi.date_envoi)}
        </h2>
        <div className="flex items-center gap-3">
          <button onClick={() => ouvrirPdf(`/envois-depot/${envoi.id}/pdf/`)} className="text-sm text-slate-600 hover:text-slate-900 underline">
            Bon PDF
          </button>
          <button onClick={onClose} className="text-sm text-slate-500 hover:text-slate-800">Fermer</button>
        </div>
      </div>

      <DataTable
        rows={envoi.lignes}
        columns={[
          { key: 'moto_numero_serie', label: 'N° serie' },
          { key: 'moto_type_label', label: 'Type' },
          { key: 'moto_couleur_nom', label: 'Couleur' },
          { key: 'statut', label: 'Statut', render: (r) => STATUTS_DEPOT[r.statut] ?? r.statut },
        ]}
        actions={(row) => row.statut === 'en_cours' && (
          <button
            onClick={() => retourner.mutate(row.id)}
            disabled={retourner.isPending}
            className="text-slate-600 hover:text-slate-900 text-sm disabled:opacity-50"
          >
            Marquer retournee
          </button>
        )}
      />
    </div>
  )
}

export default function DepotsPage() {
  const user = useAuthStore((state) => state.user)
  const [page, setPage] = useState(1)
  const { data: envoisPage, isLoading } = useResourceListPaged('envois-depot', { page })
  const envois = envoisPage?.results
  const { data: clients } = useResourceListAll('clients')
  const { data: motos } = useResourceListAll('motos')
  const { data: agences } = useResourceListAll('agences', {}, { enabled: user?.role === 'admin' })
  const { create } = useResourceMutations('envois-depot')

  const [showCreate, setShowCreate] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const [clientId, setClientId] = useState('')
  const [agenceId, setAgenceId] = useState('')
  const [motosChoisies, setMotosChoisies] = useState([])
  const [commentaire, setCommentaire] = useState('')
  const [error, setError] = useState(null)

  const estAdmin = user?.role === 'admin'
  const selected = (envois ?? []).find((e) => e.id === selectedId) ?? null
  const motosDisponibles = (motos ?? []).filter((m) => (
    m.statut === 'en_stock' && (!estAdmin || !agenceId || String(m.agence) === String(agenceId))
  ))

  const toggleMoto = (id) => {
    setMotosChoisies((prev) => (prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    try {
      await create.mutateAsync({
        client: clientId,
        agence: estAdmin ? agenceId : undefined,
        motos: motosChoisies,
        commentaire,
      })
      setShowCreate(false)
      setClientId('')
      setAgenceId('')
      setMotosChoisies([])
      setCommentaire('')
    } catch (err) {
      const data = err?.response?.data
      setError(data ? JSON.stringify(data) : 'Une erreur est survenue.')
    }
  }

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
        <h1 className="text-xl font-semibold text-slate-800">Depots revendeurs</h1>
        <button onClick={() => setShowCreate((v) => !v)} className="px-4 py-2 text-sm bg-slate-800 text-white rounded">
          + Envoyer en depot
        </button>
      </div>
      <p className="text-slate-500 text-sm mb-4">
        Pour un client revendeur qui prend des motos a vendre dans sa boutique, sans facturation immediate.
        Quand il revient, marque les motos non vendues comme "retournees", et facture normalement celles qu'il a vendues.
      </p>

      {showCreate && (
        <form onSubmit={handleSubmit} className="border border-slate-200 rounded p-4 mb-6 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-slate-600 mb-1">Client</label>
              <select
                className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                value={clientId}
                required
                onChange={(e) => setClientId(e.target.value)}
              >
                <option value="">-- choisir --</option>
                {(clients ?? []).map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}
              </select>
            </div>
            {estAdmin && (
              <div>
                <label className="block text-sm text-slate-600 mb-1">Agence</label>
                <select
                  className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                  value={agenceId}
                  required
                  onChange={(e) => setAgenceId(e.target.value)}
                >
                  <option value="">-- choisir --</option>
                  {(agences ?? []).map((a) => <option key={a.id} value={a.id}>{a.nom}</option>)}
                </select>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm text-slate-600 mb-1">
              Motos a envoyer ({motosChoisies.length} selectionnee(s))
            </label>
            <div className="max-h-48 overflow-y-auto border border-slate-200 rounded p-2 space-y-1">
              {motosDisponibles.map((m) => (
                <label key={m.id} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={motosChoisies.includes(m.id)} onChange={() => toggleMoto(m.id)} />
                  {m.numero_serie} - {m.type_moto_label} - {m.couleur_nom}
                </label>
              ))}
              {motosDisponibles.length === 0 && <p className="text-sm text-slate-500">Aucune moto disponible.</p>}
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-600 mb-1">Commentaire</label>
            <textarea
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
              value={commentaire}
              onChange={(e) => setCommentaire(e.target.value)}
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={create.isPending || motosChoisies.length === 0}
            className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
          >
            Envoyer en depot
          </button>
        </form>
      )}

      <DataTable
        isLoading={isLoading}
        rows={envois}
        onRowClick={(row) => setSelectedId(row.id)}
        selectedId={selectedId}
        emptyMessage="Aucun depot enregistre."
        columns={[
          { key: 'date_envoi', label: 'Date', render: (r) => formatDateTime(r.date_envoi) },
          { key: 'client_nom', label: 'Client' },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'nb_motos', label: 'Nb motos', render: (r) => r.lignes.length },
          {
            key: 'statut_resume',
            label: 'Statut',
            render: (r) => {
              const enCours = r.lignes.filter((l) => l.statut === 'en_cours').length
              return enCours > 0 ? `${enCours} en cours` : 'Solde'
            },
          },
        ]}
      />
      <Pagination page={page} onPageChange={setPage} count={envoisPage?.count ?? 0} />

      {selected && <EnvoiDepotPanel envoi={selected} onClose={() => setSelectedId(null)} />}
    </div>
  )
}

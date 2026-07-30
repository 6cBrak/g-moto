import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceList } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import { useUiStore } from '../../store/uiStore'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import { formatDate, formatDateTime, formatHeure, formatMontant } from '../../lib/format'

function FermerSessionModal({ session, onClose, onSuccess }) {
  const [montant, setMontant] = useState('')
  const [erreur, setErreur] = useState(null)

  const fermer = useMutation({
    mutationFn: (payload) => apiClient.post(`/sessions-caisse/${session.id}/fermer/`, payload),
    onSuccess: () => { onSuccess(); onClose() },
    onError: (err) => setErreur(err?.response?.data?.detail ?? 'Erreur lors de la fermeture.'),
  })

  return (
    <Modal title={`Fermer la caisse du ${formatDate(session.date_session)} (${session.agence_nom})`} onClose={onClose}>
      <p className="text-sm text-slate-600 mb-3">
        Montant theorique : <strong>{formatMontant(session.montant_theorique)} F</strong>
      </p>
      <label className="block text-sm text-slate-600 mb-1">Montant compte a la fermeture</label>
      <input
        type="number"
        step="0.01"
        className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3"
        value={montant}
        onChange={(e) => setMontant(e.target.value)}
      />
      {erreur && <p className="text-red-600 text-sm mb-3">{erreur}</p>}
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900">Annuler</button>
        <button
          onClick={() => fermer.mutate({ montant_fermeture: montant })}
          disabled={fermer.isPending || !montant}
          className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
        >
          Fermer
        </button>
      </div>
    </Modal>
  )
}

export default function SessionCaissePage() {
  const user = useAuthStore((state) => state.user)
  const agenceFiltre = useUiStore((state) => state.agenceFiltre)
  const queryClient = useQueryClient()

  const agenceRequise = user?.role === 'admin' && !agenceFiltre
  const params = { agence: agenceFiltre || undefined }

  const { data: courante, isLoading: loadingCourante } = useQuery({
    queryKey: ['caisse', 'session-courante', agenceFiltre],
    queryFn: async () => (await apiClient.get('/sessions-caisse/courante/', { params })).data,
    enabled: !agenceRequise,
  })
  const { data: historique, isLoading: loadingHistorique } = useResourceList(
    'sessions-caisse', params, { enabled: !agenceRequise },
  )

  const [montantOuverture, setMontantOuverture] = useState('')
  const [montantFermeture, setMontantFermeture] = useState('')
  const [erreur, setErreur] = useState(null)
  const [fermetureTarget, setFermetureTarget] = useState(null)

  const invalider = () => {
    queryClient.invalidateQueries({ queryKey: ['caisse', 'session-courante'] })
    queryClient.invalidateQueries({ queryKey: ['sessions-caisse'] })
  }

  const ouvrir = useMutation({
    mutationFn: (payload) => apiClient.post('/sessions-caisse/ouvrir/', payload),
    onSuccess: () => { invalider(); setMontantOuverture(''); setErreur(null) },
    onError: (err) => setErreur(err?.response?.data?.detail ?? 'Erreur lors de l\'ouverture.'),
  })

  const fermer = useMutation({
    mutationFn: ({ id, ...payload }) => apiClient.post(`/sessions-caisse/${id}/fermer/`, payload),
    onSuccess: () => { invalider(); setMontantFermeture(''); setErreur(null) },
    onError: (err) => setErreur(err?.response?.data?.detail ?? 'Erreur lors de la fermeture.'),
  })

  const reouvrir = useMutation({
    mutationFn: (id) => apiClient.post(`/sessions-caisse/${id}/reouvrir/`),
    onSuccess: () => { invalider(); setErreur(null) },
    onError: (err) => setErreur(err?.response?.data?.detail ?? 'Erreur lors de la reouverture.'),
  })

  const session = courante?.session ?? null
  const estOuverte = session && session.statut === 'ouverte'

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-slate-800">Ouverture / fermeture de caisse</h1>

      {agenceRequise ? (
        <p className="text-slate-500 text-sm">Selectionnez une agence (en haut a droite) pour gerer sa caisse du jour.</p>
      ) : loadingCourante ? (
        <p className="text-slate-500 text-sm">Chargement...</p>
      ) : !session ? (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm max-w-md">
          <p className="text-slate-600 mb-4">La caisse du jour n'est pas encore ouverte.</p>
          <label className="block text-sm text-slate-600 mb-1">Montant d'ouverture</label>
          <input
            type="number"
            step="0.01"
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3"
            value={montantOuverture || courante?.solde_precedent || ''}
            onChange={(e) => setMontantOuverture(e.target.value)}
          />
          <p className="text-xs text-slate-500 mb-3">
            Solde de fermeture precedent : {formatMontant(courante?.solde_precedent)} F (pre-rempli, modifiable)
          </p>
          <button
            onClick={() => ouvrir.mutate({
              montant_ouverture: montantOuverture || courante?.solde_precedent,
              agence: agenceFiltre || undefined,
            })}
            disabled={ouvrir.isPending}
            className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
          >
            Ouvrir la caisse
          </button>
        </div>
      ) : estOuverte ? (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm max-w-md">
          <p className="text-slate-600 mb-1">Caisse ouverte depuis le {formatDateTime(session.date_ouverture)}</p>
          <p className="text-sm text-slate-500 mb-1">Ouverte par {session.ouvert_par_username}</p>
          <p className="text-sm text-slate-500 mb-4">Montant d'ouverture : {formatMontant(session.montant_ouverture)} F</p>
          <p className="text-sm text-slate-600 mb-3">
            Montant theorique actuel : <strong>{formatMontant(session.montant_theorique)} F</strong>
          </p>
          <label className="block text-sm text-slate-600 mb-1">Montant compte a la fermeture</label>
          <input
            type="number"
            step="0.01"
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3"
            value={montantFermeture}
            onChange={(e) => setMontantFermeture(e.target.value)}
          />
          <button
            onClick={() => fermer.mutate({ id: session.id, montant_fermeture: montantFermeture })}
            disabled={fermer.isPending || !montantFermeture}
            className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
          >
            Fermer la caisse
          </button>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm max-w-md">
          <p className="text-slate-600">La caisse du jour est deja fermee.</p>
          <p className="text-sm text-slate-500 mt-1">
            Ouverture : {formatMontant(session.montant_ouverture)} F — Fermeture : {formatMontant(session.montant_fermeture)} F
          </p>
          <p className="text-sm text-slate-500">
            Ecart : {formatMontant(session.ecart)} F
          </p>
        </div>
      )}

      {erreur && <p className="text-red-600 text-sm">{erreur}</p>}

      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-2">Historique des sessions</h2>
        <DataTable
          isLoading={loadingHistorique}
          rows={historique}
          emptyMessage="Aucune session enregistree."
          columns={[
            { key: 'date_session', label: 'Date', render: (r) => formatDate(r.date_session) },
            { key: 'agence_nom', label: 'Agence' },
            { key: 'montant_ouverture', label: 'Ouverture', render: (r) => `${formatMontant(r.montant_ouverture)} F` },
            { key: 'heure_ouverture', label: 'Heure ouverture', render: (r) => formatHeure(r.date_ouverture) },
            { key: 'ouvert_par_username', label: 'Ouvert par' },
            { key: 'montant_fermeture', label: 'Fermeture', render: (r) => (r.montant_fermeture != null ? `${formatMontant(r.montant_fermeture)} F` : '-') },
            { key: 'heure_fermeture', label: 'Heure fermeture', render: (r) => formatHeure(r.date_fermeture) },
            { key: 'ferme_par_username', label: 'Ferme par', render: (r) => r.ferme_par_username || '-' },
            { key: 'montant_theorique', label: 'Theorique', render: (r) => `${formatMontant(r.montant_theorique)} F` },
            {
              key: 'ecart',
              label: 'Ecart',
              render: (r) => {
                if (r.ecart == null) return '-'
                const ecart = Number(r.ecart)
                return (
                  <span className={ecart === 0 ? 'text-green-700' : 'text-red-600 font-medium'}>
                    {formatMontant(r.ecart)} F
                  </span>
                )
              },
            },
            { key: 'statut', label: 'Statut', render: (r) => (r.statut === 'ouverte' ? 'Ouverte' : 'Fermee') },
          ]}
          actions={(row) => (
            row.statut === 'ouverte' ? (
              <button onClick={() => setFermetureTarget(row)} className="text-slate-600 hover:text-slate-900 text-sm">
                Fermer
              </button>
            ) : (
              <button
                onClick={() => reouvrir.mutate(row.id)}
                disabled={reouvrir.isPending}
                className="text-slate-600 hover:text-slate-900 text-sm disabled:opacity-50"
              >
                Rouvrir
              </button>
            )
          )}
        />
      </div>

      {fermetureTarget && (
        <FermerSessionModal
          session={fermetureTarget}
          onClose={() => setFermetureTarget(null)}
          onSuccess={invalider}
        />
      )}
    </div>
  )
}

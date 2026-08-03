import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import Modal from '../../components/Modal'

const LABELS = {
  versements: 'Versements',
  sorties_caisse: 'Sorties de caisse',
  sessions_caisse: 'Sessions de caisse',
  quittances: 'Quittances',
  cartes_grises: 'Cartes grises',
  declarations: 'Declarations',
  depots_vente: 'Depots-vente',
  envois_depot: 'Envois en depot',
  lignes_facture: 'Lignes de facture',
  factures: 'Factures',
  clients: 'Clients',
  motos_a_remettre_en_stock: 'Motos a remettre en stock',
}

function PurgeModal({ counts, onClose, onSuccess }) {
  const [saisie, setSaisie] = useState('')
  const [erreur, setErreur] = useState(null)

  const purger = useMutation({
    mutationFn: () => apiClient.post('/admin/purge-donnees-commerciales/', { confirmation: 'SUPPRIMER' }),
    onSuccess: (res) => { onSuccess(res.data); onClose() },
    onError: (err) => setErreur(err?.response?.data?.detail ?? 'Erreur lors de la purge.'),
  })

  return (
    <Modal title="Confirmer la purge des donnees commerciales" onClose={onClose}>
      <p className="text-sm text-slate-600 mb-3">
        Cette action est <strong>irreversible</strong>. Elle va supprimer :
      </p>
      <ul className="text-sm text-slate-700 mb-4 space-y-0.5">
        {Object.entries(counts ?? {}).map(([key, value]) => (
          <li key={key}>
            {LABELS[key] ?? key} : <strong>{value}</strong>
          </li>
        ))}
      </ul>
      <p className="text-sm text-slate-600 mb-1">
        Tape <strong>SUPPRIMER</strong> pour confirmer.
      </p>
      <input
        type="text"
        className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3"
        value={saisie}
        onChange={(e) => setSaisie(e.target.value)}
      />
      {erreur && <p className="text-red-600 text-sm mb-3">{erreur}</p>}
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900">
          Annuler
        </button>
        <button
          onClick={() => purger.mutate()}
          disabled={purger.isPending || saisie !== 'SUPPRIMER'}
          className="px-4 py-2 text-sm bg-red-600 text-white rounded disabled:opacity-50"
        >
          Supprimer definitivement
        </button>
      </div>
    </Modal>
  )
}

export default function ParametragePage() {
  const [showPurge, setShowPurge] = useState(false)
  const [resultat, setResultat] = useState(null)

  const { data: counts, isLoading, refetch } = useQuery({
    queryKey: ['admin', 'purge-donnees-commerciales'],
    queryFn: async () => (await apiClient.get('/admin/purge-donnees-commerciales/')).data,
  })

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-slate-800">Parametrage</h1>

      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm max-w-lg">
        <h2 className="font-medium text-slate-800 mb-1">Purge des donnees commerciales de test</h2>
        <p className="text-sm text-slate-600 mb-4">
          Supprime toutes les factures, versements, caisse (sessions et sorties), clients et
          depots-vente. Les motos vendues ou en depot repassent en stock disponible. Le reste du
          module stock (motos, arrivages, historique) n'est pas touche.
        </p>

        {isLoading ? (
          <p className="text-sm text-slate-500">Chargement...</p>
        ) : (
          <ul className="text-sm text-slate-700 mb-4 space-y-0.5">
            {Object.entries(counts ?? {}).map(([key, value]) => (
              <li key={key}>
                {LABELS[key] ?? key} : <strong>{value}</strong>
              </li>
            ))}
          </ul>
        )}

        {resultat && (
          <p className="text-green-700 text-sm mb-3">Donnees supprimees avec succes.</p>
        )}

        <button
          onClick={() => setShowPurge(true)}
          className="px-4 py-2 text-sm bg-red-600 text-white rounded"
        >
          Purger les donnees commerciales
        </button>
      </div>

      {showPurge && (
        <PurgeModal
          counts={counts}
          onClose={() => setShowPurge(false)}
          onSuccess={(res) => { setResultat(res); refetch() }}
        />
      )}
    </div>
  )
}

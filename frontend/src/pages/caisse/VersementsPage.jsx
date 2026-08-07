import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceListPaged } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Pagination from '../../components/Pagination'
import { formatDateTime, formatMontant } from '../../lib/format'
import { ouvrirPdf } from '../../lib/pdf'

function AnnulerVersementModal({ versement, onClose, onSuccess }) {
  const [erreur, setErreur] = useState(null)
  const mutation = useMutation({
    mutationFn: () => apiClient.post(`/versements/${versement.id}/annuler/`),
    onSuccess: () => { onSuccess(); onClose() },
    onError: (err) => setErreur(err?.response?.data?.detail ?? 'Erreur lors de l\'annulation.'),
  })

  return (
    <Modal title="Annuler ce versement" onClose={onClose}>
      <p className="text-sm text-slate-600 mb-3">
        Facture {versement.facture_numero} — Montant : <strong>{formatMontant(versement.montant)} F</strong>.
        Cette action est irreversible.
      </p>
      {erreur && <p className="text-red-600 text-sm mb-3">{erreur}</p>}
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900">
          Retour
        </button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="px-4 py-2 text-sm bg-red-600 text-white rounded disabled:opacity-50"
        >
          Confirmer l'annulation
        </button>
      </div>
    </Modal>
  )
}

export default function VersementsPage() {
  const user = useAuthStore((state) => state.user)
  const canAnnuler = user?.role === 'admin' || user?.role === 'gerant'
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const { data: versementsPage, isLoading } = useResourceListPaged('versements', { page })
  const versements = versementsPage?.results
  const [annulerTarget, setAnnulerTarget] = useState(null)

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Versements</h1>
      <p className="text-slate-500 text-sm mb-4">
        Les versements se creent depuis la page d'une facture.
      </p>
      <DataTable
        isLoading={isLoading}
        rows={versements}
        columns={[
          { key: 'date_versement', label: 'Date', render: (r) => formatDateTime(r.date_versement) },
          { key: 'facture_numero', label: 'Facture' },
          { key: 'client_nom', label: 'Client' },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
          { key: 'mode_paiement', label: 'Mode' },
          {
            key: 'statut',
            label: 'Statut',
            render: (r) => (r.statut === 'annule'
              ? <span className="text-red-600 text-xs font-medium">Annule</span>
              : <span className="text-green-700 text-xs font-medium">Valide</span>),
          },
        ]}
        actions={(row) => (
          <>
            <Link to={`/factures/${row.facture}`} className="text-slate-600 hover:text-slate-900 text-sm">
              Voir la facture
            </Link>
            <button onClick={() => ouvrirPdf(`/versements/${row.id}/recu/`)} className="text-slate-600 hover:text-slate-900 text-sm">
              Recu PDF
            </button>
            {canAnnuler && row.statut === 'valide' && (
              <button onClick={() => setAnnulerTarget(row)} className="text-red-600 hover:text-red-800 text-sm">
                Annuler
              </button>
            )}
          </>
        )}
      />
      <Pagination page={page} onPageChange={setPage} count={versementsPage?.count ?? 0} />

      {annulerTarget && (
        <AnnulerVersementModal
          versement={annulerTarget}
          onClose={() => setAnnulerTarget(null)}
          onSuccess={() => queryClient.invalidateQueries({ queryKey: ['versements'] })}
        />
      )}
    </div>
  )
}

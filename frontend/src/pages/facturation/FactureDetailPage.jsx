import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import { useResourceList, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import Modal from '../../components/Modal'
import { formatDateTime, formatMontant } from '../../lib/format'
import { ouvrirPdf } from '../../lib/pdf'

const MODES_PAIEMENT = [
  { value: 'especes', label: 'Especes' },
  { value: 'orange_money', label: 'Orange Money' },
  { value: 'moov_money', label: 'Moov Money' },
  { value: 'wave', label: 'Wave' },
  { value: 'virement', label: 'Virement bancaire' },
  { value: 'cheque', label: 'Cheque' },
]

function erreurMessage(err) {
  const data = err?.response?.data
  if (!data) return 'Une erreur est survenue.'
  return Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' — ')
}

function RetraitModal({ resource, item, onClose, onDone }) {
  const [nom, setNom] = useState('')
  const [telephone, setTelephone] = useState('')
  const [erreur, setErreur] = useState(null)
  const mutation = useMutation({
    mutationFn: () => apiClient.post(`/${resource}/${item.id}/retirer/`, {
      retirer_nom: nom, retirer_telephone: telephone,
    }),
    onSuccess: () => { onDone(); onClose() },
    onError: (err) => setErreur(erreurMessage(err)),
  })

  return (
    <Modal title="Marquer retiree" onClose={onClose}>
      <label className="block text-sm text-slate-600 mb-1">Nom de la personne</label>
      <input
        className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3"
        value={nom}
        onChange={(e) => setNom(e.target.value)}
      />
      <label className="block text-sm text-slate-600 mb-1">Telephone</label>
      <input
        className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3"
        value={telephone}
        onChange={(e) => setTelephone(e.target.value)}
      />
      {erreur && <p className="text-red-600 text-sm mb-3">{erreur}</p>}
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900">Annuler</button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
        >
          Confirmer le retrait
        </button>
      </div>
    </Modal>
  )
}

function AnnulerFactureModal({ facture, onClose, onSuccess }) {
  const [erreur, setErreur] = useState(null)
  const mutation = useMutation({
    mutationFn: () => apiClient.post(`/factures/${facture.id}/annuler/`),
    onSuccess: () => { onSuccess(); onClose() },
    onError: (err) => setErreur(erreurMessage(err)),
  })

  return (
    <Modal title={`Annuler la facture ${facture.numero_facture}`} onClose={onClose}>
      <p className="text-sm text-slate-600 mb-3">
        Cette action est irreversible. La facture passera au statut "Annulee" et les motos
        vendues dessus repasseront en stock disponible.
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

function AnnulerVersementModal({ versement, onClose, onSuccess }) {
  const [erreur, setErreur] = useState(null)
  const mutation = useMutation({
    mutationFn: () => apiClient.post(`/versements/${versement.id}/annuler/`),
    onSuccess: () => { onSuccess(); onClose() },
    onError: (err) => setErreur(erreurMessage(err)),
  })

  return (
    <Modal title="Annuler ce versement" onClose={onClose}>
      <p className="text-sm text-slate-600 mb-3">
        Montant : <strong>{formatMontant(versement.montant)} F</strong> — cette action est irreversible.
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

function UploadFichier({ resource, id, onDone, label = 'Uploader le scan' }) {
  const [file, setFile] = useState(null)
  const [erreur, setErreur] = useState(null)
  const mutation = useMutation({
    mutationFn: () => {
      const formData = new FormData()
      formData.append('fichier', file)
      return apiClient.patch(`/${resource}/${id}/`, formData)
    },
    onSuccess: () => { onDone(); setFile(null); setErreur(null) },
    onError: (err) => setErreur(erreurMessage(err)),
  })

  return (
    <div>
      <div className="flex items-center gap-2">
        <input
          type="file"
          onChange={(e) => { setFile(e.target.files[0]); setErreur(null) }}
          className="text-xs"
        />
        <button
          type="button"
          disabled={!file || mutation.isPending}
          onClick={() => mutation.mutate()}
          className="text-xs text-slate-600 hover:text-slate-900 underline disabled:opacity-50 disabled:no-underline"
        >
          {label}
        </button>
      </div>
      {erreur && <p className="text-red-600 text-xs mt-1">{erreur}</p>}
    </div>
  )
}

export default function FactureDetailPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const canAnnuler = user?.role === 'admin' || user?.role === 'gerant'

  const { data: facture, isLoading } = useQuery({
    queryKey: ['factures', id],
    queryFn: async () => (await apiClient.get(`/factures/${id}/`)).data,
  })

  const { data: versements } = useResourceList('versements', { facture: id })
  const { data: cartesGrises } = useResourceList('cartes-grises', { facture: id })
  const { data: quittances } = useResourceList('quittances', { facture: id })

  const { create: creerVersement } = useResourceMutations('versements')
  const { create: creerCarteGrise, update: modifierCarteGrise } = useResourceMutations('cartes-grises')
  const { create: creerQuittance } = useResourceMutations('quittances')

  const [modal, setModal] = useState(null)
  const [retraitTarget, setRetraitTarget] = useState(null)
  const [erreurRecue, setErreurRecue] = useState(null)
  const [annulerFacture, setAnnulerFacture] = useState(false)
  const [annulerVersementTarget, setAnnulerVersementTarget] = useState(null)

  const invalider = () => {
    queryClient.invalidateQueries({ queryKey: ['factures', id] })
    queryClient.invalidateQueries({ queryKey: ['versements'] })
    queryClient.invalidateQueries({ queryKey: ['cartes-grises'] })
    queryClient.invalidateQueries({ queryKey: ['quittances'] })
  }

  const marquerRecue = async (carteGriseId) => {
    setErreurRecue(null)
    try {
      await apiClient.post(`/cartes-grises/${carteGriseId}/recevoir/`)
      invalider()
    } catch (err) {
      setErreurRecue(erreurMessage(err))
    }
  }

  if (isLoading || !facture) {
    return <p className="text-slate-500 text-sm">Chargement...</p>
  }

  const carteGrise = cartesGrises?.[0]

  return (
    <div className="max-w-4xl space-y-8">
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-800">{facture.numero_facture}</h1>
            <span className={`text-xs px-2 py-0.5 rounded-full ${facture.statut === 'validee' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {facture.statut === 'validee' ? 'Validee' : 'Annulee'}
            </span>
          </div>
          <p className="text-slate-500 text-sm">
            {facture.client_nom} — {facture.agence_nom} — {formatDateTime(facture.date_facture)}
          </p>
          {facture.remarque && <p className="text-slate-600 text-sm mt-1">{facture.remarque}</p>}
          {facture.statut === 'annulee' && (
            <p className="text-red-600 text-xs mt-1">
              Annulee le {formatDateTime(facture.date_annulation)} par {facture.annule_par_username || '-'}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => ouvrirPdf(`/factures/${id}/pdf/`)} className="px-3 py-2 text-sm border border-slate-300 rounded">
            Facture PDF
          </button>
          <button onClick={() => ouvrirPdf(`/factures/${id}/bordereau/`)} className="px-3 py-2 text-sm border border-slate-300 rounded">
            Bordereau PDF
          </button>
          {canAnnuler && facture.statut === 'validee' && (
            <button
              onClick={() => setAnnulerFacture(true)}
              className="px-3 py-2 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
            >
              Annuler la facture
            </button>
          )}
        </div>
      </div>

      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-2">Lignes</h2>
        <DataTable
          rows={facture.lignes}
          columns={[
            { key: 'moto_numero_serie', label: 'Moto', render: (r) => r.moto_numero_serie || r.modele_casque_nom || r.designation },
            { key: 'moto_type_label', label: 'Type', render: (r) => r.moto_type_label || '-' },
            { key: 'moto_couleur_nom', label: 'Couleur', render: (r) => r.moto_couleur_nom || '-' },
            { key: 'quantite', label: 'Qte' },
            { key: 'prix_unitaire', label: 'PU', render: (r) => `${formatMontant(r.prix_unitaire)} F` },
            { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
            {
              key: 'arrivage_fichier_cmc',
              label: 'CMC',
              render: (r) => (r.arrivage_fichier_cmc
                ? <a href={r.arrivage_fichier_cmc} target="_blank" rel="noreferrer" className="text-slate-600 hover:text-slate-900 underline">Voir le CMC</a>
                : '-'),
            },
          ]}
        />
        <div className="text-right mt-2 space-y-1">
          <p className="text-slate-600 text-sm">Total : {formatMontant(facture.total)} F</p>
          <p className="text-slate-600 text-sm">Total verse : {formatMontant(facture.total_verse)} F</p>
          <p className="font-semibold text-slate-800">Reste a payer : {formatMontant(facture.solde)} F</p>
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-sm font-medium text-slate-700">Versements</h2>
          {facture.statut === 'validee' && Number(facture.solde) > 0 ? (
            <button onClick={() => setModal('versement')} className="text-sm text-slate-600 hover:text-slate-900 underline">
              + Ajouter un versement
            </button>
          ) : facture.statut === 'validee' ? (
            <span className="text-sm text-green-700">Facture soldee</span>
          ) : null}
        </div>
        <DataTable
          rows={versements}
          emptyMessage="Aucun versement enregistre."
          columns={[
            { key: 'date_versement', label: 'Date', render: (r) => formatDateTime(r.date_versement) },
            { key: 'montant', label: 'Montant', render: (r) => `${formatMontant(r.montant)} F` },
            { key: 'mode_paiement', label: 'Mode' },
            { key: 'reference_transaction', label: 'Reference' },
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
              <button onClick={() => ouvrirPdf(`/versements/${row.id}/recu/`)} className="text-slate-600 hover:text-slate-900 text-sm">
                Recu PDF
              </button>
              {canAnnuler && row.statut === 'valide' && (
                <button onClick={() => setAnnulerVersementTarget(row)} className="text-red-600 hover:text-red-800 text-sm">
                  Annuler
                </button>
              )}
            </>
          )}
        />
      </div>

      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-2">Carte grise</h2>
        {carteGrise ? (
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-base font-semibold text-slate-800">
                  Dossier {carteGrise.numero_dossier || '-'}
                </span>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                  carteGrise.retiree ? 'bg-green-100 text-green-700'
                    : carteGrise.recue ? 'bg-blue-100 text-blue-700'
                      : 'bg-amber-100 text-amber-700'
                }`}>
                  {carteGrise.retiree ? 'Retiree' : carteGrise.recue ? 'Recue' : 'En attente'}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setModal('carte_grise_edit')}
                  className="px-3 py-1.5 text-xs border border-slate-300 rounded hover:bg-white"
                >
                  Modifier
                </button>
                {!carteGrise.recue && (
                  <button
                    onClick={() => marquerRecue(carteGrise.id)}
                    className="px-3 py-1.5 text-xs border border-slate-300 rounded hover:bg-white"
                  >
                    Marquer recue
                  </button>
                )}
                {!carteGrise.retiree && (
                  <button
                    onClick={() => setRetraitTarget({ resource: 'cartes-grises', item: carteGrise })}
                    className="px-3 py-1.5 text-xs bg-slate-800 text-white rounded hover:bg-slate-700"
                  >
                    Marquer retiree
                  </button>
                )}
              </div>
            </div>

            {carteGrise.retiree && (
              <div className="mt-3 text-xs text-slate-600 bg-white border border-slate-200 rounded px-3 py-2">
                Retiree le <span className="font-medium text-slate-800">{formatDateTime(carteGrise.date_retrait)}</span>
                {' '}par <span className="font-medium text-slate-800">{carteGrise.retirer_nom || '-'}</span>
                {' '}({carteGrise.retirer_telephone || '-'})
              </div>
            )}

            {carteGrise.commentaire && (
              <p className="mt-3 text-xs text-slate-500 italic">{carteGrise.commentaire}</p>
            )}

            <div className="mt-4 pt-3 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
              {carteGrise.fichier ? (
                <a
                  href={carteGrise.fichier}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-slate-600 hover:text-slate-900 underline"
                >
                  Voir le fichier scanne
                </a>
              ) : (
                <span className="text-xs text-slate-400">Aucun fichier scanne</span>
              )}
              <UploadFichier
                resource="cartes-grises"
                id={carteGrise.id}
                label={carteGrise.fichier ? 'Remplacer le scan' : 'Uploader le scan'}
                onDone={invalider}
              />
            </div>
            {erreurRecue && <p className="text-red-600 text-xs mt-2">{erreurRecue}</p>}
          </div>
        ) : (
          <button onClick={() => setModal('carte_grise')} className="text-sm text-slate-600 hover:text-slate-900 underline">
            + Creer le dossier carte grise
          </button>
        )}
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-sm font-medium text-slate-700">Quittances / CMC</h2>
          <button onClick={() => setModal('quittance')} className="text-sm text-slate-600 hover:text-slate-900 underline">
            + Ajouter
          </button>
        </div>
        <DataTable
          rows={quittances}
          emptyMessage="Aucune quittance enregistree."
          columns={[
            { key: 'type_document', label: 'Type' },
            { key: 'numero', label: 'Numero' },
            {
              key: 'fichier',
              label: 'Fichier',
              render: (r) => (r.fichier
                ? <a href={r.fichier} target="_blank" rel="noreferrer" className="underline">Voir</a>
                : <UploadFichier resource="quittances" id={r.id} onDone={invalider} />),
            },
            { key: 'retiree', label: 'Statut', render: (r) => (r.retiree ? `Retiree (${r.retirer_nom || '-'})` : 'En attente') },
          ]}
          actions={(row) => !row.retiree && (
            <button onClick={() => setRetraitTarget({ resource: 'quittances', item: row })} className="text-slate-600 hover:text-slate-900 text-sm">
              Marquer retiree
            </button>
          )}
        />
      </div>

      {modal === 'versement' && (
        <FormModal
          title="Nouveau versement"
          fields={[
            { name: 'montant', label: 'Montant', type: 'number', step: '0.01', required: true },
            { name: 'mode_paiement', label: 'Mode de paiement', type: 'select', required: true, options: MODES_PAIEMENT },
            { name: 'reference_transaction', label: 'Reference (optionnel)' },
          ]}
          onSubmit={async (values) => {
            await creerVersement.mutateAsync({ ...values, facture: id })
            invalider()
          }}
          onClose={() => setModal(null)}
        />
      )}

      {modal === 'carte_grise' && (
        <FormModal
          title="Dossier carte grise"
          fields={[{ name: 'numero_dossier', label: 'Numero de dossier' }]}
          onSubmit={async (values) => {
            await creerCarteGrise.mutateAsync({ ...values, facture: id })
            invalider()
          }}
          onClose={() => setModal(null)}
        />
      )}

      {modal === 'carte_grise_edit' && (
        <FormModal
          title="Modifier le dossier carte grise"
          initialValues={carteGrise}
          fields={[
            { name: 'numero_dossier', label: 'Numero de dossier' },
            { name: 'commentaire', label: 'Commentaire', type: 'textarea' },
          ]}
          onSubmit={async (values) => {
            await modifierCarteGrise.mutateAsync({ id: carteGrise.id, payload: values })
            invalider()
          }}
          onClose={() => setModal(null)}
        />
      )}

      {modal === 'quittance' && (
        <FormModal
          title="Nouvelle quittance / CMC"
          fields={[
            { name: 'type_document', label: 'Type', type: 'select', required: true, options: [
              { value: 'quittance', label: 'Quittance' },
              { value: 'cmc', label: 'CMC' },
            ] },
            { name: 'numero', label: 'Numero' },
          ]}
          onSubmit={async (values) => {
            await creerQuittance.mutateAsync({ ...values, facture: id })
            invalider()
          }}
          onClose={() => setModal(null)}
        />
      )}

      {retraitTarget && (
        <RetraitModal
          resource={retraitTarget.resource}
          item={retraitTarget.item}
          onClose={() => setRetraitTarget(null)}
          onDone={invalider}
        />
      )}

      {annulerFacture && (
        <AnnulerFactureModal
          facture={facture}
          onClose={() => setAnnulerFacture(false)}
          onSuccess={invalider}
        />
      )}

      {annulerVersementTarget && (
        <AnnulerVersementModal
          versement={annulerVersementTarget}
          onClose={() => setAnnulerVersementTarget(null)}
          onSuccess={invalider}
        />
      )}
    </div>
  )
}

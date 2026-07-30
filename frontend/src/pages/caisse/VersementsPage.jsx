import { Link } from 'react-router-dom'
import { useResourceList } from '../../hooks/useResource'
import DataTable from '../../components/DataTable'
import { formatDateTime, formatMontant } from '../../lib/format'
import { ouvrirPdf } from '../../lib/pdf'

export default function VersementsPage() {
  const { data: versements, isLoading } = useResourceList('versements')

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
        ]}
        actions={(row) => (
          <>
            <Link to={`/factures/${row.facture}`} className="text-slate-600 hover:text-slate-900 text-sm">
              Voir la facture
            </Link>
            <button onClick={() => ouvrirPdf(`/versements/${row.id}/recu/`)} className="text-slate-600 hover:text-slate-900 text-sm">
              Recu PDF
            </button>
          </>
        )}
      />
    </div>
  )
}

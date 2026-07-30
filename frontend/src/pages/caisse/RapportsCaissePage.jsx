import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import DataTable from '../../components/DataTable'
import { formatMontant } from '../../lib/format'

export default function RapportsCaissePage() {
  const { data: rapportVentes } = useQuery({
    queryKey: ['caisse', 'rapport-ventes'],
    queryFn: async () => (await apiClient.get('/caisse/rapport-ventes/')).data,
  })
  const { data: rapportDepenses } = useQuery({
    queryKey: ['caisse', 'rapport-depenses'],
    queryFn: async () => (await apiClient.get('/caisse/rapport-depenses/')).data,
  })
  const { data: debiteurs, isLoading: loadingDebiteurs } = useQuery({
    queryKey: ['caisse', 'clients-debiteurs'],
    queryFn: async () => (await apiClient.get('/caisse/clients-debiteurs/')).data,
  })
  const { data: ventesParClient, isLoading: loadingVentesClient } = useQuery({
    queryKey: ['caisse', 'rapport-ventes-clients'],
    queryFn: async () => (await apiClient.get('/caisse/rapport-ventes-clients/')).data,
  })

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-slate-800">Rapports</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border border-slate-200 rounded-lg p-4">
          <p className="text-sm text-slate-500">Ventes</p>
          <p className="text-2xl font-semibold text-slate-800">{formatMontant(rapportVentes?.total_ventes)} F</p>
          <p className="text-sm text-slate-500">{rapportVentes?.nb_factures ?? 0} facture(s)</p>
        </div>
        <div className="border border-slate-200 rounded-lg p-4">
          <p className="text-sm text-slate-500">Depenses</p>
          <p className="text-2xl font-semibold text-slate-800">{formatMontant(rapportDepenses?.total_depenses)} F</p>
        </div>
      </div>

      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-2">Depenses par categorie</h2>
        <DataTable
          rows={rapportDepenses?.par_categorie}
          columns={[
            { key: 'categorie', label: 'Categorie' },
            { key: 'total', label: 'Total', render: (r) => `${formatMontant(r.total)} F` },
          ]}
        />
      </div>

      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-2">Clients debiteurs</h2>
        <DataTable
          isLoading={loadingDebiteurs}
          rows={debiteurs}
          emptyMessage="Aucun client debiteur."
          columns={[
            { key: 'client_nom', label: 'Client' },
            { key: 'agence', label: 'Agence' },
            { key: 'total_facture', label: 'Total facture', render: (r) => `${formatMontant(r.total_facture)} F` },
            { key: 'total_verse', label: 'Total verse', render: (r) => `${formatMontant(r.total_verse)} F` },
            { key: 'solde', label: 'Solde du', render: (r) => `${formatMontant(r.solde)} F` },
          ]}
        />
      </div>

      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-2">Ventes par client</h2>
        <DataTable
          isLoading={loadingVentesClient}
          rows={ventesParClient}
          columns={[
            { key: 'client_nom', label: 'Client' },
            { key: 'total', label: 'Total', render: (r) => `${formatMontant(r.total)} F` },
          ]}
        />
      </div>
    </div>
  )
}

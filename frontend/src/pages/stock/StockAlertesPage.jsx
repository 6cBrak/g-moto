import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import DataTable from '../../components/DataTable'

export default function StockAlertesPage() {
  const { data: vueEnsemble, isLoading: loadingVue } = useQuery({
    queryKey: ['stock', 'vue-ensemble'],
    queryFn: async () => (await apiClient.get('/stock/vue-ensemble/')).data,
  })
  const { data: alertes, isLoading: loadingAlertes } = useQuery({
    queryKey: ['stock', 'alertes'],
    queryFn: async () => (await apiClient.get('/stock/alertes/')).data,
  })

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-800 mb-4">Vue d'ensemble du stock</h1>
        {!loadingVue && vueEnsemble && (
          <p className="text-slate-600 mb-4">
            Total en stock : <span className="font-semibold">{vueEnsemble.total_en_stock}</span> moto(s)
          </p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-sm font-medium text-slate-600 mb-2">Par agence</h2>
            <DataTable
              isLoading={loadingVue}
              rows={vueEnsemble?.par_agence}
              columns={[
                { key: 'agence__nom', label: 'Agence' },
                { key: 'quantite', label: 'Quantite' },
              ]}
            />
          </div>
          <div>
            <h2 className="text-sm font-medium text-slate-600 mb-2">Par type de moto</h2>
            <DataTable
              isLoading={loadingVue}
              rows={vueEnsemble?.par_type}
              columns={[
                { key: 'type_moto__marque__nom', label: 'Marque' },
                { key: 'type_moto__nom', label: 'Modele' },
                { key: 'quantite', label: 'Quantite' },
              ]}
            />
          </div>
        </div>
      </div>

      <div>
        <h1 className="text-xl font-semibold text-slate-800 mb-4">Alertes de stock bas</h1>
        <DataTable
          isLoading={loadingAlertes}
          rows={alertes}
          emptyMessage="Aucune alerte, le stock est suffisant partout."
          columns={[
            { key: 'agence', label: 'Agence' },
            { key: 'type_moto', label: 'Type de moto' },
            { key: 'quantite_stock', label: 'Stock actuel' },
            { key: 'seuil_alerte', label: 'Seuil' },
          ]}
        />
      </div>
    </div>
  )
}

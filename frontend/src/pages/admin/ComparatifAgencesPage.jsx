import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../api/client'
import DataTable from '../../components/DataTable'
import { formatMontant } from '../../lib/format'

export default function ComparatifAgencesPage() {
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'comparatif-agences', dateDebut, dateFin],
    queryFn: async () => (await apiClient.get('/dashboard/comparatif-agences/', {
      params: { date_debut: dateDebut || undefined, date_fin: dateFin || undefined },
    })).data,
  })

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Comparatif inter-agences</h1>

      <div className="flex gap-3 mb-4">
        <input type="date" value={dateDebut} onChange={(e) => setDateDebut(e.target.value)} className="border border-slate-300 rounded px-2 py-1 text-sm" />
        <input type="date" value={dateFin} onChange={(e) => setDateFin(e.target.value)} className="border border-slate-300 rounded px-2 py-1 text-sm" />
      </div>

      <DataTable
        isLoading={isLoading}
        rows={data}
        columns={[
          { key: 'agence', label: 'Agence' },
          { key: 'nb_factures', label: 'Nb factures' },
          { key: 'total_ventes', label: 'Ventes', render: (r) => `${formatMontant(r.total_ventes)} F` },
          { key: 'total_depenses', label: 'Depenses', render: (r) => `${formatMontant(r.total_depenses)} F` },
          { key: 'tresorerie', label: 'Tresorerie', render: (r) => `${formatMontant(r.tresorerie)} F` },
        ]}
      />
    </div>
  )
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import { useAuthStore } from '../store/authStore'
import { useUiStore } from '../store/uiStore'
import DataTable from '../components/DataTable'
import { formatDate, formatMontant } from '../lib/format'

function premierJourMoisEnCours() {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10)
}

function formatPeriode(periode, granularite) {
  if (granularite === 'jour') return formatDate(periode)
  const d = new Date(periode)
  return d.toLocaleDateString('fr-FR', { year: 'numeric', month: 'long' })
}

const TONES = {
  default: 'text-slate-800',
  warning: 'text-amber-600',
  critical: 'text-red-600',
}

function KpiCard({ to, label, value, sub, tone = 'default' }) {
  return (
    <Link
      to={to}
      className="block bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:border-slate-400 hover:shadow-md transition"
    >
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`text-2xl font-semibold ${TONES[tone]}`}>{value}</p>
      {sub && <p className="text-sm text-slate-500">{sub}</p>}
    </Link>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <h2 className="text-sm font-medium text-slate-700 mb-3">{title}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{children}</div>
    </div>
  )
}

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)
  const agenceFiltre = useUiStore((state) => state.agenceFiltre)

  const params = agenceFiltre ? { agence: agenceFiltre } : {}

  const { data: kpis, isLoading: loadingKpis } = useQuery({
    queryKey: ['dashboard', 'kpis', agenceFiltre],
    queryFn: async () => (await apiClient.get('/dashboard/kpis/', { params })).data,
  })
  const [granularite, setGranularite] = useState('mois')
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')

  const changerGranularite = (g) => {
    setGranularite(g)
    setDateDebut(g === 'jour' ? premierJourMoisEnCours() : '')
    setDateFin('')
  }

  const { data: comparatif, isLoading: loadingComparatif } = useQuery({
    queryKey: ['dashboard', 'comparatif-periode', agenceFiltre, granularite, dateDebut, dateFin],
    queryFn: async () => (await apiClient.get('/dashboard/comparatif-periode/', {
      params: { ...params, granularite, date_debut: dateDebut || undefined, date_fin: dateFin || undefined },
    })).data,
  })

  const v = (val) => (loadingKpis ? '...' : val)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Tableau de bord</h1>
        <p className="text-slate-500 text-sm mt-1">
          Connecte en tant que <strong>{user?.username}</strong> ({user?.role})
          {user?.agence_nom && ` — ${user.agence_nom}`}
        </p>
      </div>

      <Section title="Ventes">
        <KpiCard
          to="/factures"
          label="Ventes du jour"
          value={v(`${formatMontant(kpis?.ventes_du_jour?.total)} F`)}
          sub={`${kpis?.ventes_du_jour?.nb_factures ?? 0} facture(s)`}
        />
        <KpiCard
          to="/factures"
          label="Ventes du mois"
          value={v(`${formatMontant(kpis?.ventes_du_mois?.total)} F`)}
          sub={`${kpis?.ventes_du_mois?.nb_factures ?? 0} facture(s)`}
        />
        <KpiCard
          to="/factures"
          label="Panier moyen (mois)"
          value={v(`${formatMontant(kpis?.panier_moyen)} F`)}
          sub="par facture ce mois-ci"
        />
      </Section>

      <Section title="Finances">
        <KpiCard
          to="/caisse/session"
          label="Tresorerie"
          value={v(`${formatMontant(kpis?.tresorerie)} F`)}
          sub="argent disponible en caisse"
        />
        <KpiCard
          to="/caisse/versements"
          label="Total encaissements"
          value={v(`${formatMontant(kpis?.total_encaissements)} F`)}
          sub="depuis le debut"
        />
        <KpiCard
          to="/clients"
          label="Reste a payer (clients)"
          value={v(`${formatMontant(kpis?.reste_a_payer?.total)} F`)}
          sub={`${kpis?.reste_a_payer?.nb_clients ?? 0} client(s) debiteur(s)`}
        />
        <KpiCard
          to="/caisse/rapports"
          label="Du aux fournisseurs (depot)"
          value={v(`${formatMontant(kpis?.du_fournisseurs?.total)} F`)}
          sub={`${kpis?.du_fournisseurs?.nb_fournisseurs ?? 0} fournisseur(s)`}
          tone={Number(kpis?.du_fournisseurs?.total) > 0 ? 'warning' : 'default'}
        />
        <KpiCard
          to="/depenses"
          label="Depenses du mois"
          value={v(`${formatMontant(kpis?.depenses_du_mois)} F`)}
        />
        <KpiCard
          to="/caisse/sorties"
          label="Sorties de caisse (mois)"
          value={v(`${formatMontant(kpis?.sorties_du_mois)} F`)}
        />
        <KpiCard
          to="/stock/marge-arrivages"
          label="Marge du mois"
          value={v(`${formatMontant(kpis?.marge_du_mois)} F`)}
          tone={Number(kpis?.marge_du_mois) < 0 ? 'critical' : 'default'}
        />
        <KpiCard
          to="/clients"
          label="Taux de recouvrement"
          value={v(kpis?.taux_recouvrement != null ? `${kpis.taux_recouvrement}%` : '-')}
          sub="verse / facture, global"
        />
      </Section>

      <Section title="Stock">
        <KpiCard
          to="/stock/motos"
          label="Stock total"
          value={v(kpis?.stock_total ?? 0)}
          sub={`Valeur : ${formatMontant(kpis?.valeur_stock)} F`}
        />
        <KpiCard
          to="/stock/alertes"
          label="Stock critique"
          value={v(kpis?.stock_critique ?? 0)}
          sub="type(s) de moto sous le seuil"
          tone={Number(kpis?.stock_critique) > 0 ? 'warning' : 'default'}
        />
        <KpiCard
          to="/stock/motos"
          label="Stock dormant"
          value={v(kpis?.stock_dormant ?? 0)}
          sub="en stock depuis + de 60 jours"
          tone={Number(kpis?.stock_dormant) > 0 ? 'warning' : 'default'}
        />
      </Section>

      <Section title="Apres-vente">
        <KpiCard
          to="/apresvente/garanties"
          label="Garanties expirant bientot"
          value={v(kpis?.garanties_expirant_bientot ?? 0)}
          sub="dans les 30 prochains jours"
        />
        <KpiCard
          to="/apresvente/entretiens"
          label="Entretiens a venir"
          value={v(kpis?.entretiens_a_venir ?? 0)}
          sub="dans les 30 prochains jours"
        />
      </Section>

      <Section title="Cartes grises">
        <KpiCard
          to="/clients"
          label="Plaques produites"
          value={v(kpis?.plaques_produites ?? 0)}
          sub="recues de l'administration"
        />
        <KpiCard
          to="/clients"
          label="Plaques retirees"
          value={v(kpis?.plaques_retirees ?? 0)}
        />
        <KpiCard
          to="/clients"
          label="Reste a retirer"
          value={v(kpis?.plaques_a_retirer ?? 0)}
          sub="recues, pas encore retirees"
          tone={Number(kpis?.plaques_a_retirer) > 0 ? 'warning' : 'default'}
        />
      </Section>

      <div>
        <div className="flex flex-wrap items-end justify-between gap-3 mb-3">
          <h2 className="text-sm font-medium text-slate-700">Comparatif par periode</h2>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex border border-slate-300 rounded overflow-hidden">
              <button
                type="button"
                onClick={() => changerGranularite('jour')}
                className={`px-3 py-1 text-sm ${granularite === 'jour' ? 'bg-slate-800 text-white' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              >
                Par jour
              </button>
              <button
                type="button"
                onClick={() => changerGranularite('mois')}
                className={`px-3 py-1 text-sm ${granularite === 'mois' ? 'bg-slate-800 text-white' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              >
                Par mois
              </button>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Du</label>
              <input
                type="date"
                value={dateDebut}
                onChange={(e) => setDateDebut(e.target.value)}
                className="border border-slate-300 rounded px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Au</label>
              <input
                type="date"
                value={dateFin}
                onChange={(e) => setDateFin(e.target.value)}
                className="border border-slate-300 rounded px-2 py-1 text-sm"
              />
            </div>
          </div>
        </div>
        {granularite === 'jour' && (
          <p className="text-xs text-slate-500 mb-2">Par defaut, limite au mois en cours — ajustez les dates si besoin.</p>
        )}
        <DataTable
          isLoading={loadingComparatif}
          rows={comparatif}
          columns={[
            { key: 'periode', label: 'Periode', render: (r) => formatPeriode(r.periode, granularite) },
            { key: 'total_ventes', label: 'Ventes', render: (r) => `${formatMontant(r.total_ventes)} F` },
            { key: 'total_depenses', label: 'Depenses', render: (r) => `${formatMontant(r.total_depenses)} F` },
          ]}
        />
      </div>
    </div>
  )
}

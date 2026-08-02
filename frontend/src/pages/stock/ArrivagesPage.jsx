import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import CrudPage from '../../components/CrudPage'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import { useResourceList, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'
import { formatDate, formatMontant } from '../../lib/format'
import { ouvrirPdf } from '../../lib/pdf'

const STATUTS = {
  en_stock: 'En stock',
  vendue: 'Vendue',
  transferee: 'Transferee',
  en_depot: 'En depot',
}

function ArrivageMotosPanel({ arrivage, onClose }) {
  const queryClient = useQueryClient()
  const { data: motos, isLoading } = useResourceList('motos', { arrivage: arrivage.id })
  const { data: typesMoto } = useResourceList('types-moto')
  const { data: couleurs } = useResourceList('couleurs')
  const { create, update, remove } = useResourceMutations('motos')

  const [form, setForm] = useState({ numero_serie: '', type_moto: '', couleur: '', prix_achat: '', immatriculation: '' })
  const [error, setError] = useState(null)
  const [editTarget, setEditTarget] = useState(null)

  // nb_motos et montant_facture (calcule) affiches sur la ligne parente doivent se rafraichir aussi.
  const invaliderArrivages = () => queryClient.invalidateQueries({ queryKey: ['arrivages'] })

  const handleDelete = async (moto) => {
    if (window.confirm(`Supprimer la moto ${moto.numero_serie} ?`)) {
      try {
        await remove.mutateAsync(moto.id)
        invaliderArrivages()
      } catch (err) {
        setError(err?.response?.data?.detail ?? 'Une erreur est survenue.')
      }
    }
  }

  const handleTypeChange = (value) => {
    const type = (typesMoto ?? []).find((t) => String(t.id) === String(value))
    setForm((prev) => ({ ...prev, type_moto: value, numero_serie: prev.numero_serie || type?.code || '' }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    try {
      await create.mutateAsync({
        ...form,
        arrivage: arrivage.id,
        agence: arrivage.agence,
      })
      invaliderArrivages()
      const type = (typesMoto ?? []).find((t) => String(t.id) === String(form.type_moto))
      setForm((prev) => ({ ...prev, numero_serie: type?.code || '', immatriculation: '' }))
    } catch (err) {
      const data = err?.response?.data
      const message = data
        ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' — ')
        : 'Une erreur est survenue.'
      setError(message)
    }
  }

  return (
    <div className="mt-6 border-t border-slate-200 pt-4">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-slate-800">
          Motos de l'arrivage {arrivage.numero_bon}
        </h2>
        <div className="flex items-center gap-3">
          <button onClick={() => ouvrirPdf(`/arrivages/${arrivage.id}/pdf/`)} className="text-sm text-slate-600 hover:text-slate-900 underline">
            Imprimer la liste
          </button>
          <button onClick={onClose} className="text-sm text-slate-500 hover:text-slate-800">Fermer</button>
        </div>
      </div>

      <DataTable
        isLoading={isLoading}
        rows={motos}
        emptyMessage="Aucune moto pour cet arrivage."
        columns={[
          { key: 'numero_serie', label: 'N° serie' },
          { key: 'type_moto_label', label: 'Type' },
          { key: 'couleur_nom', label: 'Couleur' },
          { key: 'immatriculation', label: 'Immatriculation', render: (r) => r.immatriculation || '-' },
          { key: 'statut', label: 'Statut', render: (r) => STATUTS[r.statut] ?? r.statut },
        ]}
        actions={(row) => row.statut !== 'vendue' && (
          <>
            <button onClick={() => setEditTarget(row)} className="text-slate-600 hover:text-slate-900 text-sm">
              Modifier
            </button>
            <button onClick={() => handleDelete(row)} className="text-red-600 hover:text-red-800 text-sm">
              Supprimer
            </button>
          </>
        )}
      />

      <form onSubmit={handleSubmit} className="mt-4 grid grid-cols-2 sm:flex sm:flex-wrap items-end gap-3">
        <div className="col-span-2 sm:col-span-1">
          <label className="block text-sm text-slate-600 mb-1">Type de moto</label>
          <select
            className="w-full sm:w-auto border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.type_moto}
            required
            onChange={(e) => handleTypeChange(e.target.value)}
          >
            <option value="">-- choisir --</option>
            {(typesMoto ?? []).map((t) => (
              <option key={t.id} value={t.id}>{t.marque_nom} {t.nom}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Couleur</label>
          <select
            className="w-full sm:w-auto border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.couleur}
            required
            onChange={(e) => setForm((prev) => ({ ...prev, couleur: e.target.value }))}
          >
            <option value="">-- choisir --</option>
            {(couleurs ?? []).map((c) => (
              <option key={c.id} value={c.id}>{c.nom}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Numero de serie</label>
          <input
            className="w-full sm:w-auto border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.numero_serie}
            required
            onChange={(e) => setForm((prev) => ({ ...prev, numero_serie: e.target.value }))}
          />
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Prix achat</label>
          <input
            type="number"
            step="0.01"
            className="w-full sm:w-32 border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.prix_achat}
            onChange={(e) => setForm((prev) => ({ ...prev, prix_achat: e.target.value }))}
          />
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Immatriculation</label>
          <input
            className="w-full sm:w-auto border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.immatriculation}
            onChange={(e) => setForm((prev) => ({ ...prev, immatriculation: e.target.value }))}
          />
        </div>
        <button
          type="submit"
          disabled={create.isPending}
          className="col-span-2 sm:col-span-1 px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
        >
          + Ajouter la moto
        </button>
      </form>
      {error && <p className="text-red-600 text-sm mt-2">{error}</p>}

      {editTarget && (
        <FormModal
          title={`Modifier ${editTarget.numero_serie}`}
          initialValues={editTarget}
          fields={[
            { name: 'numero_serie', label: 'Numero de serie', required: true },
            {
              name: 'type_moto',
              label: 'Type de moto',
              type: 'select',
              required: true,
              options: (typesMoto ?? []).map((t) => ({ value: t.id, label: `${t.marque_nom} ${t.nom}` })),
            },
            {
              name: 'couleur',
              label: 'Couleur',
              type: 'select',
              required: true,
              options: (couleurs ?? []).map((c) => ({ value: c.id, label: c.nom })),
            },
            { name: 'prix_achat', label: 'Prix achat', type: 'number', step: '0.01' },
            { name: 'immatriculation', label: 'Immatriculation' },
          ]}
          onSubmit={async (values) => {
            await update.mutateAsync({ id: editTarget.id, payload: values })
            invaliderArrivages()
          }}
          onClose={() => setEditTarget(null)}
        />
      )}
    </div>
  )
}

export default function ArrivagesPage() {
  const user = useAuthStore((state) => state.user)
  const { data: fournisseurs } = useResourceList('fournisseurs')
  const { data: agences } = useResourceList('agences')
  const [selected, setSelected] = useState(null)

  const fields = [
    {
      name: 'fournisseur',
      label: 'Fournisseur',
      type: 'select',
      required: true,
      options: (fournisseurs ?? []).map((f) => ({ value: f.id, label: f.nom })),
    },
    { name: 'numero_bon', label: 'Numero de bon', required: true },
    { name: 'date_arrivage', label: 'Date arrivage', type: 'date', required: true },
    { name: 'numero_facture', label: 'Numero facture' },
    { name: 'fichier_cmc', label: 'Fichier CMC scanne', type: 'file' },
    { name: 'commentaire', label: 'Commentaire', type: 'textarea' },
  ]

  if (user?.role === 'admin') {
    fields.unshift({
      name: 'agence',
      label: 'Agence',
      type: 'select',
      required: true,
      options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
    })
  }

  return (
    <div>
      <CrudPage
        resource="arrivages"
        title="Arrivages"
        canWrite
        onRowClick={(row) => setSelected(row)}
        selectedId={selected?.id}
        columns={[
          { key: 'numero_bon', label: 'N° bon' },
          { key: 'agence_nom', label: 'Agence' },
          { key: 'fournisseur_nom', label: 'Fournisseur' },
          { key: 'date_arrivage', label: 'Date', render: (r) => formatDate(r.date_arrivage) },
          { key: 'nb_motos', label: 'Nb motos' },
          { key: 'montant_facture', label: 'Montant facture (calcule)', render: (r) => `${formatMontant(r.montant_facture)} F` },
        ]}
        fields={fields}
      />

      {selected && <ArrivageMotosPanel arrivage={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

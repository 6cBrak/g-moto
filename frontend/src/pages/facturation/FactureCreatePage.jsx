import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useResourceList, useResourceMutations } from '../../hooks/useResource'
import { useAuthStore } from '../../store/authStore'

function ligneVide() {
  return {
    type: 'moto',
    type_moto: '',
    series: [''],
    modele_casque: '',
    designation: '',
    quantite: 1,
    prix_unitaire: '',
  }
}

export default function FactureCreatePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const { data: clients } = useResourceList('clients')
  const { data: motos } = useResourceList('motos', { page_size: 1000 })
  const { data: typesMoto } = useResourceList('types-moto')
  const { data: casques } = useResourceList('modeles-casque')
  const { data: agences } = useResourceList('agences', {}, { enabled: user?.role === 'admin' })
  const { create } = useResourceMutations('factures')

  const [clientId, setClientId] = useState(searchParams.get('client') ?? '')
  const [agenceId, setAgenceId] = useState('')
  const [remarque, setRemarque] = useState('')
  const [lignes, setLignes] = useState([ligneVide()])
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const estAdmin = user?.role === 'admin'
  const motosDisponibles = (motos ?? []).filter((m) => {
    const bonneAgence = !estAdmin || !agenceId || String(m.agence) === String(agenceId)
    if (m.statut === 'en_stock') return bonneAgence
    if (m.statut === 'en_depot') return bonneAgence && clientId && String(m.depot_client_id) === String(clientId)
    return false
  })
  const clientsDisponibles = (clients ?? []).filter((c) => (
    !estAdmin || !agenceId || String(c.agence) === String(agenceId)
  ))

  const majLigne = (index, champ, valeur) => {
    setLignes((prev) => prev.map((ligne, i) => (i === index ? { ...ligne, [champ]: valeur } : ligne)))
  }

  const majTypeMoto = (index, typeMotoId) => {
    setLignes((prev) => prev.map((ligne, i) => (
      i === index ? { ...ligne, type_moto: typeMotoId, series: Array(ligne.quantite).fill('') } : ligne
    )))
  }

  const majQuantite = (index, valeur) => {
    const quantite = Math.max(1, Number(valeur) || 1)
    setLignes((prev) => prev.map((ligne, i) => {
      if (i !== index) return ligne
      const series = [...ligne.series]
      while (series.length < quantite) series.push('')
      while (series.length > quantite) series.pop()
      return { ...ligne, quantite, series }
    }))
  }

  const majSerie = (index, slot, motoId) => {
    setLignes((prev) => prev.map((ligne, i) => {
      if (i !== index) return ligne
      const series = [...ligne.series]
      series[slot] = motoId
      return { ...ligne, series }
    }))
  }

  const ajouterLigne = () => setLignes((prev) => [...prev, ligneVide()])
  const supprimerLigne = (index) => setLignes((prev) => prev.filter((_, i) => i !== index))

  const motosExclues = (indexActuel, slotActuel) => {
    const set = new Set()
    lignes.forEach((ligne, i) => {
      if (ligne.type !== 'moto') return
      ligne.series.forEach((id, j) => {
        if (id && !(i === indexActuel && j === slotActuel)) set.add(String(id))
      })
    })
    return set
  }

  const total = lignes.reduce((acc, l) => acc + (Number(l.quantite) || 0) * (Number(l.prix_unitaire) || 0), 0)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)

    const blocMotoIncomplet = lignes.some((l) => l.type === 'moto' && (!l.type_moto || l.series.some((s) => !s)))
    if (blocMotoIncomplet) {
      setError('Choisissez un type de moto et un numero de serie pour chaque unite.')
      return
    }

    setSubmitting(true)
    try {
      const payloadLignes = lignes.flatMap((l) => {
        if (l.type === 'moto') {
          return l.series.map((motoId) => ({ moto: motoId, quantite: 1, prix_unitaire: l.prix_unitaire }))
        }
        const base = { quantite: Number(l.quantite) || 1, prix_unitaire: l.prix_unitaire }
        if (l.type === 'casque') return [{ ...base, modele_casque: l.modele_casque }]
        return [{ ...base, designation: l.designation }]
      })
      const payload = { client: clientId, remarque, lignes: payloadLignes }
      if (estAdmin) payload.agence = agenceId
      const response = await create.mutateAsync(payload)
      navigate(`/factures/${response.data.id}`)
    } catch (err) {
      const data = err?.response?.data
      setError(data ? JSON.stringify(data) : 'Une erreur est survenue.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-semibold text-slate-800 mb-4">Nouvelle facture</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {estAdmin && (
          <div>
            <label className="block text-sm text-slate-600 mb-1">Agence</label>
            <select
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
              value={agenceId}
              required
              onChange={(e) => setAgenceId(e.target.value)}
            >
              <option value="">-- choisir --</option>
              {(agences ?? []).map((a) => <option key={a.id} value={a.id}>{a.nom}</option>)}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm text-slate-600 mb-1">Client</label>
          <select
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            value={clientId}
            required
            onChange={(e) => setClientId(e.target.value)}
          >
            <option value="">-- choisir --</option>
            {clientsDisponibles.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}
          </select>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-sm font-medium text-slate-700">Lignes de facture</h2>
            <button type="button" onClick={ajouterLigne} className="text-sm text-slate-600 hover:text-slate-900 underline">
              + Ajouter une ligne
            </button>
          </div>

          <div className="space-y-3">
            {lignes.map((ligne, index) => (
              <div key={index} className="border border-slate-200 rounded p-3 space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:items-end">
                  <div className="sm:col-span-2">
                    <label className="block text-xs text-slate-500 mb-1">Type</label>
                    <select
                      className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                      value={ligne.type}
                      onChange={(e) => majLigne(index, 'type', e.target.value)}
                    >
                      <option value="moto">Moto</option>
                      <option value="casque">Casque</option>
                      <option value="autre">Autre</option>
                    </select>
                  </div>

                  <div className="sm:col-span-4">
                    <label className="block text-xs text-slate-500 mb-1">
                      {ligne.type === 'moto' ? 'Type de moto' : 'Article'}
                    </label>
                    {ligne.type === 'moto' && (
                      <select
                        className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                        value={ligne.type_moto}
                        required
                        onChange={(e) => majTypeMoto(index, e.target.value)}
                      >
                        <option value="">-- choisir --</option>
                        {(typesMoto ?? []).map((t) => (
                          <option key={t.id} value={t.id}>{t.marque_nom} {t.nom}</option>
                        ))}
                      </select>
                    )}
                    {ligne.type === 'casque' && (
                      <select
                        className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                        value={ligne.modele_casque}
                        required
                        onChange={(e) => majLigne(index, 'modele_casque', e.target.value)}
                      >
                        <option value="">-- choisir --</option>
                        {(casques ?? []).map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}
                      </select>
                    )}
                    {ligne.type === 'autre' && (
                      <input
                        className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                        value={ligne.designation}
                        required
                        onChange={(e) => majLigne(index, 'designation', e.target.value)}
                        placeholder="Designation"
                      />
                    )}
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs text-slate-500 mb-1">Quantite</label>
                    <input
                      type="number"
                      min="1"
                      className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                      value={ligne.quantite}
                      onChange={(e) => (
                        ligne.type === 'moto' ? majQuantite(index, e.target.value) : majLigne(index, 'quantite', e.target.value)
                      )}
                    />
                  </div>

                  <div className="sm:col-span-3">
                    <label className="block text-xs text-slate-500 mb-1">Prix unitaire</label>
                    <input
                      type="number"
                      step="0.01"
                      className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                      value={ligne.prix_unitaire}
                      required
                      onChange={(e) => majLigne(index, 'prix_unitaire', e.target.value)}
                    />
                  </div>

                  <div className="sm:col-span-1 text-right">
                    {lignes.length > 1 && (
                      <button type="button" onClick={() => supprimerLigne(index)} className="text-red-600 text-sm">
                        <span className="sm:hidden">Retirer cette ligne</span>
                        <span className="hidden sm:inline">&times;</span>
                      </button>
                    )}
                  </div>
                </div>

                {ligne.type === 'moto' && ligne.type_moto && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pl-1">
                    {ligne.series.map((serieId, slot) => {
                      const exclus = motosExclues(index, slot)
                      const options = motosDisponibles.filter((m) => (
                        String(m.type_moto) === String(ligne.type_moto) && !exclus.has(String(m.id))
                      ))
                      return (
                        <div key={slot}>
                          <label className="block text-xs text-slate-500 mb-1">N° serie {slot + 1}</label>
                          <select
                            className="w-full border border-slate-300 rounded px-2 py-1 text-sm"
                            value={serieId}
                            required
                            onChange={(e) => majSerie(index, slot, e.target.value)}
                          >
                            <option value="">-- choisir --</option>
                            {options.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.numero_serie}{m.statut === 'en_depot' ? ' (en depot)' : ''}
                              </option>
                            ))}
                          </select>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>

          <p className="text-right font-semibold text-slate-800 mt-3">
            Total : {new Intl.NumberFormat('fr-FR').format(total)} F
          </p>
        </div>

        <div>
          <label className="block text-sm text-slate-600 mb-1">Remarque</label>
          <textarea
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            rows={2}
            value={remarque}
            onChange={(e) => setRemarque(e.target.value)}
          />
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button type="submit" disabled={submitting} className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50">
          {submitting ? 'Creation...' : 'Creer la facture'}
        </button>
      </form>
    </div>
  )
}

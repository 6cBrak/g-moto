import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'
import CrudPage from '../../components/CrudPage'
import TypeMotoPage from './TypeMotoPage'

const onglets = [
  { key: 'marques', label: 'Marques' },
  { key: 'couleurs', label: 'Couleurs' },
  { key: 'types-moto', label: 'Types de moto' },
  { key: 'modeles-casque', label: 'Modeles de casque' },
  { key: 'fournisseurs', label: 'Fournisseurs' },
]

export default function CataloguePage() {
  const [onglet, setOnglet] = useState('marques')
  const user = useAuthStore((state) => state.user)
  const canWrite = user?.role === 'admin' || user?.role === 'gerant'

  return (
    <div>
      <div className="flex gap-2 mb-6 border-b border-slate-200">
        {onglets.map((o) => (
          <button
            key={o.key}
            onClick={() => setOnglet(o.key)}
            className={`px-4 py-2 text-sm border-b-2 -mb-px ${
              onglet === o.key ? 'border-slate-800 text-slate-900 font-medium' : 'border-transparent text-slate-500'
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>

      {onglet === 'marques' && (
        <CrudPage
          resource="marques"
          title="Marques"
          canWrite={canWrite}
          columns={[
            { key: 'nom', label: 'Nom' },
            { key: 'actif', label: 'Actif', render: (r) => (r.actif ? 'Oui' : 'Non') },
          ]}
          fields={[
            { name: 'nom', label: 'Nom', required: true },
            { name: 'actif', label: 'Actif', type: 'checkbox' },
          ]}
        />
      )}

      {onglet === 'couleurs' && (
        <CrudPage
          resource="couleurs"
          title="Couleurs"
          canWrite={canWrite}
          columns={[
            { key: 'nom', label: 'Nom' },
            { key: 'code_hex', label: 'Code hexa' },
          ]}
          fields={[
            { name: 'nom', label: 'Nom', required: true },
            { name: 'code_hex', label: 'Code hexa (ex: #FF0000)' },
          ]}
        />
      )}

      {onglet === 'types-moto' && <TypeMotoPage canWrite={canWrite} />}

      {onglet === 'modeles-casque' && (
        <CrudPage
          resource="modeles-casque"
          title="Modeles de casque"
          canWrite={canWrite}
          columns={[
            { key: 'nom', label: 'Nom' },
            { key: 'taille', label: 'Taille' },
            { key: 'actif', label: 'Actif', render: (r) => (r.actif ? 'Oui' : 'Non') },
          ]}
          fields={[
            { name: 'nom', label: 'Nom', required: true },
            { name: 'taille', label: 'Taille' },
            { name: 'actif', label: 'Actif', type: 'checkbox' },
          ]}
        />
      )}

      {onglet === 'fournisseurs' && (
        <CrudPage
          resource="fournisseurs"
          title="Fournisseurs"
          canWrite={canWrite}
          columns={[
            { key: 'nom', label: 'Nom' },
            { key: 'contact', label: 'Contact' },
            { key: 'telephone', label: 'Telephone' },
          ]}
          fields={[
            { name: 'nom', label: 'Nom', required: true },
            { name: 'contact', label: 'Contact' },
            { name: 'telephone', label: 'Telephone' },
            { name: 'adresse', label: 'Adresse' },
          ]}
        />
      )}
    </div>
  )
}

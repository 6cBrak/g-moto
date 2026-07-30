import CrudPage from '../../components/CrudPage'
import { useResourceList } from '../../hooks/useResource'

const ROLES = [
  { value: 'vendeur_caissier', label: 'Vendeur / Caissier' },
  { value: 'gerant', label: 'Gerant' },
  { value: 'admin', label: 'Admin' },
]

export default function UtilisateursPage() {
  const { data: agences } = useResourceList('agences')

  return (
    <CrudPage
      resource="utilisateurs"
      title="Utilisateurs"
      columns={[
        { key: 'username', label: 'Utilisateur' },
        { key: 'role', label: 'Role' },
        { key: 'agence_nom', label: 'Agence' },
        { key: 'email', label: 'Email' },
        { key: 'is_active', label: 'Actif', render: (r) => (r.is_active ? 'Oui' : 'Non') },
      ]}
      fields={[
        { name: 'username', label: 'Nom utilisateur', required: true },
        { name: 'password', label: 'Mot de passe (laisser vide pour ne pas changer)', type: 'password' },
        { name: 'first_name', label: 'Prenom' },
        { name: 'last_name', label: 'Nom' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'role', label: 'Role', type: 'select', required: true, options: ROLES },
        {
          name: 'agence',
          label: 'Agence',
          type: 'select',
          options: (agences ?? []).map((a) => ({ value: a.id, label: a.nom })),
        },
        { name: 'is_active', label: 'Actif', type: 'checkbox' },
      ]}
    />
  )
}

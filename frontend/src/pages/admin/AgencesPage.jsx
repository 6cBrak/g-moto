import CrudPage from '../../components/CrudPage'

export default function AgencesPage() {
  return (
    <CrudPage
      resource="agences"
      title="Agences"
      columns={[
        { key: 'nom', label: 'Nom' },
        { key: 'nom_commercial', label: 'Nom commercial', render: (r) => r.nom_commercial || '-' },
        { key: 'telephone', label: 'Telephone' },
        { key: 'email', label: 'Email', render: (r) => r.email || '-' },
        { key: 'adresse', label: 'Adresse' },
        { key: 'actif', label: 'Actif', render: (r) => (r.actif ? 'Oui' : 'Non') },
      ]}
      fields={[
        { name: 'nom', label: 'Nom', required: true },
        { name: 'nom_commercial', label: 'Nom commercial (affiche sur les documents)' },
        { name: 'logo', label: 'Logo (affiche sur les documents)', type: 'file' },
        { name: 'adresse', label: 'Adresse' },
        { name: 'telephone', label: 'Telephone' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'site_web', label: 'Site web' },
        { name: 'rccm', label: 'RCCM (registre de commerce)' },
        { name: 'nif', label: 'NIF (identification fiscale)' },
        { name: 'actif', label: 'Actif', type: 'checkbox' },
      ]}
    />
  )
}

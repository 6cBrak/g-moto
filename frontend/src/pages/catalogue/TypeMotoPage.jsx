import CrudPage from '../../components/CrudPage'
import { useResourceList } from '../../hooks/useResource'

export default function TypeMotoPage({ canWrite }) {
  const { data: marques } = useResourceList('marques')

  return (
    <CrudPage
      resource="types-moto"
      title="Types de moto"
      canWrite={canWrite}
      columns={[
        { key: 'marque_nom', label: 'Marque' },
        { key: 'nom', label: 'Modele' },
        { key: 'code', label: 'Code' },
        { key: 'cylindree', label: 'Cylindree (cm3)' },
        { key: 'seuil_alerte', label: 'Seuil alerte stock' },
      ]}
      fields={[
        {
          name: 'marque',
          label: 'Marque',
          type: 'select',
          required: true,
          options: (marques ?? []).map((m) => ({ value: m.id, label: m.nom })),
        },
        { name: 'nom', label: 'Modele', required: true },
        { name: 'code', label: 'Code (prefixe n° de serie)' },
        { name: 'cylindree', label: 'Cylindree (cm3)', type: 'number' },
        { name: 'seuil_alerte', label: 'Seuil alerte stock', type: 'number' },
      ]}
    />
  )
}

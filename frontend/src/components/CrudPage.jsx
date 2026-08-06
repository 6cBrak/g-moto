import { useEffect, useState } from 'react'
import DataTable from './DataTable'
import FormModal from './FormModal'
import Pagination from './Pagination'
import { useResourceListPaged, useResourceMutations } from '../hooks/useResource'

export default function CrudPage({ resource, title, columns, fields, canWrite = true, extraParams = {}, onRowClick, selectedId, filterBar }) {
  const [page, setPage] = useState(1)
  const { data: rowsPage, isLoading } = useResourceListPaged(resource, { ...extraParams, page })
  const rows = rowsPage?.results
  const { create, update, remove } = useResourceMutations(resource)
  const [modalMode, setModalMode] = useState(null)
  const [editing, setEditing] = useState(null)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setPage(1) }, [JSON.stringify(extraParams)])

  const handleSubmit = async (values) => {
    if (modalMode === 'create') {
      await create.mutateAsync(values)
    } else {
      await update.mutateAsync({ id: editing.id, payload: values })
    }
  }

  const handleDelete = async (row) => {
    if (window.confirm('Supprimer cet element ?')) {
      await remove.mutateAsync(row.id)
    }
  }

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
        <h1 className="text-xl font-semibold text-slate-800">{title}</h1>
        {canWrite && (
          <button
            onClick={() => { setEditing(null); setModalMode('create') }}
            className="px-4 py-2 text-sm bg-slate-800 text-white rounded"
          >
            + Nouveau
          </button>
        )}
      </div>

      {filterBar}

      <DataTable
        columns={columns}
        rows={rows}
        isLoading={isLoading}
        onRowClick={onRowClick}
        selectedId={selectedId}
        actions={canWrite ? (row) => (
          <>
            <button
              onClick={() => { setEditing(row); setModalMode('edit') }}
              className="text-slate-600 hover:text-slate-900 text-sm"
            >
              Modifier
            </button>
            <button
              onClick={() => handleDelete(row)}
              className="text-red-600 hover:text-red-800 text-sm"
            >
              Supprimer
            </button>
          </>
        ) : undefined}
      />
      <Pagination page={page} onPageChange={setPage} count={rowsPage?.count ?? 0} />

      {modalMode && (
        <FormModal
          title={modalMode === 'create' ? `Nouveau : ${title}` : `Modifier : ${title}`}
          fields={fields}
          initialValues={editing ?? {}}
          onSubmit={handleSubmit}
          onClose={() => setModalMode(null)}
        />
      )}
    </div>
  )
}

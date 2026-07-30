export default function DataTable({ columns, rows, isLoading, emptyMessage = 'Aucune donnee.', actions, onRowClick, selectedId, rowClassName }) {
  if (isLoading) {
    return <p className="text-slate-500 text-sm py-8 text-center">Chargement...</p>
  }

  if (!rows || rows.length === 0) {
    return <p className="text-slate-500 text-sm py-8 text-center">{emptyMessage}</p>
  }

  return (
    <div className="overflow-x-auto border border-slate-200 rounded-lg">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-2 text-left font-medium text-slate-600">
                {col.label}
              </th>
            ))}
            {actions && <th className="px-4 py-2 text-right font-medium text-slate-600">Actions</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr
              key={row.id ?? index}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`hover:bg-slate-50 ${onRowClick ? 'cursor-pointer' : ''} ${selectedId != null && row.id === selectedId ? 'bg-slate-100' : ''} ${rowClassName ? rowClassName(row) : ''}`}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-2 text-slate-700">
                  {col.render ? col.render(row) : (row[col.key] ?? '-')}
                </td>
              ))}
              {actions && (
                <td
                  className="px-4 py-2 text-right space-x-2 whitespace-nowrap"
                  onClick={onRowClick ? (e) => e.stopPropagation() : undefined}
                >
                  {actions(row)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

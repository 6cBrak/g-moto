export default function Pagination({ page, onPageChange, count, pageSize = 20 }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between mt-3 text-sm text-slate-600">
      <span>Page {page} sur {totalPages} ({count} au total)</span>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5 border border-slate-300 rounded disabled:opacity-40"
        >
          Precedent
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1.5 border border-slate-300 rounded disabled:opacity-40"
        >
          Suivant
        </button>
      </div>
    </div>
  )
}

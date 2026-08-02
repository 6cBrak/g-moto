export default function FilterBar({ filters, values, onChange }) {
  return (
    <div className="grid grid-cols-2 sm:flex sm:flex-wrap items-end gap-3 mb-4">
      {filters.map((f) => (
        <div key={f.name} className="min-w-0">
          <label className="block text-xs text-slate-500 mb-1">{f.label}</label>
          {f.type === 'select' ? (
            <select
              className="w-full sm:w-auto border border-slate-300 rounded px-2 py-1.5 sm:py-1 text-sm"
              value={values[f.name] ?? ''}
              onChange={(e) => onChange(f.name, e.target.value)}
            >
              <option value="">{f.allLabel ?? 'Tous'}</option>
              {f.options.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          ) : (
            <input
              type={f.type ?? 'text'}
              placeholder={f.placeholder}
              className="w-full sm:w-auto border border-slate-300 rounded px-2 py-1.5 sm:py-1 text-sm"
              value={values[f.name] ?? ''}
              onChange={(e) => onChange(f.name, e.target.value)}
            />
          )}
        </div>
      ))}
    </div>
  )
}

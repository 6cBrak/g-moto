export default function FilterBar({ filters, values, onChange }) {
  return (
    <div className="flex flex-wrap items-end gap-3 mb-4">
      {filters.map((f) => (
        <div key={f.name}>
          <label className="block text-xs text-slate-500 mb-1">{f.label}</label>
          {f.type === 'select' ? (
            <select
              className="border border-slate-300 rounded px-2 py-1 text-sm"
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
              className="border border-slate-300 rounded px-2 py-1 text-sm"
              value={values[f.name] ?? ''}
              onChange={(e) => onChange(f.name, e.target.value)}
            />
          )}
        </div>
      ))}
    </div>
  )
}

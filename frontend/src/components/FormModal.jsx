import { useState } from 'react'
import Modal from './Modal'

function champVide(fields) {
  return Object.fromEntries(fields.map((f) => [f.name, f.type === 'checkbox' ? false : '']))
}

export default function FormModal({ title, fields, initialValues, onSubmit, onClose, submitLabel = 'Enregistrer', wide = false }) {
  const [values, setValues] = useState({ ...champVide(fields), ...initialValues })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (name, value) => {
    setValues((prev) => {
      const next = { ...prev, [name]: value }
      const field = fields.find((f) => f.name === name)
      const patch = field?.onChange?.(value, prev)
      return patch ? { ...next, ...patch } : next
    })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const contientFichier = fields.some((f) => f.type === 'file')
      if (contientFichier) {
        const formData = new FormData()
        Object.entries(values).forEach(([key, value]) => {
          if (value !== '' && value !== null && value !== undefined) {
            formData.append(key, value)
          }
        })
        await onSubmit(formData)
      } else {
        await onSubmit(values)
      }
      onClose()
    } catch (err) {
      const data = err?.response?.data
      const message = data
        ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' — ')
        : 'Une erreur est survenue.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal title={title} onClose={onClose} wide={wide}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map((field) => (
          <div key={field.name}>
            <label className="block text-sm text-slate-600 mb-1">{field.label}</label>
            {field.type === 'select' ? (
              <select
                className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                value={values[field.name]}
                required={field.required}
                onChange={(e) => handleChange(field.name, e.target.value)}
              >
                <option value="">-- choisir --</option>
                {field.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            ) : field.type === 'textarea' ? (
              <textarea
                className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                value={values[field.name]}
                required={field.required}
                onChange={(e) => handleChange(field.name, e.target.value)}
              />
            ) : field.type === 'checkbox' ? (
              <input
                type="checkbox"
                checked={!!values[field.name]}
                onChange={(e) => handleChange(field.name, e.target.checked)}
              />
            ) : field.type === 'file' ? (
              <input
                type="file"
                className="w-full text-sm"
                required={field.required}
                onChange={(e) => handleChange(field.name, e.target.files[0])}
              />
            ) : (
              <input
                type={field.type ?? 'text'}
                step={field.step}
                className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                value={values[field.name]}
                required={field.required}
                onChange={(e) => handleChange(field.name, e.target.value)}
              />
            )}
          </div>
        ))}
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900">
            Annuler
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 text-sm bg-slate-800 text-white rounded disabled:opacity-50"
          >
            {submitting ? '...' : submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  )
}

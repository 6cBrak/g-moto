export function formatMontant(valeur) {
  const nombre = Number(valeur ?? 0)
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(nombre)
}

export function formatDate(valeur) {
  if (!valeur) return '-'
  return new Date(valeur).toLocaleDateString('fr-FR')
}

export function formatDateTime(valeur) {
  if (!valeur) return '-'
  return new Date(valeur).toLocaleString('fr-FR')
}

export function formatHeure(valeur) {
  if (!valeur) return '-'
  return new Date(valeur).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

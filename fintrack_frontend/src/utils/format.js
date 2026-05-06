export function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 2 }).format(amount)
}

export function formatDate(dateStr) {
  if (!dateStr) return '—'
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatMonth(dateStr) {
  if (!dateStr) return ''
  const [year, month] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, 1).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
}

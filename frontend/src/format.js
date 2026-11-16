export const CATEGORIES = [
  'Groceries',
  'Dining',
  'Transport',
  'Shopping',
  'Health',
  'Utilities',
  'Other',
]

export function formatMoney(amount, currency = 'USD') {
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount ?? 0)
  } catch {
    // Unknown currency codes make Intl throw, so fall back to a plain number.
    return `${Number(amount ?? 0).toFixed(2)} ${currency}`
  }
}

export function formatDate(isoDate) {
  if (!isoDate) return 'No date'
  // Appending a time stops the browser shifting the date by the UTC offset.
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

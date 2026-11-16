const BASE = '/api/v1/receipts'

async function request(path, options) {
  const response = await fetch(path, options)

  if (!response.ok) {
    // FastAPI puts the readable error message in "detail".
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new Error(detail || `Request failed (${response.status})`)
  }

  return response.status === 204 ? null : response.json()
}

export function scanReceipt(file) {
  const form = new FormData()
  form.append('file', file)
  return request(`${BASE}/scan`, { method: 'POST', body: form })
}

export function listReceipts(search = '') {
  const params = new URLSearchParams({ limit: '50' })
  if (search) params.set('q', search)
  return request(`${BASE}?${params}`)
}

export function updateReceipt(id, data) {
  return request(`${BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export function deleteReceipt(id) {
  return request(`${BASE}/${id}`, { method: 'DELETE' })
}

export function deleteSamples() {
  return request(`${BASE}/samples`, { method: 'DELETE' })
}

export function getSummary() {
  return request(`${BASE}/summary`)
}

export function getHealth() {
  return request('/api/health')
}

export const imageUrl = (id) => `${BASE}/${id}/image`
export const exportUrl = `${BASE}/export.csv`

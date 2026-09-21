const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function parseError(response) {
  try {
    const body = await response.json()
    return body.detail ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

export async function extractTitles(file) {
  const form = new FormData()
  form.append('pdf', file)

  const response = await fetch(`${API_BASE}/api/extract-titles`, {
    method: 'POST',
    body: form,
  })
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

export async function searchJobs(query, location) {
  const response = await fetch(`${API_BASE}/api/search-jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, location: location || null }),
  })
  if (!response.ok) throw new Error(await parseError(response))
  return response.json()
}

const BASE = '/api'

export async function getConfig() {
  const resp = await fetch(`${BASE}/config`)
  return resp.json()
}

export async function updateConfig(data) {
  const resp = await fetch(`${BASE}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return resp.json()
}

export async function query(question, topK = 5, tagFilter = null) {
  const resp = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK, tag_filter: tagFilter }),
  })
  return resp.json()
}

export async function getTags() {
  const resp = await fetch(`${BASE}/tags`)
  return resp.json()
}

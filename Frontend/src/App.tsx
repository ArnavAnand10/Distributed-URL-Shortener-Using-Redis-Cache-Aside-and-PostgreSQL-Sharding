import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type CreateResponse = {
  short_url: string
  original_url: string
}

type ResolveResponse = {
  short_code: string
  original_url: string
  source: 'cache' | 'db'
  server_latency_ms: number
}

type LookupEntry = {
  id: number
  short_code: string
  original_url: string
  source: 'cache' | 'db'
  server_latency_ms: number
  round_trip_ms: number
}

function App() {
  const [url, setUrl] = useState('https://')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<CreateResponse | null>(null)
  const [copied, setCopied] = useState(false)

  const [lookupCode, setLookupCode] = useState('')
  const [lookupLoading, setLookupLoading] = useState(false)
  const [lookupError, setLookupError] = useState('')
  const [lookupHistory, setLookupHistory] = useState<LookupEntry[]>([])
  const [nextId, setNextId] = useState(1)

  const apiBase = useMemo(
    () => import.meta.env.VITE_API_BASE?.replace(/\/$/, '') ?? 'http://localhost:8080',
    [],
  )

  const shortLink = result ? `${apiBase}/${result.short_url}` : ''

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    setCopied(false)
    try {
      const response = await fetch(`${apiBase}/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(typeof data?.detail === 'string' ? data.detail : 'Request failed')
      }
      setResult(data as CreateResponse)
      setUrl('https://')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const copyShortLink = async () => {
    if (!shortLink) return
    try {
      await navigator.clipboard.writeText(shortLink)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Could not copy to clipboard')
    }
  }

  const onLookup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLookupLoading(true)
    setLookupError('')
    const raw = lookupCode.trim()
    const shortCode = raw.includes('/') ? raw.split('/').filter(Boolean).pop() ?? raw : raw
    const t0 = performance.now()
    try {
      const response = await fetch(`${apiBase}/resolve/${encodeURIComponent(shortCode)}`)
      const roundTripMs = Math.round(performance.now() - t0)
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(typeof data?.detail === 'string' ? data.detail : 'Not found')
      }
      const res = data as ResolveResponse
      setLookupHistory((prev) => [
        {
          id: nextId,
          short_code: res.short_code,
          original_url: res.original_url,
          source: res.source,
          server_latency_ms: res.server_latency_ms,
          round_trip_ms: roundTripMs,
        },
        ...prev.slice(0, 19),
      ])
      setNextId((n) => n + 1)
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLookupLoading(false)
    }
  }

  const maxServerLatency = lookupHistory.length
    ? Math.max(...lookupHistory.map((entry) => entry.server_latency_ms), 1)
    : 1
  const cacheHits = lookupHistory.filter((entry) => entry.source === 'cache').length
  const dbHits = lookupHistory.filter((entry) => entry.source === 'db').length
  const avgMs = lookupHistory.length
    ? (lookupHistory.reduce((sum, entry) => sum + entry.server_latency_ms, 0) / lookupHistory.length).toFixed(1)
    : null
  const cacheRate = lookupHistory.length
    ? Math.round((cacheHits / lookupHistory.length) * 100)
    : null

  const stackItems = [
    { label: 'Gateway', value: 'NGINX reverse proxy and routing' },
    { label: 'Creation API', value: 'POST /create returns short_url and original_url' },
    { label: 'Resolve API', value: 'GET /resolve/{code} returns source and latency' },
    { label: 'Cache Strategy', value: 'Redis cache-aside before PostgreSQL fallback' },
  ]

  return (
    <div className="root">
      <header className="topbar">
        <div className="topbar__inner">
          <div className="brand-wrap">
            <span className="brand">Short Link Console</span>
            <span className="brand-sub">Create, resolve, and inspect traffic behavior</span>
          </div>
          <div className="topbar-right">
            <span className="live-pill">Live</span>
            <div className="stack-chips">
              <span className="chip">NGINX</span>
              <span className="chip">Redis</span>
              <span className="chip">PostgreSQL</span>
            </div>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="layout">
          <section className="pane">
            <div className="pane__head pane__head--stack">
              <h2 className="pane__title">Create Short URL</h2>
              <p className="pane__desc">
                Sends your long URL to <code className="inline-code">POST /create</code> and returns a short code that routes through the gateway.
              </p>
              <div className="meta-strip">
                <span className="meta-pill">Validation: URL format enforced</span>
                <span className="meta-pill">Response: short_url + original_url</span>
                <span className="meta-pill">Gateway: {apiBase}</span>
              </div>
            </div>

            <form className="form-stack" onSubmit={onSubmit}>
              <label className="field-label" htmlFor="url-input">Long URL</label>
              <div className="field-row">
                <input
                  id="url-input"
                  className="text-input"
                  type="url"
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="https://example.com/product/alpha?source=campaign"
                  required
                />
                <button className="btn btn--primary" type="submit" disabled={loading}>
                  {loading ? <span className="spinner" /> : 'Generate'}
                </button>
              </div>
            </form>

            {error && <p className="notice notice--error">{error}</p>}

            {result && (
              <div className="result-card">
                <div className="result-row">
                  <span className="result-label">Short URL</span>
                  <a className="result-link" href={shortLink} target="_blank" rel="noreferrer">
                    {shortLink}
                  </a>
                  <button
                    className={`btn btn--ghost${copied ? ' btn--done' : ''}`}
                    type="button"
                    onClick={copyShortLink}
                  >
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="result-row result-row--muted">
                  <span className="result-label">Original URL</span>
                  <a
                    className="result-link result-link--muted"
                    href={result.original_url}
                    target="_blank"
                    rel="noreferrer"
                    title={result.original_url}
                  >
                    {result.original_url.length > 84
                      ? `${result.original_url.slice(0, 84)}...`
                      : result.original_url}
                  </a>
                </div>
                <div className="result-row result-row--meta">
                  <span className="result-label">Routing</span>
                  <span className="result-info">All traffic enters through NGINX and resolves through Redis cache-aside before PostgreSQL fallback.</span>
                </div>
              </div>
            )}
          </section>

          <section className="pane">
            <div className="pane__head">
              <div className="pane__head-main">
                <h2 className="pane__title">Resolve Analytics</h2>
                <p className="pane__desc pane__desc--tight">
                  Resolves codes via <code className="inline-code">GET /resolve/{'{code}'}</code> and shows source plus latency metrics.
                </p>
              </div>

              <div className="stats-row">
                <div className="stat">
                  <span className="stat__label">Requests</span>
                  <strong className="stat__value">{lookupHistory.length}</strong>
                </div>
                <div className="stat stat--cache">
                  <span className="stat__label">Cache</span>
                  <strong className="stat__value">{cacheHits}</strong>
                </div>
                <div className="stat stat--db">
                  <span className="stat__label">DB</span>
                  <strong className="stat__value">{dbHits}</strong>
                </div>
                <div className="stat">
                  <span className="stat__label">Avg ms</span>
                  <strong className="stat__value">{avgMs ?? '--'}</strong>
                </div>
                <div className="stat">
                  <span className="stat__label">Cache rate</span>
                  <strong className="stat__value">{cacheRate !== null ? `${cacheRate}%` : '--'}</strong>
                </div>
              </div>
            </div>

            <div className="resolve-flow">
              <span className="resolve-flow__item">1. Parse short code</span>
              <span className="resolve-flow__item">2. Check Redis</span>
              <span className="resolve-flow__item">3. Fallback to PostgreSQL</span>
              <span className="resolve-flow__item">4. Return original URL + latency</span>
            </div>

            <form className="form-stack" onSubmit={onLookup}>
              <label className="field-label" htmlFor="lookup-input">Short code or full short URL</label>
              <div className="field-row">
                <input
                  id="lookup-input"
                  className="text-input"
                  type="text"
                  value={lookupCode}
                  onChange={(event) => setLookupCode(event.target.value)}
                  placeholder="abc123 or http://localhost:8080/abc123"
                  required
                />
                <button className="btn btn--secondary" type="submit" disabled={lookupLoading}>
                  {lookupLoading ? <span className="spinner spinner--dark" /> : 'Resolve'}
                </button>
              </div>
            </form>

            {lookupError && <p className="notice notice--error">{lookupError}</p>}

            {lookupHistory.length > 0 ? (
              <div className="ledger">
                {lookupHistory.map((entry, idx) => {
                  const pct = Math.min(100, (entry.server_latency_ms / maxServerLatency) * 100)
                  return (
                    <article key={entry.id} className={`ledger-entry ledger-entry--${entry.source}`}>
                      <div className="ledger-entry__head">
                        <div className="ledger-entry__id">
                          <span className="ledger-entry__seq">#{lookupHistory.length - idx}</span>
                          <span className="ledger-entry__code">{entry.short_code}</span>
                        </div>
                        <span className={`badge badge--${entry.source}`}>
                          {entry.source === 'cache' ? 'Redis Cache' : 'PostgreSQL'}
                        </span>
                      </div>

                      <div className="ledger-entry__metrics">
                        <span className="metric-pair">
                          <span className="metric-pair__label">Server</span>
                          <span className="metric-pair__value">{entry.server_latency_ms} ms</span>
                        </span>
                        <span className="metric-pair">
                          <span className="metric-pair__label">Round-trip</span>
                          <span className="metric-pair__value">{entry.round_trip_ms} ms</span>
                        </span>
                        <div className="latency-bar">
                          <span
                            className={`latency-bar__fill latency-bar__fill--${entry.source}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>

                      <a
                        className="ledger-entry__url"
                        href={entry.original_url}
                        target="_blank"
                        rel="noreferrer"
                        title={entry.original_url}
                      >
                        {entry.original_url}
                      </a>
                    </article>
                  )
                })}
              </div>
            ) : (
              <div className="empty-state">
                No resolve records yet. Submit a short code above and this panel will show request sequence, data source, server latency, and round-trip timing.
              </div>
            )}
          </section>

          <section className="pane pane--wide">
            <div className="pane__head pane__head--stack">
              <h2 className="pane__title">Operational Context</h2>
              <p className="pane__desc">
                This section describes exactly how requests flow through the system so the interface remains informative even before traffic arrives.
              </p>
            </div>

            <div className="ops-grid">
              {stackItems.map((item) => (
                <article key={item.label} className="ops-card">
                  <span className="ops-card__label">{item.label}</span>
                  <p className="ops-card__value">{item.value}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default App
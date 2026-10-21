import { useCallback, useEffect, useState } from 'react'
import './App.css'

type Target = {
  id: number
  name: string
  url: string
}

type HealthCheck = {
  id: number
  target_id: number
  target_name: string
  url: string
  success: boolean
  status_code: number | null
  response_time_ms: number | null
  checked_at: string
  error: string | null
}

type Incident = {
  id: number
  target_id: number
  target_name: string
  reason: string
  status: string
  created_at: string
  resolved_at: string | null
  response_time_ms: number | null
}

function App() {
  const [targets, setTargets] = useState<Target[]>([])
  const [checks, setChecks] = useState<HealthCheck[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const responses = await Promise.all([
        fetch('/targets'),
        fetch('/checks'),
        fetch('/incidents'),
      ])

      if (responses.some((response) => !response.ok)) {
        throw new Error('The backend returned an error. Check that Flask is running.')
      }

      const [targetData, checkData, incidentData] = await Promise.all(
        responses.map((response) => response.json()),
      )

      setTargets(targetData.targets ?? [])
      setChecks(checkData.checks ?? [])
      setIncidents(incidentData.incidents ?? [])
      setLastUpdated(new Date())
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not connect to the backend.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadDashboard()
  }, [loadDashboard])

  const latestChecks = targets.map((target) => {
    const targetChecks = checks
      .filter((check) => check.target_id === target.id)
      .sort((a, b) => b.id - a.id)

    return {
      target,
      latest: targetChecks[0],
    }
  })

  const successfulChecks = checks.filter((check) => check.success).length
  const failedChecks = checks.filter((check) => !check.success).length
  const openIncidents = incidents.filter(
    (incident) => incident.status.toLowerCase() === 'open',
  ).length
  const averageResponseTime = checks.length
    ? checks.reduce((total, check) => total + (check.response_time_ms ?? 0), 0) /
      checks.length
    : 0

  const recentChecks = [...checks].sort((a, b) => b.id - a.id).slice(0, 6)
  const recentIncidents = [...incidents].sort((a, b) => b.id - a.id).slice(0, 5)

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">R</div>
          <div>
            <strong>Reliability</strong>
            <span>MONITORING PLATFORM</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <a className="nav-item active" href="#overview">
          <span>◫</span> Overview
        </a>
        <a className="nav-item" href="#targets">
          <span>◎</span> API targets
        </a>
        <a className="nav-item" href="#checks">
          <span>⌁</span> Health checks
        </a>
        <a className="nav-item" href="#incidents">
          <span>△</span> Incidents
        </a>

        <div className="sidebar-bottom">
          <div className="connection-dot" />
          <div>
            <strong>Backend connection</strong>
            <span>{error ? 'Connection issue' : 'Local environment'}</span>
          </div>
        </div>
      </aside>

      <section className="main-content" id="overview">
        <header className="topbar">
          <div>
            <div className="eyebrow">MONITORING / OVERVIEW</div>
            <h1>System overview</h1>
            <p className="subtitle">
              Monitor API health, performance and incidents in one place.
            </p>
          </div>
          <button className="refresh-button" onClick={() => void loadDashboard()}>
            <span>↻</span> {loading ? 'Refreshing…' : 'Refresh data'}
          </button>
        </header>

        {error && (
          <div className="error-banner">
            <strong>Unable to load live data.</strong> {error}
            <button onClick={() => void loadDashboard()}>Retry</button>
          </div>
        )}

        <div className="section-heading">
          <div>
            <h2>Key metrics</h2>
            <p>Based on recorded backend data</p>
          </div>
          <span className="live-label"><span /> BACKEND DATA</span>
        </div>

        <section className="metrics-grid">
          <article className="metric-card">
            <div className="metric-top">
              <span>Monitored APIs</span>
              <span className="metric-icon purple">◎</span>
            </div>
            <div className="metric-value">{targets.length}</div>
            <div className="metric-foot">Configured targets</div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span>Successful checks</span>
              <span className="metric-icon green">✓</span>
            </div>
            <div className="metric-value">{successfulChecks}</div>
            <div className="metric-foot">
              {checks.length} total recorded checks
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span>Failed checks</span>
              <span className="metric-icon red">!</span>
            </div>
            <div className="metric-value">{failedChecks}</div>
            <div className="metric-foot">Recorded unsuccessful checks</div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span>Open incidents</span>
              <span className="metric-icon amber">△</span>
            </div>
            <div className="metric-value">{openIncidents}</div>
            <div className="metric-foot">
              {incidents.length} total recorded incidents
            </div>
          </article>
        </section>

        <section className="content-grid" id="targets">
          <article className="panel targets-panel">
            <div className="panel-heading">
              <div>
                <h2>API targets</h2>
                <p>Latest recorded result for each target</p>
              </div>
              <span className="count-pill">{targets.length} targets</span>
            </div>

            {loading && targets.length === 0 ? (
              <p className="empty-state">Loading API targets…</p>
            ) : targets.length === 0 ? (
              <p className="empty-state">No API targets found.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>API TARGET</th>
                      <th>STATUS</th>
                      <th>RESPONSE</th>
                      <th>HTTP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestChecks.map(({ target, latest }) => (
                      <tr key={target.id}>
                        <td>
                          <div className="target-name">{target.name}</div>
                          <div className="target-url">{target.url}</div>
                        </td>
                        <td>
                          {latest ? (
                            <span className={`status ${latest.success ? 'ok' : 'failed'}`}>
                              <span />
                              {latest.success ? 'Healthy' : 'Failing'}
                            </span>
                          ) : (
                            <span className="status unknown">Not checked</span>
                          )}
                        </td>
                        <td className="response-time">
                          {latest?.response_time_ms != null
                            ? `${latest.response_time_ms.toFixed(1)} ms`
                            : '—'}
                        </td>
                        <td>
                          {latest?.status_code ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="panel performance-panel">
            <div className="panel-heading">
              <div>
                <h2>Performance snapshot</h2>
                <p>Across recorded health checks</p>
              </div>
            </div>
            <div className="performance-number">
              {checks.length ? averageResponseTime.toFixed(1) : '—'}
              <span> ms</span>
            </div>
            <p className="performance-caption">Average response time</p>
            <div className="performance-divider" />
            <div className="performance-row">
              <span>Successful checks</span>
              <strong>{checks.length ? `${Math.round((successfulChecks / checks.length) * 100)}%` : '—'}</strong>
            </div>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${checks.length ? (successfulChecks / checks.length) * 100 : 0}%`,
                }}
              />
            </div>
            <div className="performance-row">
              <span>Recorded incidents</span>
              <strong>{incidents.length}</strong>
            </div>
            <div className="performance-row">
              <span>Resolved incidents</span>
              <strong>
                {incidents.filter((incident) => incident.status.toLowerCase() === 'resolved').length}
              </strong>
            </div>
            <p className="data-note">
              Metrics use historical records, not a real-time uptime calculation.
            </p>
          </article>
        </section>

        <section className="content-grid lower-grid">
          <article className="panel" id="checks">
            <div className="panel-heading">
              <div>
                <h2>Recent health checks</h2>
                <p>Latest recorded check results</p>
              </div>
              <span className="count-pill">{checks.length} records</span>
            </div>

            {recentChecks.length === 0 ? (
              <p className="empty-state">No health checks recorded yet.</p>
            ) : (
              <div className="activity-list">
                {recentChecks.map((check) => (
                  <div className="activity-item" key={check.id}>
                    <div className={`activity-icon ${check.success ? 'success-icon' : 'failure-icon'}`}>
                      {check.success ? '✓' : '!'}
                    </div>
                    <div className="activity-main">
                      <strong>{check.target_name}</strong>
                      <span>{check.checked_at}</span>
                    </div>
                    <div className="activity-result">
                      <strong>{check.status_code ?? 'Error'}</strong>
                      <span>{check.response_time_ms?.toFixed(1) ?? '—'} ms</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="panel" id="incidents">
            <div className="panel-heading">
              <div>
                <h2>Recent incidents</h2>
                <p>Incident history from the backend</p>
              </div>
              <span className="count-pill">{incidents.length} records</span>
            </div>

            {recentIncidents.length === 0 ? (
              <p className="empty-state">No incidents recorded yet.</p>
            ) : (
              <div className="incident-list">
                {recentIncidents.map((incident) => (
                  <div className="incident-item" key={incident.id}>
                    <div className={`incident-symbol ${incident.status.toLowerCase() === 'open' ? 'incident-open' : 'incident-resolved'}`}>
                      {incident.status.toLowerCase() === 'open' ? '!' : '✓'}
                    </div>
                    <div className="incident-main">
                      <strong>{incident.target_name}</strong>
                      <span>{incident.reason}</span>
                      <small>{incident.created_at}</small>
                    </div>
                    <span className={`incident-status ${incident.status.toLowerCase() === 'open' ? 'open' : 'resolved'}`}>
                      {incident.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>

        <footer className="footer">
          <span>API Reliability &amp; Incident Replay Platform</span>
          <span>
            {lastUpdated
              ? `Last refreshed ${lastUpdated.toLocaleTimeString()}`
              : 'Waiting for data'}
          </span>
        </footer>
      </section>
    </main>
  )
}

export default App

'use client'

import { useEffect, useState } from 'react'
import Navbar from '@/components/Navbar'

interface ScraperLog {
  id: number
  status: string
  records_extracted: number
  error_message: string | null
  run_date: string
  created_at: string
}

interface ScraperStatus {
  status: string
  last_run: string | null
  last_status: string | null
  total_records: number
  last_extraction_count: number
}

interface Court {
  court_number: string
  court_name: string
  judge: string
  url: string
  has_data: boolean
}

interface CourtDiscoveryResponse {
  date: string
  total_courts_checked: number
  courts_with_data: number
  courts: Court[]
}

export default function AdminPage() {
  const [logs, setLogs] = useState<ScraperLog[]>([])
  const [status, setStatus] = useState<ScraperStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [targetDate, setTargetDate] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [liveLogs, setLiveLogs] = useState<string[]>([])
  const [discoveryDate, setDiscoveryDate] = useState('')
  const [discovering, setDiscovering] = useState(false)
  const [discoveredCourts, setDiscoveredCourts] = useState<Court[]>([])
  const [selectedCourts, setSelectedCourts] = useState<string[]>([])
  const [fetchingCourts, setFetchingCourts] = useState(false)

  const stopScraper = async () => {
    try {
      const token = localStorage.getItem('token')
      await fetch(`/api/proxy/api/scraper/stop`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      setMessage('Stop requested...')
    } catch (err) {
      console.error('Failed to stop scraper', err)
    }
  }

  useEffect(() => {
    let intervalId: NodeJS.Timeout

    if (triggering || discovering || fetchingCourts) {
      setLiveLogs([])
      intervalId = setInterval(async () => {
        try {
          const token = localStorage.getItem('token')
          const res = await fetch(`/api/proxy/api/scraper/progress`, {
             headers: { 'Authorization': `Bearer ${token}` }
          })
          if (res.ok) {
            const data = await res.json()
            if (data.logs) {
                setLiveLogs(data.logs)
            }
          }
        } catch (e) {
          console.error("Polling error", e)
        }
      }, 2000)
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [triggering, discovering, fetchingCourts])

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setError('Please login first')
        setLoading(false)
        return
      }

      const headers = { 'Authorization': `Bearer ${token}` }
      
      const [statusRes, logsRes] = await Promise.all([
        fetch(`/api/proxy/api/scraper/status`, { headers }),
        fetch(`/api/proxy/api/scraper/logs`, { headers })
      ])
      
      if (statusRes.ok) {
        const statusData = await statusRes.json()
        setStatus(statusData)
      }
      
      if (logsRes.ok) {
        const logsData = await logsRes.json()
        setLogs(logsData)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const triggerScraper = async () => {
    setTriggering(true)
    setMessage('')
    setError('')
    
    try {
      const token = localStorage.getItem('token')
      let url = `/api/proxy/api/scraper/trigger`
      if (targetDate) {
        url += `?target_date=${targetDate}`
      }
      
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setMessage(`Scraper completed! Extracted ${data.records_extracted} records.`)
        fetchData()
      } else {
        setError(data.message || 'Failed to trigger scraper')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to trigger scraper')
    } finally {
      setTriggering(false)
    }
  }

  const discoverCourts = async () => {
    if (!discoveryDate) {
      setError('Please select a date for court discovery')
      return
    }

    setDiscovering(true)
    setError('')
    setMessage('')
    setDiscoveredCourts([])
    setSelectedCourts([])

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `/api/proxy/api/scraper/discover-courts?target_date=${discoveryDate}&court_start=1&court_end=60`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      const data: CourtDiscoveryResponse = await response.json()

      if (response.ok) {
        setDiscoveredCourts(data.courts)
        setMessage(`Found ${data.courts_with_data} courts with data out of ${data.total_courts_checked} checked`)
        if (data.courts.length > 0) {
          setSelectedCourts(data.courts.map(c => c.court_number))
        }
      } else {
        setError('Failed to discover courts')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to discover courts')
    } finally {
      setDiscovering(false)
    }
  }

  const fetchSelectedCourts = async () => {
    if (selectedCourts.length === 0) {
      setError('No courts selected')
      return
    }

    setFetchingCourts(true)
    setError('')
    setMessage('')

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/proxy/api/scraper/fetch-court-data`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          target_date: discoveryDate,
          court_numbers: selectedCourts
        })
      })

      const data = await response.json()

      if (response.ok) {
        setMessage(`Successfully saved ${data.total_cases_saved} cases from ${data.courts_processed} courts`)
        fetchData()
      } else {
        setError(data.detail || 'Failed to fetch court data')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch court data')
    } finally {
      setFetchingCourts(false)
    }
  }

  const toggleCourtSelection = (courtNumber: string) => {
    setSelectedCourts(prev =>
      prev.includes(courtNumber)
        ? prev.filter(c => c !== courtNumber)
        : [...prev, courtNumber]
    )
  }

  const selectAllCourts = () => {
    setSelectedCourts(discoveredCourts.map(c => c.court_number))
  }

  const deselectAllCourts = () => {
    setSelectedCourts([])
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <Navbar />
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Admin Dashboard</h1>
        
        {error && (
          <div style={{ 
            background: '#ffebee', 
            color: '#c62828', 
            padding: '1rem',
            borderRadius: '4px',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}
        
        {message && (
          <div style={{ 
            background: '#e8f5e9', 
            color: '#2e7d32', 
            padding: '1rem',
            borderRadius: '4px',
            marginBottom: '1rem'
          }}>
            {message}
          </div>
        )}
        
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>Loading...</div>
        ) : (
          <>
            <div style={{ 
              background: 'white', 
              padding: '2rem', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              marginBottom: '2rem'
            }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>Scraper Status</h2>
              
              <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                    Select Date to Scrape (Optional)
                  </label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                  />
                </div>
                <button
                  onClick={triggerScraper}
                  disabled={triggering}
                  style={{
                    background: triggering ? '#ccc' : '#2196f3',
                    color: 'white',
                    border: 'none',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '4px',
                    cursor: triggering ? 'not-allowed' : 'pointer',
                    fontWeight: 'bold',
                    height: '46px'
                  }}
                >
                  {triggering ? 'Running Scraper...' : 'Run Scraper Now'}
                </button>
                {triggering && (
                  <button
                    onClick={stopScraper}
                    style={{
                      background: '#d32f2f',
                      color: 'white',
                      border: 'none',
                      padding: '0.75rem 1.5rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 'bold',
                      height: '46px'
                    }}
                  >
                    Stop
                  </button>
                )}
              </div>
              
              {status && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                  <div>
                    <div style={{ color: '#666', fontSize: '0.875rem' }}>Status</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: status.status === 'success' ? '#2e7d32' : '#666' }}>
                      {status.status || 'Never Run'}
                    </div>
                  </div>
                  
                  <div>
                    <div style={{ color: '#666', fontSize: '0.875rem' }}>Last Run</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                      {status.last_run ? new Date(status.last_run).toLocaleString() : 'N/A'}
                    </div>
                  </div>
                  
                  <div>
                    <div style={{ color: '#666', fontSize: '0.875rem' }}>Total Records</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#1976d2' }}>
                      {status.total_records}
                    </div>
                  </div>
                  
                  <div>
                    <div style={{ color: '#666', fontSize: '0.875rem' }}>Last Extraction Count</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                      {status.last_extraction_count}
                    </div>
                  </div>
                </div>
              )}

              {triggering && (
                <div style={{ marginBottom: '1.5rem', background: '#f5f5f5', padding: '1rem', borderRadius: '4px', maxHeight: '300px', overflowY: 'auto' }}>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Live Logs</h3>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>
                    {liveLogs.length > 0 ? liveLogs.join('\n') : 'Waiting for logs...'}
                  </div>
                </div>
              )}
              
              <button
                onClick={triggerScraper}
                disabled={triggering}
                style={{
                  background: '#2e7d32',
                  color: 'white',
                  padding: '0.75rem 2rem',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  cursor: triggering ? 'not-allowed' : 'pointer',
                  opacity: triggering ? 0.6 : 1
                }}
              >
                {triggering ? 'Running Scraper...' : 'Trigger Scraper Manually'}
              </button>
            </div>

            <div style={{ 
              background: 'white', 
              padding: '2rem', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              marginBottom: '2rem'
            }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>Court Discovery</h2>
              <p style={{ marginBottom: '1.5rem', color: '#666' }}>
                Select a date to discover which courts have active cause lists, then fetch the data from those courts.
              </p>
              
              <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                    Select Date for Court Discovery
                  </label>
                  <input
                    type="date"
                    value={discoveryDate}
                    onChange={(e) => setDiscoveryDate(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                  />
                </div>
                <button
                  onClick={discoverCourts}
                  disabled={discovering || !discoveryDate}
                  style={{
                    background: discovering || !discoveryDate ? '#ccc' : '#ff9800',
                    color: 'white',
                    border: 'none',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '4px',
                    cursor: discovering || !discoveryDate ? 'not-allowed' : 'pointer',
                    fontWeight: 'bold',
                    height: '46px'
                  }}
                >
                  {discovering ? 'Discovering...' : 'Discover Courts'}
                </button>
              </div>

              {discoveredCourts.length > 0 && (
                <>
                  <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ fontSize: '1.2rem' }}>
                      Available Courts ({discoveredCourts.length})
                    </h3>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={selectAllCourts}
                        style={{
                          background: '#4caf50',
                          color: 'white',
                          border: 'none',
                          padding: '0.5rem 1rem',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.875rem'
                        }}
                      >
                        Select All
                      </button>
                      <button
                        onClick={deselectAllCourts}
                        style={{
                          background: '#9e9e9e',
                          color: 'white',
                          border: 'none',
                          padding: '0.5rem 1rem',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.875rem'
                        }}
                      >
                        Deselect All
                      </button>
                    </div>
                  </div>

                  <div style={{ 
                    maxHeight: '300px', 
                    overflowY: 'auto', 
                    border: '1px solid #ddd', 
                    borderRadius: '4px',
                    marginBottom: '1.5rem'
                  }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead style={{ position: 'sticky', top: 0, background: '#f5f5f5', zIndex: 1 }}>
                        <tr style={{ borderBottom: '2px solid #ddd' }}>
                          <th style={{ padding: '0.75rem', textAlign: 'left', width: '50px' }}>
                            <input 
                              type="checkbox" 
                              checked={selectedCourts.length === discoveredCourts.length}
                              onChange={() => selectedCourts.length === discoveredCourts.length ? deselectAllCourts() : selectAllCourts()}
                            />
                          </th>
                          <th style={{ padding: '0.75rem', textAlign: 'left' }}>Court</th>
                          <th style={{ padding: '0.75rem', textAlign: 'left' }}>Judge</th>
                        </tr>
                      </thead>
                      <tbody>
                        {discoveredCourts.map((court) => (
                          <tr 
                            key={court.court_number} 
                            style={{ 
                              borderBottom: '1px solid #eee',
                              background: selectedCourts.includes(court.court_number) ? '#e3f2fd' : 'white'
                            }}
                          >
                            <td style={{ padding: '0.75rem' }}>
                              <input
                                type="checkbox"
                                checked={selectedCourts.includes(court.court_number)}
                                onChange={() => toggleCourtSelection(court.court_number)}
                              />
                            </td>
                            <td style={{ padding: '0.75rem', fontWeight: '500' }}>
                              {court.court_name}
                            </td>
                            <td style={{ padding: '0.75rem', color: '#666' }}>
                              {court.judge}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <button
                    onClick={fetchSelectedCourts}
                    disabled={fetchingCourts || selectedCourts.length === 0}
                    style={{
                      background: fetchingCourts || selectedCourts.length === 0 ? '#ccc' : '#2196f3',
                      color: 'white',
                      border: 'none',
                      padding: '0.75rem 2rem',
                      borderRadius: '4px',
                      cursor: fetchingCourts || selectedCourts.length === 0 ? 'not-allowed' : 'pointer',
                      fontWeight: 'bold',
                      fontSize: '1rem'
                    }}
                  >
                    {fetchingCourts 
                      ? 'Fetching Court Data...' 
                      : `Fetch Data from ${selectedCourts.length} Selected Court${selectedCourts.length !== 1 ? 's' : ''}`
                    }
                  </button>
                </>
              )}
            </div>
            
            <div style={{ 
              background: 'white', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              overflow: 'hidden'
            }}>
              <h2 style={{ fontSize: '1.5rem', padding: '1.5rem', borderBottom: '1px solid #eee' }}>Scraper Logs</h2>
              
              {logs.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                  No logs available
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Status</th>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Run Date</th>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Records Extracted</th>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Error Message</th>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Created At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '1rem' }}>
                          <span style={{
                            background: log.status === 'success' ? '#e8f5e9' : '#ffebee',
                            color: log.status === 'success' ? '#2e7d32' : '#c62828',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '12px',
                            fontSize: '0.875rem',
                            fontWeight: '500'
                          }}>
                            {log.status}
                          </span>
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {new Date(log.run_date).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '1rem' }}>{log.records_extracted}</td>
                        <td style={{ padding: '1rem', color: log.error_message ? '#c62828' : '#666' }}>
                          {log.error_message || '-'}
                        </td>
                        <td style={{ padding: '1rem' }}>
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

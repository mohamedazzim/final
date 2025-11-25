'use client'

import { useState, useEffect } from 'react'
import Navbar from '@/components/Navbar'

interface Cause {
  id: number
  sr_no: string | null
  court_no: string | null
  case_no: string | null
  petitioner: string | null
  respondent: string | null
  advocate: string | null
  hearing_date: string | null
  hearing_time: string | null
  case_type: string | null
  is_hrce: boolean
  inserted_at: string
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [caseNo, setCaseNo] = useState('')
  const [advocate, setAdvocate] = useState('')
  const [courtNo, setCourtNo] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [fuzzy, setFuzzy] = useState(false)
  const [hrceOnly, setHrceOnly] = useState(false)
  const [results, setResults] = useState<Cause[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    handleSearch()
  }, [])

  const handleSearch = async () => {
    setLoading(true)
    setError('')
    
    const params = new URLSearchParams()
    if (query) params.append('query', query)
    if (caseNo) params.append('case_no', caseNo)
    if (advocate) params.append('advocate', advocate)
    if (courtNo) params.append('court_no', courtNo)
    if (dateFrom) params.append('hearing_date_from', dateFrom)
    if (dateTo) params.append('hearing_date_to', dateTo)
    if (fuzzy) params.append('fuzzy', 'true')
    if (hrceOnly) params.append('is_hrce', 'true')
    
    try {
      const token = localStorage.getItem('token')
      const fetchInit: RequestInit = {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      }
      const response = await fetch(`/api/proxy/api/cases/search?${params}`, fetchInit)
      
      if (!response.ok) {
        throw new Error('Search failed')
      }
      
      const data = await response.json()
      setResults(data)
    } catch (err: any) {
      setError(err.message || 'Failed to search')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = async () => {
    const params = new URLSearchParams()
    if (query) params.append('query', query)
    if (caseNo) params.append('case_no', caseNo)
    if (advocate) params.append('advocate', advocate)
    if (courtNo) params.append('court_no', courtNo)
    if (dateFrom) params.append('hearing_date_from', dateFrom)
    if (dateTo) params.append('hearing_date_to', dateTo)
    if (hrceOnly) params.append('is_hrce', 'true')
    
    try {
      const token = localStorage.getItem('token')
      const fetchInit: RequestInit = {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      }
      const response = await fetch(`/api/proxy/api/cases/download-pdf?${params}`, fetchInit)
      
      if (!response.ok) throw new Error('Download failed')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'cause_list_results.pdf'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
      setError('Failed to download PDF')
    }
  }

  return (
    <div>
      <Navbar />
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Search Cause Lists</h1>
        
        <div style={{ 
          background: 'white', 
          padding: '2rem', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          marginBottom: '2rem'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>General Search</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search all fields..."
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Case Number</label>
              <input
                type="text"
                value={caseNo}
                onChange={(e) => setCaseNo(e.target.value)}
                placeholder="W.P. No. 1234 of 2024"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Advocate Name</label>
              <input
                type="text"
                value={advocate}
                onChange={(e) => setAdvocate(e.target.value)}
                placeholder="Enter advocate name"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Court Number</label>
              <input
                type="text"
                value={courtNo}
                onChange={(e) => setCourtNo(e.target.value)}
                placeholder="e.g., 1, 2, 3..."
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Hearing Date From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Hearing Date To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem'
                }}
              />
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={fuzzy}
                onChange={(e) => setFuzzy(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <span>Fuzzy Search (typo tolerance)</span>
            </label>
            
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={hrceOnly}
                onChange={(e) => setHrceOnly(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <span>HRCE Cases Only</span>
            </label>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={handleSearch}
              disabled={loading}
              style={{
                background: '#1976d2',
                color: 'white',
                padding: '0.75rem 2rem',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontWeight: 'bold'
              }}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
            
            <button
              onClick={handleDownloadPDF}
              disabled={loading}
              style={{
                background: '#2e7d32',
                color: 'white',
                padding: '0.75rem 2rem',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontWeight: 'bold'
              }}
            >
              Download PDF
            </button>
          </div>

        </div>
        
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
        
        {results.length > 0 && (
          <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '1000px' }}>
              <thead>
                <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Sr. No.</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Case No.</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Court</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Petitioner</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Respondent</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Advocate</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Hearing Date</th>
                  <th style={{ padding: '1rem', textAlign: 'left' }}>Type</th>
                </tr>
              </thead>
              <tbody>
                {results.map((cause) => (
                  <tr 
                    key={cause.id}
                    style={{ 
                      borderBottom: '1px solid #eee',
                      background: cause.is_hrce ? '#fff8e1' : 'white'
                    }}
                  >
                    <td style={{ padding: '1rem' }}>{cause.sr_no || 'N/A'}</td>
                    <td style={{ padding: '1rem' }}>
                      <a href={`/cases/${cause.id}`} style={{ color: '#1976d2', textDecoration: 'none' }}>
                        {cause.case_no || 'N/A'}
                      </a>
                    </td>
                    <td style={{ padding: '1rem' }}>{cause.court_no || 'N/A'}</td>
                    <td style={{ padding: '1rem' }}>{cause.petitioner || 'N/A'}</td>
                    <td style={{ padding: '1rem' }}>{cause.respondent || 'N/A'}</td>
                    <td style={{ padding: '1rem' }}>{cause.advocate || 'N/A'}</td>
                    <td style={{ padding: '1rem' }}>{cause.hearing_date ? new Date(cause.hearing_date).toLocaleDateString() : 'N/A'}</td>
                    <td style={{ padding: '1rem' }}>
                      {cause.is_hrce && (
                        <span style={{
                          background: '#ff9800',
                          color: 'white',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}>
                          HRCE
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {results.length === 0 && !loading && !error && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
            No results found. Try adjusting your search criteria.
          </div>
        )}
      </main>
    </div>
  )
}

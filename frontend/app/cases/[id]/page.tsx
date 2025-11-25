'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
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
  raw_text: string | null
  is_hrce: boolean
  inserted_at: string
}

interface RelatedCase {
  cause: Cause
  similarity_score: number
  match_reason: string
}

export default function CaseDetailsPage() {
  const params = useParams()
  const [cause, setCause] = useState<Cause | null>(null)
  const [relatedCases, setRelatedCases] = useState<RelatedCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchCaseDetails = async () => {
      try {
        const token = localStorage.getItem('token')
        const fetchInit: RequestInit = {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        }
        
        const causeResponse = await fetch(`/api/proxy/api/cases/${params.id}`, fetchInit)
        if (!causeResponse.ok) throw new Error('Failed to fetch case details')
        const causeData = await causeResponse.json()
        setCause(causeData)
        
        const relatedResponse = await fetch(`/api/proxy/api/cases/${params.id}/related`, fetchInit)
        if (relatedResponse.ok) {
          const relatedData = await relatedResponse.json()
          setRelatedCases(relatedData)
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load case details')
      } finally {
        setLoading(false)
      }
    }
    
    if (params.id) {
      fetchCaseDetails()
    }
  }, [params.id])

  if (loading) {
    return (
      <div>
        <Navbar />
        <main style={{ padding: '2rem', textAlign: 'center' }}>Loading...</main>
      </div>
    )
  }

  if (error || !cause) {
    return (
      <div>
        <Navbar />
        <main style={{ padding: '2rem' }}>
          <div style={{ color: '#c62828', background: '#ffebee', padding: '1rem', borderRadius: '4px' }}>
            {error || 'Case not found'}
          </div>
        </main>
      </div>
    )
  }

  return (
    <div>
      <Navbar />
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Case Details</h1>
        
        {cause.is_hrce && (
          <div style={{
            background: '#fff8e1',
            border: '2px solid #ff9800',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '2rem'
          }}>
            <strong style={{ color: '#e65100' }}>HRCE Case:</strong> This case is related to Hindu Religious and Charitable Endowments or temple matters.
          </div>
        )}
        
        <div style={{ 
          background: 'white', 
          padding: '2rem', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          marginBottom: '2rem'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem' }}>
            <div style={{ fontWeight: 'bold' }}>Sr. No.:</div>
            <div>{cause.sr_no || 'N/A'}</div>

            <div style={{ fontWeight: 'bold' }}>Case Number:</div>
            <div>{cause.case_no || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Court Number:</div>
            <div>{cause.court_no || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Petitioner:</div>
            <div>{cause.petitioner || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Respondent:</div>
            <div>{cause.respondent || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Advocate:</div>
            <div>{cause.advocate || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Hearing Date:</div>
            <div>{cause.hearing_date ? new Date(cause.hearing_date).toLocaleDateString() : 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Hearing Time:</div>
            <div>{cause.hearing_time || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Case Type:</div>
            <div>{cause.case_type || 'N/A'}</div>
            
            <div style={{ fontWeight: 'bold' }}>Added On:</div>
            <div>{new Date(cause.inserted_at).toLocaleString()}</div>
          </div>
          
          {cause.raw_text && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>Raw Text:</h3>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: '1rem', 
                borderRadius: '4px',
                whiteSpace: 'pre-wrap',
                fontSize: '0.875rem'
              }}>
                {cause.raw_text}
              </pre>
            </div>
          )}
        </div>
        
        {relatedCases.length > 0 && (
          <div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Related Cases</h2>
            <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Case No.</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Similarity</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Reason</th>
                    <th style={{ padding: '1rem', textAlign: 'left' }}>Hearing Date</th>
                  </tr>
                </thead>
                <tbody>
                  {relatedCases.map((related) => (
                    <tr key={related.cause.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '1rem' }}>
                        <a href={`/cases/${related.cause.id}`} style={{ color: '#1976d2', textDecoration: 'none' }}>
                          {related.cause.case_no || 'N/A'}
                        </a>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {Math.round(related.similarity_score * 100)}%
                      </td>
                      <td style={{ padding: '1rem' }}>{related.match_reason}</td>
                      <td style={{ padding: '1rem' }}>
                        {related.cause.hearing_date ? new Date(related.cause.hearing_date).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

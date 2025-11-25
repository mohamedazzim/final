import Navbar from '@/components/Navbar'

export default function Home() {
  return (
    <div>
      <Navbar />
      <main style={{ padding: '2rem' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Madras High Court Cause List Automation
          </h1>
          <p style={{ fontSize: '1.2rem', color: '#666', marginBottom: '2rem' }}>
            Automated extraction and intelligent search of court cause lists
          </p>
          
          <div style={{ 
            background: 'white', 
            padding: '2rem', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            marginBottom: '2rem'
          }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Features</h2>
            <ul style={{ lineHeight: '2', paddingLeft: '2rem' }}>
              <li>Daily automated scraping of cause lists from Madras High Court</li>
              <li>Advanced search with fuzzy matching for typo tolerance</li>
              <li>HRCE and temple case highlighting</li>
              <li>Related case identification using similarity matching</li>
              <li>Role-based access control (Legal Professional, Court Admin, Superadmin)</li>
              <li>Admin dashboard for scraper management and monitoring</li>
            </ul>
          </div>

          <div style={{ 
            background: '#e3f2fd', 
            padding: '1.5rem', 
            borderRadius: '8px',
            border: '1px solid #2196f3',
            marginBottom: '2rem'
          }}>
            <h3 style={{ color: '#1976d2', marginBottom: '0.5rem', fontSize: '1.2rem' }}>System Status</h3>
            <p style={{ marginBottom: '0.5rem' }}>✓ Frontend running on port 5000</p>
            <p>✓ Backend API running on port 8000</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
            <a href="/search" style={{ 
              background: 'white', 
              padding: '2rem', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              textDecoration: 'none',
              color: 'inherit',
              transition: 'transform 0.2s'
            }}>
              <h3 style={{ color: '#1976d2', marginBottom: '0.5rem' }}>Search Cases</h3>
              <p style={{ color: '#666', fontSize: '0.9rem' }}>Search and filter through court cause lists</p>
            </a>

            <a href="/admin" style={{ 
              background: 'white', 
              padding: '2rem', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              textDecoration: 'none',
              color: 'inherit'
            }}>
              <h3 style={{ color: '#1976d2', marginBottom: '0.5rem' }}>Admin Dashboard</h3>
              <p style={{ color: '#666', fontSize: '0.9rem' }}>Manage scraper and view logs</p>
            </a>

            <a href="/login" style={{ 
              background: 'white', 
              padding: '2rem', 
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              textDecoration: 'none',
              color: 'inherit'
            }}>
              <h3 style={{ color: '#1976d2', marginBottom: '0.5rem' }}>Login</h3>
              <p style={{ color: '#666', fontSize: '0.9rem' }}>Access protected features</p>
            </a>
          </div>
        </div>
      </main>
    </div>
  )
}

'use client'

import Link from 'next/link'

export default function Navbar() {
  return (
    <nav style={{
      background: '#1976d2',
      color: 'white',
      padding: '1rem 2rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link href="/" style={{ 
          fontSize: '1.5rem', 
          fontWeight: 'bold',
          textDecoration: 'none',
          color: 'white'
        }}>
          MHC Cause List
        </Link>
        <div style={{ display: 'flex', gap: '2rem' }}>
          <Link href="/search" style={{ color: 'white', textDecoration: 'none' }}>
            Search
          </Link>
          <Link href="/admin" style={{ color: 'white', textDecoration: 'none' }}>
            Admin
          </Link>
          <Link href="/login" style={{ color: 'white', textDecoration: 'none' }}>
            Login
          </Link>
        </div>
      </div>
    </nav>
  )
}

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Madras High Court Cause List',
  description: 'Search and filter Madras High Court cause lists',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

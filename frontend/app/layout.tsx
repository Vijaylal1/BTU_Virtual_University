import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'BTU Virtual University',
  description: 'Multi-Agentic AI Framework · Dean → Coach → Professor',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

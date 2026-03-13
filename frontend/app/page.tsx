'use client'
import { useState, useEffect, useCallback } from 'react'
import { apiFetch, setApiToken, clearApiToken } from '@/lib/api'
import { User, Panel, ToastData } from '@/lib/types'
import AuthScreen    from '@/components/AuthScreen'
import Sidebar       from '@/components/Sidebar'
import DashboardPanel from '@/components/DashboardPanel'
import ChatPanel     from '@/components/ChatPanel'
import LibraryPanel  from '@/components/LibraryPanel'
import DoubtPanel    from '@/components/DoubtPanel'

export default function Home() {
  const [user, setUser]     = useState<User | null>(null)
  const [panel, setPanel]   = useState<Panel>('dashboard')
  const [toast, setToast]   = useState<ToastData>(null)
  const [booting, setBooting] = useState(true)

  // Restore session on mount
  useEffect(() => {
    const saved = localStorage.getItem('btu_token')
    if (!saved) { setBooting(false); return }
    setApiToken(saved)
    apiFetch<User>('/auth/me')
      .then(setUser)
      .catch(() => { localStorage.removeItem('btu_token'); clearApiToken() })
      .finally(() => setBooting(false))
  }, [])

  const showToast = useCallback((message: string, type: 'success' | 'error') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3500)
  }, [])

  const handleLogin = useCallback((me: User) => { setUser(me); setPanel('dashboard') }, [])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('btu_token')
    clearApiToken()
    setUser(null)
    setPanel('dashboard')
    showToast('Signed out', 'success')
  }, [showToast])

  if (booting) {
    return (
      <div className="h-screen flex items-center justify-center" style={{ background: '#0a0a18' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="text-5xl">🎓</div>
          <div className="text-sm text-bmuted flex items-center gap-2">
            <span className="spinner" /> Loading BTU Virtual University…
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return <AuthScreen onLogin={handleLogin} showToast={showToast} />
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar user={user} panel={panel} onPanelChange={setPanel} onLogout={handleLogout} />

      <main className="flex-1 overflow-hidden min-w-0">
        {panel === 'dashboard' && <DashboardPanel />}
        {panel === 'chat'      && <ChatPanel      showToast={showToast} />}
        {panel === 'library'   && <LibraryPanel   showToast={showToast} />}
        {panel === 'doubt'     && <DoubtPanel      showToast={showToast} />}
      </main>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-sm font-semibold animate-toastIn"
          style={toast.type === 'success'
            ? { background: 'rgba(62,207,142,0.12)', border: '1px solid rgba(62,207,142,0.28)', color: '#3ecf8e' }
            : { background: 'rgba(255,107,107,0.12)', border: '1px solid rgba(255,107,107,0.28)', color: '#ff6b6b' }}>
          {toast.type === 'success' ? '✓ ' : '⚠ '}{toast.message}
        </div>
      )}
    </div>
  )
}

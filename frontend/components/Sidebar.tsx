'use client'
import { Panel, User } from '@/lib/types'

const NAV = [
  { id: 'dashboard', icon: '📊', label: 'Dashboard',      accent: '#4facfe' },
  { id: 'chat',      icon: '💬', label: 'Chat',           accent: '#9b7de0' },
  { id: 'library',   icon: '📚', label: 'Library',        accent: '#3ecf8e' },
  { id: 'doubt',     icon: '🤔', label: 'Doubt Clearing', accent: '#ffd93d' },
] as const

interface Props {
  user: User
  panel: Panel
  onPanelChange: (p: Panel) => void
  onLogout: () => void
}

export default function Sidebar({ user, panel, onPanelChange, onLogout }: Props) {
  const initials = user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

  return (
    <nav className="w-52 flex flex-col flex-shrink-0 h-screen"
      style={{ background: '#0d0d24', borderRight: '1px solid rgba(255,255,255,0.06)' }}>

      {/* Logo */}
      <div className="px-5 py-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="text-sm font-black grad-text">🎓 BTU Virtual</div>
        <div className="text-[0.65rem] text-bmuted mt-0.5">Multi-Agentic AI Framework</div>
      </div>

      {/* Nav items */}
      <div className="flex-1 py-3">
        {NAV.map(n => {
          const active = panel === n.id
          return (
            <button key={n.id} onClick={() => onPanelChange(n.id as Panel)}
              className="w-full flex items-center gap-3 px-5 py-3 text-sm font-medium transition-all text-left"
              style={{
                color:       active ? '#e2e8f0' : '#8892a4',
                background:  active ? `rgba(${hexToRgb(n.accent)},0.1)` : 'transparent',
                borderLeft:  active ? `3px solid ${n.accent}` : '3px solid transparent',
              }}>
              <span className="text-base w-5 text-center">{n.icon}</span>
              {n.label}
            </button>
          )
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-4" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
            style={{ background: 'linear-gradient(135deg,#7c5cbf,#3ecf8e)' }}>
            {initials}
          </div>
          <div className="min-w-0">
            <div className="text-xs font-semibold text-btext truncate">{user.full_name}</div>
            <div className="text-[0.62rem] text-bmuted">Student</div>
          </div>
        </div>
        <button onClick={onLogout}
          className="w-full py-1.5 rounded-lg text-xs font-semibold transition-all"
          style={{ background: 'rgba(255,107,107,0.08)', border: '1px solid rgba(255,107,107,0.18)', color: '#ff6b6b' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,107,107,0.16)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,107,107,0.08)')}>
          Sign Out
        </button>
      </div>
    </nav>
  )
}

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1,3),16)
  const g = parseInt(hex.slice(3,5),16)
  const b = parseInt(hex.slice(5,7),16)
  return `${r},${g},${b}`
}

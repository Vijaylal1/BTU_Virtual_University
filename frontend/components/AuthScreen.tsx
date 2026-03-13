'use client'
import { useState } from 'react'
import { apiFetch, setApiToken } from '@/lib/api'
import { User } from '@/lib/types'

interface Props {
  onLogin: (user: User) => void
  showToast: (msg: string, type: 'success' | 'error') => void
}

export default function AuthScreen({ onLogin, showToast }: Props) {
  const [mode, setMode]       = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPw, setLoginPw]       = useState('')
  const [regName, setRegName]       = useState('')
  const [regEmail, setRegEmail]     = useState('')
  const [regPw, setRegPw]           = useState('')

  const handleLogin = async () => {
    if (!loginEmail || !loginPw) { setError('Please fill in all fields'); return }
    setLoading(true); setError('')
    try {
      const d = await apiFetch<{ access_token: string }>('/auth/login', 'POST', { email: loginEmail, password: loginPw })
      setApiToken(d.access_token)
      localStorage.setItem('btu_token', d.access_token)
      const me = await apiFetch<User>('/auth/me')
      showToast(`Welcome back, ${me.full_name}!`, 'success')
      onLogin(me)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Login failed')
    } finally { setLoading(false) }
  }

  const handleRegister = async () => {
    if (!regName || !regEmail || !regPw) { setError('Please fill in all fields'); return }
    setLoading(true); setError('')
    try {
      const d = await apiFetch<{ access_token: string }>('/auth/register', 'POST', { full_name: regName, email: regEmail, password: regPw })
      setApiToken(d.access_token)
      localStorage.setItem('btu_token', d.access_token)
      const me = await apiFetch<User>('/auth/me')
      showToast(`Welcome to BTU, ${me.full_name}!`, 'success')
      onLogin(me)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Registration failed')
    } finally { setLoading(false) }
  }

  const onKey = (e: React.KeyboardEvent, fn: () => void) => { if (e.key === 'Enter') fn() }

  return (
    <div className="flex h-screen" style={{ background: 'linear-gradient(135deg,#0a0a18 0%,#1a0a3a 55%,#0a1a2a 100%)' }}>

      {/* Brand */}
      <div className="flex-1 flex flex-col justify-center items-center p-14 relative overflow-hidden">
        <div className="absolute w-[500px] h-[500px] rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle,rgba(124,92,191,0.13) 0%,transparent 70%)', top: '50%', left: '50%', transform: 'translate(-50%,-50%)' }} />
        <div className="absolute w-64 h-64 rounded-full pointer-events-none"
          style={{ background: 'rgba(62,207,142,0.07)', filter: 'blur(60px)', bottom: '15%', right: '10%' }} />

        <div className="relative z-10 text-center max-w-xs">
          <div className="text-7xl mb-5">🎓</div>
          <h1 className="text-[2.6rem] font-black leading-tight mb-3 grad-text">
            BTU Virtual<br />University
          </h1>
          <p className="text-bmuted text-sm leading-relaxed mb-8">
            A 3-tier multi-agentic AI framework with 10 specialist professors,
            Agentic RAG, and Socratic learning sessions.
          </p>

          <div className="flex flex-wrap gap-2 justify-center mb-8">
            {[
              ['Claude Opus 4.6','#9b7de0','rgba(124,92,191,0.12)'],
              ['PostgreSQL',     '#3ecf8e','rgba(62,207,142,0.12)'],
              ['FastAPI',        '#4facfe','rgba(79,172,254,0.12)'],
              ['FAISS RAG',      '#ffd93d','rgba(255,217,61,0.12)'],
              ['10 Professors',  '#9b7de0','rgba(155,125,224,0.12)'],
              ['30 Chapters',    '#3ecf8e','rgba(62,207,142,0.12)'],
            ].map(([label,color,bg]) => (
              <span key={label} className="text-xs font-semibold px-3 py-1 rounded-full border"
                style={{ color, background: bg as string, borderColor: (color as string)+'55' }}>
                {label}
              </span>
            ))}
          </div>

          <div className="flex items-center justify-center gap-2 text-xs">
            {[
              ['Dean','#4facfe','rgba(79,172,254,0.1)'],
              ['→','#8892a4','transparent'],
              ['Coach Elias','#3ecf8e','rgba(62,207,142,0.1)'],
              ['→','#8892a4','transparent'],
              ['Professor','#9b7de0','rgba(124,92,191,0.1)'],
            ].map(([t,c,bg],i) => (
              <span key={i} className="px-2 py-1 rounded font-semibold"
                style={{ color: c as string, background: bg as string }}>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="w-[400px] flex flex-col justify-center px-10 py-12 flex-shrink-0"
        style={{ background: 'rgba(13,13,36,0.9)', borderLeft: '1px solid rgba(255,255,255,0.07)' }}>

        {mode === 'login' ? (
          <>
            <h2 className="text-2xl font-bold mb-1">Welcome back</h2>
            <p className="text-bmuted text-sm mb-7">Sign in to continue your journey</p>
            <ErrBox msg={error} />
            <BtuField label="Email">
              <input type="email" value={loginEmail} onChange={e=>setLoginEmail(e.target.value)}
                onKeyDown={e=>onKey(e,handleLogin)} placeholder="you@example.com" />
            </BtuField>
            <BtuField label="Password">
              <input type="password" value={loginPw} onChange={e=>setLoginPw(e.target.value)}
                onKeyDown={e=>onKey(e,handleLogin)} placeholder="••••••••" />
            </BtuField>
            <PrimaryBtn onClick={handleLogin} loading={loading} label="Sign In" loadingLabel="Signing in…" color="#7c5cbf,#5a3f9e" />
            <p className="text-center text-sm text-bmuted mt-5">
              No account?{' '}
              <button onClick={()=>{setMode('register');setError('')}} className="text-blight font-semibold hover:underline">Register</button>
            </p>
          </>
        ) : (
          <>
            <h2 className="text-2xl font-bold mb-1">Create account</h2>
            <p className="text-bmuted text-sm mb-7">Join BTU Virtual University today</p>
            <ErrBox msg={error} />
            <BtuField label="Full Name">
              <input type="text" value={regName} onChange={e=>setRegName(e.target.value)} placeholder="Your full name" />
            </BtuField>
            <BtuField label="Email">
              <input type="email" value={regEmail} onChange={e=>setRegEmail(e.target.value)} placeholder="you@example.com" />
            </BtuField>
            <BtuField label="Password">
              <input type="password" value={regPw} onChange={e=>setRegPw(e.target.value)}
                onKeyDown={e=>onKey(e,handleRegister)} placeholder="••••••••" />
            </BtuField>
            <PrimaryBtn onClick={handleRegister} loading={loading} label="Create Account" loadingLabel="Creating…" color="#7c5cbf,#5a3f9e" />
            <p className="text-center text-sm text-bmuted mt-5">
              Have an account?{' '}
              <button onClick={()=>{setMode('login');setError('')}} className="text-blight font-semibold hover:underline">Sign in</button>
            </p>
          </>
        )}
      </div>
    </div>
  )
}

function ErrBox({ msg }: { msg: string }) {
  if (!msg) return null
  return (
    <div className="mb-4 px-4 py-3 rounded-xl text-sm text-bcoral"
      style={{ background: 'rgba(255,107,107,0.07)', border: '1px solid rgba(255,107,107,0.22)' }}>
      {msg}
    </div>
  )
}

function BtuField({ label, children }: { label: string; children: React.ReactElement }) {
  return (
    <div className="mb-4 [&_input]:w-full [&_input]:px-4 [&_input]:py-3 [&_input]:rounded-xl [&_input]:text-sm [&_input]:text-btext [&_input]:outline-none [&_input]:transition-all"
      style={{ '--inp-bg': 'rgba(255,255,255,0.04)', '--inp-border': 'rgba(255,255,255,0.09)' } as React.CSSProperties}>
      <label className="block text-[0.7rem] font-bold text-bmuted uppercase tracking-widest mb-1.5">{label}</label>
      <style jsx>{`
        div :global(input) {
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.09);
        }
        div :global(input:focus) {
          border-color: #7c5cbf;
          background: rgba(124,92,191,0.06);
        }
      `}</style>
      {children}
    </div>
  )
}

function PrimaryBtn({ onClick, loading, label, loadingLabel, color }: {
  onClick: () => void; loading: boolean; label: string; loadingLabel: string; color: string
}) {
  return (
    <button onClick={onClick} disabled={loading}
      className="w-full py-3 rounded-xl font-semibold text-white mt-1 transition-opacity disabled:opacity-50 hover:opacity-90 active:scale-[0.98]"
      style={{ background: `linear-gradient(135deg, ${color})` }}>
      {loading ? <><span className="spinner align-middle mr-2" />{loadingLabel}</> : label}
    </button>
  )
}

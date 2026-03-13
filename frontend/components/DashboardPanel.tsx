'use client'

const STATS = [
  { icon: '🤖', value: '3',    label: 'Tiers (Dean → Coach → Prof)', top: 'linear-gradient(90deg,#7c5cbf,#9b7de0)' },
  { icon: '👩‍🏫', value: '10',   label: 'Specialist Professors',       top: 'linear-gradient(90deg,#3ecf8e,#2eaf74)' },
  { icon: '📖', value: '30',   label: 'Chapters · 10 P\'s of Business', top: 'linear-gradient(90deg,#ffd93d,#f0c930)' },
  { icon: '🧠', value: 'RAG',  label: 'Agentic Multi-Round Retrieval', top: 'linear-gradient(90deg,#4facfe,#3a8fe0)' },
]

const PROFESSORS = [
  { name: 'Prof. Priya Place',       chapters: 'Ch. 1–3  · Place',       icon: '🏬', active: true,  grad: 'linear-gradient(135deg,#7c5cbf,#9b7de0)' },
  { name: 'Prof. Maya People',       chapters: 'Ch. 4–6  · People',      icon: '👥', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Sam Process',       chapters: 'Ch. 7–9  · Process',     icon: '⚙️', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Pablo Positioning', chapters: 'Ch. 10–12 · Positioning', icon: '🎯', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Leila Performance', chapters: 'Ch. 13–15 · Performance', icon: '📈', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Dana Platform',     chapters: 'Ch. 16–18 · Platform',   icon: '💻', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Marcus Pricing',    chapters: 'Ch. 19–21 · Pricing',    icon: '💰', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Iris Purpose',      chapters: 'Ch. 22–24 · Purpose',    icon: '🌟', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Lucas Policy',      chapters: 'Ch. 25–27 · Policy',     icon: '📋', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
  { name: 'Prof. Petra Profit',      chapters: 'Ch. 28–30 · Profit',     icon: '💹', active: false, grad: 'linear-gradient(135deg,#2a2a4a,#3a3a6a)' },
]

export default function DashboardPanel() {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="text-lg font-bold">📊 Dashboard</div>
        <span className="text-xs font-bold px-3 py-1 rounded-full"
          style={{ background: 'rgba(79,172,254,0.1)', color: '#4facfe', border: '1px solid rgba(79,172,254,0.2)' }}>
          BTU VU
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 py-6">

        {/* Stat cards */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
          {STATS.map(s => (
            <div key={s.label} className="rounded-2xl p-5 relative overflow-hidden"
              style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.07)' }}>
              <div className="absolute top-0 left-0 right-0 h-[3px] rounded-t-2xl" style={{ background: s.top }} />
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="text-3xl font-black text-btext">{s.value}</div>
              <div className="text-xs text-bmuted mt-1 leading-snug">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Intent types */}
        <div className="mb-8">
          <SectionTitle>Intent Types Handled</SectionTitle>
          <div className="flex flex-wrap gap-2">
            {['domain','cross_p','nav','motivation','ceremony','sprint','wheel','library','doubt'].map(intent => (
              <span key={intent} className="text-xs font-mono font-semibold px-3 py-1.5 rounded-lg"
                style={{ background: 'rgba(124,92,191,0.1)', border: '1px solid rgba(124,92,191,0.22)', color: '#9b7de0' }}>
                {intent}
              </span>
            ))}
          </div>
        </div>

        {/* Professors grid */}
        <div>
          <SectionTitle>10 Specialist Professors</SectionTitle>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {PROFESSORS.map(p => (
              <div key={p.name} className="flex items-center gap-3 p-4 rounded-2xl transition-all"
                style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.07)' }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0"
                  style={{ background: p.grad }}>
                  {p.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-btext truncate">{p.name}</div>
                  <div className="text-[0.68rem] text-bmuted">{p.chapters}</div>
                </div>
                {p.active ? (
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: '#3ecf8e', boxShadow: '0 0 6px #3ecf8e' }} />
                ) : (
                  <div className="w-2 h-2 rounded-full flex-shrink-0 bg-white/10" />
                )}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[0.68rem] font-bold text-bmuted uppercase tracking-widest mb-3">{children}</div>
  )
}

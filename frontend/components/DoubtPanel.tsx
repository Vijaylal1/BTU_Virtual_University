'use client'
import { useState } from 'react'
import { apiFetch } from '@/lib/api'
import { DoubtResult } from '@/lib/types'

interface Props {
  showToast: (msg: string, type: 'success' | 'error') => void
}

function formatText(text: string) {
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/\n/g,'<br/>')
}

export default function DoubtPanel({ showToast }: Props) {
  const [question, setQuestion]   = useState('')
  const [chapter, setChapter]     = useState('')
  const [result, setResult]       = useState<DoubtResult | null>(null)
  const [loading, setLoading]     = useState(false)

  const submit = async (q?: string) => {
    const q_ = (q ?? question).trim()
    if (!q_ || loading) return
    if (q) setQuestion(q)
    setLoading(true); setResult(null)
    const payload: Record<string, unknown> = { doubt_question: q_ }
    if (chapter) payload.chapter_hint = parseInt(chapter)
    try {
      const resp = await apiFetch<DoubtResult>('/doubt', 'POST', payload)
      setResult(resp)
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Request failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const SAMPLES = [
    { q: 'How does footfall analysis work?',           ch: '2' },
    { q: 'What is the difference between price and value?', ch: '19' },
    { q: 'Why is brand purpose important?',            ch: '22' },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="text-lg font-bold">🤔 Doubt Clearing Session</div>
        <span className="text-xs font-bold px-3 py-1 rounded-full"
          style={{ background: 'rgba(255,217,61,0.1)', color: '#ffd93d', border: '1px solid rgba(255,217,61,0.22)' }}>
          Socratic · Direct to Professor
        </span>
      </div>

      {/* Form */}
      <div className="px-8 py-5 flex-shrink-0" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex gap-3 items-end">
          {/* Question input */}
          <div className="flex-1">
            <label className="block text-[0.7rem] font-bold text-bmuted uppercase tracking-widest mb-1.5">Your Doubt</label>
            <input type="text" value={question} onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && submit()}
              placeholder="e.g. How does footfall analysis work?"
              className="w-full px-4 py-3 rounded-xl text-sm text-btext outline-none transition-all"
              style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.09)' }}
              onFocus={e => (e.target.style.borderColor = '#ffd93d')}
              onBlur={e  => (e.target.style.borderColor = 'rgba(255,255,255,0.09)')} />
          </div>
          {/* Chapter hint */}
          <div>
            <label className="block text-[0.7rem] font-bold text-bmuted uppercase tracking-widest mb-1.5">Chapter</label>
            <input type="number" min={1} max={30} value={chapter} onChange={e => setChapter(e.target.value)}
              placeholder="1–30"
              className="w-20 px-3 py-3 rounded-xl text-sm text-btext text-center outline-none transition-all"
              style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.09)' }}
              onFocus={e => (e.target.style.borderColor = '#ffd93d')}
              onBlur={e  => (e.target.style.borderColor = 'rgba(255,255,255,0.09)')} />
          </div>
          {/* Submit */}
          <button onClick={() => submit()} disabled={loading || !question.trim()}
            className="px-5 py-3 rounded-xl font-bold text-sm transition-all disabled:opacity-40 flex-shrink-0 whitespace-nowrap"
            style={{ background: 'linear-gradient(135deg,#ffd93d,#f0c930)', color: '#1a1400' }}
            onMouseEnter={e => !loading && (e.currentTarget.style.opacity='0.85')}
            onMouseLeave={e => (e.currentTarget.style.opacity='1')}>
            {loading ? <span className="spinner" style={{ borderTopColor: '#1a1400' }} /> : 'Ask Professor'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {!result && !loading && (
          <div className="flex flex-col items-center justify-center text-center text-bmuted py-16 animate-fadeUp">
            <div className="text-5xl mb-4 opacity-40">🤔</div>
            <div className="font-semibold text-btext mb-1">Ask a professor directly</div>
            <div className="text-sm mb-8">Bypass Dean and Coach — go straight to the specialist.<br />Get a Socratic explanation with follow-up questions.</div>
            <div className="flex flex-col gap-2 w-full max-w-lg">
              {SAMPLES.map(s => (
                <button key={s.q} onClick={() => { setQuestion(s.q); setChapter(s.ch); submit(s.q) }}
                  className="text-sm px-4 py-3 rounded-xl text-left transition-all"
                  style={{ background: 'rgba(255,217,61,0.06)', border: '1px solid rgba(255,217,61,0.15)', color: '#ffd93d' }}
                  onMouseEnter={e => (e.currentTarget.style.background='rgba(255,217,61,0.12)')}
                  onMouseLeave={e => (e.currentTarget.style.background='rgba(255,217,61,0.06)')}>
                  💭 {s.q} <span className="opacity-50 ml-1">(Ch. {s.ch})</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center text-center py-20 animate-fadeUp">
            <div className="text-4xl mb-4">🎓</div>
            <div className="text-sm text-bmuted">Consulting the professor…</div>
            <div className="flex gap-1 mt-4">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}

        {result && (
          <div className="animate-fadeUp">
            <div className="rounded-2xl overflow-hidden mb-4"
              style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.07)' }}>
              {/* Card header */}
              <div className="px-5 py-3 flex items-center justify-between"
                style={{ background: 'rgba(255,217,61,0.06)', borderBottom: '1px solid rgba(255,217,61,0.12)' }}>
                <div className="flex items-center gap-2">
                  <span className="text-base">🎓</span>
                  <span className="text-sm font-bold" style={{ color: '#ffd93d' }}>
                    {result.professor_id?.replace(/_/g, ' ').replace('professor ', 'Prof. ') || 'Professor'}
                  </span>
                </div>
                {result.latency_ms && (
                  <span className="text-xs text-bmuted">{result.latency_ms}ms</span>
                )}
              </div>

              {/* Explanation */}
              <div className="px-5 py-5 text-sm leading-7 text-btext bubble-content"
                dangerouslySetInnerHTML={{ __html: formatText(result.explanation) }} />

              {/* Suggested chapters */}
              {result.suggested_chapters?.length > 0 && (
                <div className="px-5 pb-4 flex flex-wrap gap-2">
                  {result.suggested_chapters.map(c => (
                    <span key={c} className="text-[0.68rem] font-semibold px-2.5 py-1 rounded-lg"
                      style={{ background: 'rgba(255,217,61,0.08)', border: '1px solid rgba(255,217,61,0.2)', color: '#ffd93d' }}>
                      Ch. {c}
                    </span>
                  ))}
                </div>
              )}

              {/* Follow-up questions */}
              {result.follow_up_questions?.length > 0 && (
                <div className="px-5 pb-5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="text-[0.68rem] font-bold text-bmuted uppercase tracking-widest mt-4 mb-3">
                    Follow-up questions to deepen your understanding
                  </div>
                  <div className="flex flex-col gap-2">
                    {result.follow_up_questions.map((fq, i) => (
                      <button key={i}
                        onClick={() => { setQuestion(fq); setResult(null) }}
                        className="text-sm px-4 py-3 rounded-xl text-left transition-all"
                        style={{ background: 'rgba(255,217,61,0.04)', border: '1px solid rgba(255,217,61,0.12)', color: '#c4a832' }}
                        onMouseEnter={e => { e.currentTarget.style.background='rgba(255,217,61,0.1)'; e.currentTarget.style.color='#ffd93d' }}
                        onMouseLeave={e => { e.currentTarget.style.background='rgba(255,217,61,0.04)'; e.currentTarget.style.color='#c4a832' }}>
                        💭 {fq}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <button onClick={() => { setResult(null); setQuestion(''); setChapter('') }}
              className="text-xs text-bmuted hover:text-btext transition-colors">
              ← Ask another question
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

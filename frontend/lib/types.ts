export interface User {
  student_id: string
  email: string
  full_name: string
}

export interface ChatMsg {
  id: string
  role: 'user' | 'assistant'
  text: string
  source_agent?: string
  thinking?: string
  latency_ms?: number
  rag_chunks?: number
}

export interface LibraryResult {
  answer: string
  chapters_hit: number[]
  rag_rounds: number
  latency_ms?: number
}

export interface DoubtResult {
  explanation: string
  follow_up_questions: string[]
  suggested_chapters: number[]
  professor_id: string
  latency_ms?: number
}

export type Panel = 'dashboard' | 'chat' | 'library' | 'doubt'

export type ToastData = { message: string; type: 'success' | 'error' } | null

/**
 * SP3CT3R Global State — Zustand store
 * Manages scan sessions, results, terminal logs, and WebSocket state
 */
import { create } from 'zustand'

export const useScanStore = create((set, get) => ({
  // Active scan state
  activeScanId:   null,
  target:         '',
  activeModule:   'domain',
  scanStatus:     'idle',   // idle | running | completed | failed
  progress:       0,
  found:          0,
  totalSources:   0,
  elapsed:        0,
  riskLevel:      'info',

  // Results
  results:        [],
  summary:        {},

  // Terminal logs
  logs:           [],

  // Scan history
  history:        [],

  // WebSocket ref
  wsRef:          null,
  elapsedTimer:   null,

  // ── Actions ──────────────────────────────────────────────

  setTarget:        (t)    => set({ target: t }),
  setActiveModule:  (m)    => set({ activeModule: m }),

  startScan: (scanId, target, module) => {
    // Clear previous state
    const timer = setInterval(() => {
      set(s => ({ elapsed: s.elapsed + 1 }))
    }, 1000)

    set({
      activeScanId: scanId,
      target,
      activeModule: module,
      scanStatus: 'running',
      progress: 0,
      found: 0,
      results: [],
      logs: [],
      summary: {},
      elapsed: 0,
      elapsedTimer: timer,
    })
  },

  completeScan: (summary) => {
    const { elapsedTimer } = get()
    if (elapsedTimer) clearInterval(elapsedTimer)
    set({ scanStatus: 'completed', progress: 100, summary, elapsedTimer: null })
  },

  failScan: () => {
    const { elapsedTimer } = get()
    if (elapsedTimer) clearInterval(elapsedTimer)
    set({ scanStatus: 'failed', elapsedTimer: null })
  },

  updateProgress: (progress, found, total) =>
    set({ progress, found, totalSources: total }),

  addResult: (result) =>
    set(s => ({
      results: [...s.results, { ...result, id: Date.now() + Math.random() }],
      found: s.found + (result.status === 'found' || result.status === 'exposed' || result.status === 'live' ? 1 : 0),
    })),

  addLog: (level, message) =>
    set(s => ({
      logs: [...s.logs.slice(-200), {  // keep last 200 lines
        id: Date.now() + Math.random(),
        level, message,
        time: new Date().toLocaleTimeString('en-US', { hour12: false }),
      }]
    })),

  setWsRef: (ws) => set({ wsRef: ws }),

  resetScan: () => {
    const { elapsedTimer } = get()
    if (elapsedTimer) clearInterval(elapsedTimer)
    set({
      activeScanId: null, scanStatus: 'idle', progress: 0, found: 0,
      results: [], logs: [], summary: {}, elapsed: 0, elapsedTimer: null,
    })
  },

  addToHistory: (scan) =>
    set(s => ({ history: [scan, ...s.history].slice(0, 50) })),
}))
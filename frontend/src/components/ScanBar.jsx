import React, { useState, useRef } from 'react'
import { useScanStore } from '../store/scanStore'
import { startScan } from '../services/api'
import { detectModule, MODULE_COLORS } from '../utils/helpers'
import { useWebSocket } from '../hooks/useWebSocket'

const MODULES = ['domain','email','username','ip','phone','person']

export default function ScanBar() {
  const { activeModule, setActiveModule, target, setTarget, startScan: storeStart, scanStatus } = useScanStore()
  const [loading, setLoading] = useState(false)
  const [activeScanId, setActiveScanId] = useState(null)
  const { connect } = useWebSocket(null)
  const inputRef = useRef()

  const handleInput = (e) => {
    const val = e.target.value
    setTarget(val)
    // Auto-detect module
    if (val.length > 3) {
      const detected = detectModule(val)
      setActiveModule(detected)
    }
  }

  const handleScan = async () => {
    if (!target.trim() || loading || scanStatus === 'running') return
    setLoading(true)
    try {
      const res = await startScan(target.trim(), activeModule)
      const { scan_id } = res.data
      storeStart(scan_id, target.trim(), activeModule)
      setActiveScanId(scan_id)
      connect(scan_id)
    } catch (err) {
      console.error('Scan start failed:', err)
      useScanStore.getState().addLog('ERROR', 'Failed to start scan — is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => { if (e.key === 'Enter') handleScan() }

  return (
    <div style={{ padding:'12px 20px', background:'#050d14', borderBottom:'1px solid #0d2438', display:'flex', gap:10, alignItems:'center', flexShrink:0 }}>
      {/* Module chips */}
      <div style={{ display:'flex', gap:4 }}>
        {MODULES.map(m => {
          const active = activeModule === m
          const col = MODULE_COLORS[m]
          return (
            <div key={m} onClick={() => setActiveModule(m)}
              style={{
                padding:'5px 12px', fontFamily:'Share Tech Mono,monospace', fontSize:10,
                letterSpacing:1, border:`1px solid ${active ? col : '#0d2438'}`,
                background: active ? `${col}14` : 'none',
                color: active ? col : '#5a8ba8',
                cursor:'pointer', transition:'all .15s', textTransform:'uppercase',
              }}>
              {m}
            </div>
          )
        })}
      </div>

      {/* Search input */}
      <div style={{ flex:1, display:'flex', alignItems:'center', border:'1px solid #0f3a5a', background:'#0b1520', padding:'0 14px', gap:10, position:'relative', overflow:'hidden', height:38 }}>
        <div style={{ position:'absolute', left:0, top:0, bottom:0, width:2, background:'#00d4ff', boxShadow:'0 0 10px #00d4ff' }}/>
        <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:12, color:'#00d4ff', whiteSpace:'nowrap' }}>TARGET://</span>
        <input ref={inputRef} value={target} onChange={handleInput} onKeyDown={handleKey}
          placeholder="Enter domain, IP, email, username, phone..."
          style={{ flex:1, background:'none', border:'none', outline:'none', fontFamily:'Share Tech Mono,monospace', fontSize:13, color:'#c8e6f5', caretColor:'#00d4ff' }}
        />
        {target && <span onClick={() => setTarget('')} style={{ color:'#2a4a62', cursor:'pointer', fontSize:12 }}>✕</span>}
      </div>

      {/* Execute button */}
      <button onClick={handleScan} disabled={loading || scanStatus === 'running' || !target.trim()}
        style={{
          padding:'9px 28px', background: (loading || scanStatus==='running') ? '#0d2438' : '#00d4ff',
          border:'none', color: (loading || scanStatus==='running') ? '#5a8ba8' : '#020408',
          fontFamily:'Orbitron,monospace', fontSize:11, fontWeight:700, letterSpacing:2,
          cursor: (loading || scanStatus==='running') ? 'not-allowed' : 'pointer',
          textTransform:'uppercase', clipPath:'polygon(10px 0%,100% 0%,calc(100% - 10px) 100%,0% 100%)',
          boxShadow: (loading || scanStatus==='running') ? 'none' : '0 0 20px rgba(0,212,255,0.35)',
          transition:'all .2s', whiteSpace:'nowrap',
        }}>
        {loading ? '...' : scanStatus === 'running' ? 'SCANNING' : 'EXECUTE'}
      </button>
    </div>
  )
}




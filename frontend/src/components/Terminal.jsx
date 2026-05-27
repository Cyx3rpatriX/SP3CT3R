import React, { useEffect, useRef, useState } from 'react'
import { useScanStore } from '../store/scanStore'
import { LOG_COLORS } from '../utils/helpers'

export default function Terminal() {
  const { logs, addLog, activeScanId } = useScanStore()
  const [cmd, setCmd] = useState('')
  const bottomRef = useRef()
  const inputRef = useRef()

  // Auto-scroll to bottom on new log
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleCommand = (e) => {
    if (e.key !== 'Enter' || !cmd.trim()) return
    addLog('INFO', `> ${cmd}`)
    // Basic built-in commands
    const parts = cmd.trim().split(' ')
    switch(parts[0]) {
      case 'clear': useScanStore.setState({ logs: [] }); break
      case 'help':  addLog('DATA', 'Commands: clear, help, status, scan <target>'); break
      case 'status': addLog('INFO', `Scan: ${useScanStore.getState().scanStatus} | Found: ${useScanStore.getState().found}`); break
      default: addLog('WARN', `Unknown command: ${parts[0]}. Type 'help' for commands.`)
    }
    setCmd('')
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', background:'#080f18', overflow:'hidden', height:'100%' }}>
      {/* Header */}
      <div style={{ padding:'10px 16px', background:'#050d14', borderBottom:'1px solid #0d2438', display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
        <div style={{ width:6, height:6, borderRadius:'50%', background:'#00ff9d', boxShadow:'0 0 8px #00ff9d' }}/>
        <span style={{ fontFamily:'Orbitron,monospace', fontSize:10, fontWeight:600, letterSpacing:2, textTransform:'uppercase', color:'#5a8ba8' }}>Live Terminal Feed</span>
        <span style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>[STDOUT] {activeScanId ? `SCAN:${activeScanId.slice(0,8)}` : 'IDLE'}</span>
      </div>

      {/* Log output */}
      <div style={{ flex:1, overflowY:'auto', padding:'10px 16px', fontFamily:'Share Tech Mono,monospace', fontSize:11, lineHeight:1.8 }}>
        {logs.length === 0 && (
          <div style={{ color:'#2a4a62' }}>SP3CT3R terminal ready. Enter a target above to begin scan.</div>
        )}
        {logs.map(log => (
          <div key={log.id} style={{ display:'flex', gap:10, animationName:'slide-in', animationDuration:'.2s' }}>
            <span style={{ color:'#2a4a62', flexShrink:0 }}>{log.time}</span>
            <span style={{ color: LOG_COLORS[log.level] || '#5a8ba8', flexShrink:0 }}>[{log.level}]</span>
            <span style={{ color: log.level === 'OK' ? '#00ff9d' : log.level === 'ERROR' ? '#ff2d55' : log.level === 'WARN' ? '#ffaa00' : log.level === 'DATA' ? '#a855f7' : '#5a8ba8' }}>
              {log.message}
            </span>
          </div>
        ))}
        <div ref={bottomRef}/>
      </div>

      {/* Command input */}
      <div style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 16px', borderTop:'1px solid #0d2438', flexShrink:0 }}>
        <span style={{ color:'#00ff9d', fontFamily:'Share Tech Mono,monospace', fontSize:12, flexShrink:0 }}>sp3ct3r ›</span>
        <input ref={inputRef} value={cmd} onChange={e => setCmd(e.target.value)} onKeyDown={handleCommand}
          placeholder="Type a command (help, clear, status)..."
          style={{ flex:1, background:'none', border:'none', outline:'none', fontFamily:'Share Tech Mono,monospace', fontSize:12, color:'#c8e6f5', caretColor:'#00ff9d' }}
        />
        <span className="animate-blink" style={{ display:'inline-block', width:8, height:14, background:'#00ff9d' }}/>
      </div>
    </div>
  )
}
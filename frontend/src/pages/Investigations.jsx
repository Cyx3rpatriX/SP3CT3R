import React from 'react'
import { useScanStore } from '../store/scanStore'
import { MODULE_ICONS, RISK_COLORS, formatElapsed } from '../utils/helpers'

export default function Investigations() {
  const { history } = useScanStore()

  return (
    <div style={{ flex:1, overflow:'auto', padding:24, background:'#020408' }}>
      <div style={{ marginBottom:24 }}>
        <h1 style={{ fontFamily:'Orbitron,monospace', fontSize:18, color:'#00d4ff', letterSpacing:3, textShadow:'0 0 16px rgba(0,212,255,.4)', marginBottom:4 }}>INVESTIGATIONS</h1>
        <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#2a4a62' }}>Scan history and saved intelligence profiles</div>
      </div>

      {history.length === 0 ? (
        <div style={{ textAlign:'center', padding:'80px 20px', color:'#2a4a62' }}>
          <div style={{ fontSize:48, marginBottom:16, opacity:.2 }}>📁</div>
          <div style={{ fontFamily:'Orbitron,monospace', fontSize:12, letterSpacing:2, marginBottom:8 }}>NO INVESTIGATIONS YET</div>
          <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11 }}>Complete scans will appear here for review</div>
        </div>
      ) : (
        <div>
          {history.map((scan, i) => (
            <div key={i} style={{ background:'#0b1520', border:'1px solid #0d2438', padding:16, marginBottom:8, display:'flex', alignItems:'center', gap:16, cursor:'pointer' }}>
              <div style={{ fontSize:24 }}>{MODULE_ICONS[scan.module] || '🔍'}</div>
              <div style={{ flex:1 }}>
                <div style={{ fontFamily:'Orbitron,monospace', fontSize:12, color:'#00d4ff', marginBottom:4 }}>{scan.target}</div>
                <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#5a8ba8' }}>{scan.module?.toUpperCase()} · {scan.found} findings</div>
              </div>
              <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>{new Date(scan.time).toLocaleString()}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
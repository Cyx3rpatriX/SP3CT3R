import React from 'react'
import { useScanStore } from '../store/scanStore'
import { formatElapsed } from '../utils/helpers'

export default function StatusBar() {
  const { scanStatus, target, activeModule, progress, found, totalSources, elapsed, activeScanId } = useScanStore()

  const bars = Math.round(progress / 10)
  const progressStr = '▓'.repeat(bars) + '░'.repeat(10 - bars)

  return (
    <>
      {/* Progress bar */}
      <div style={{ height:2, background:'#0d2438', position:'relative', flexShrink:0 }}>
        <div style={{
          height:'100%', width:`${progress}%`,
          background:'linear-gradient(90deg,#00d4ff,#00ff9d)',
          boxShadow:'0 0 10px rgba(0,212,255,0.5)',
          transition:'width .4s ease', position:'relative', overflow:'hidden',
        }}>
          {scanStatus === 'running' && (
            <div style={{ position:'absolute', right:0, top:0, bottom:0, width:30, background:'linear-gradient(90deg,transparent,rgba(255,255,255,.5))' }} className="animate-shimmer"/>
          )}
        </div>
      </div>

      {/* Status strip */}
      <div style={{ padding:'6px 20px', background:'rgba(0,13,20,.97)', borderBottom:'1px solid #0d2438', display:'flex', alignItems:'center', gap:20, flexShrink:0 }}>
        {/* Status label */}
        <div style={{ display:'flex', alignItems:'center', gap:6, fontFamily:'Share Tech Mono,monospace', fontSize:10, color: scanStatus==='running' ? '#00d4ff' : scanStatus==='completed' ? '#00ff9d' : scanStatus==='failed' ? '#ff2d55' : '#5a8ba8', letterSpacing:1 }}>
          {scanStatus === 'running' && <span className="animate-spin-fast" style={{ fontSize:12 }}>◈</span>}
          {scanStatus === 'completed' && <span>✓</span>}
          {scanStatus === 'failed' && <span>✗</span>}
          {scanStatus === 'idle' && <span>◉</span>}
          <span>
            {scanStatus === 'idle'      && 'READY — Enter a target above'}
            {scanStatus === 'running'   && `SCANNING — ${target}`}
            {scanStatus === 'completed' && `COMPLETE — ${target}`}
            {scanStatus === 'failed'    && `FAILED — ${target}`}
          </span>
        </div>

        {scanStatus !== 'idle' && <>
          <Stat label="Module"  value={activeModule?.toUpperCase()} />
          <Stat label="Found"   value={found} color="#00ff9d" />
          <Stat label="Sources" value={totalSources || '—'} />
          <Stat label="Elapsed" value={formatElapsed(elapsed)} />
          {scanStatus === 'running' && (
            <div style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#00ff9d' }}>
              {Math.round(progress)}% {progressStr}
            </div>
          )}
        </>}
      </div>
    </>
  )
}

function Stat({ label, value, color }) {
  return (
    <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#5a8ba8' }}>
      {label}: <span style={{ color: color || '#c8e6f5' }}>{value}</span>
    </div>
  )
}
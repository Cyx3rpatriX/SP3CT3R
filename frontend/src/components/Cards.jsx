import React from 'react'
import { useScanStore } from '../store/scanStore'
import { MODULE_ICONS, RISK_COLORS } from '../utils/helpers'

const RISK_LABEL = { critical:'CRITICAL', high:'HIGH RISK', medium:'MED RISK', low:'LOW RISK', info:'INFO' }
const RISK_BG    = { critical:'rgba(255,45,85,.15)', high:'rgba(255,45,85,.1)', medium:'rgba(255,170,0,.08)', low:'rgba(0,212,255,.06)', info:'rgba(42,74,98,.1)' }

export function TargetCard() {
  const { target, activeModule, results, riskLevel, summary } = useScanStore()
  if (!target) return null

  const found    = results.filter(r => ['found','live'].includes(r.status)).length
  const exposed  = results.filter(r => r.status === 'exposed').length
  const partial  = results.filter(r => r.status === 'partial').length
  const risk     = riskLevel || 'info'

  const subdomains = results.filter(r => r.category === 'subdomain').length
  const ports      = results.filter(r => r.category === 'port').length
  const breaches   = results.filter(r => r.category === 'breach').length
  const socials    = results.filter(r => r.category === 'social' && r.status === 'found').length

  return (
    <div style={{ background:'#0b1520', border:'1px solid #0f3a5a', padding:16, marginBottom:16, position:'relative', overflow:'hidden', flexShrink:0 }}>
      {/* Top gradient bar */}
      <div style={{ position:'absolute', top:0, left:0, right:0, height:2, background:'linear-gradient(90deg,#00d4ff,#00ff9d)' }}/>

      <div style={{ display:'flex', alignItems:'center', gap:14, marginBottom:14 }}>
        {/* Avatar */}
        <div style={{ width:48, height:48, border:'2px solid #00d4ff', background:'#050d14', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20, boxShadow:'0 0 20px rgba(0,212,255,.35)', flexShrink:0, position:'relative' }}>
          <div style={{ position:'absolute', inset:-4, border:'1px solid rgba(0,212,255,.2)' }} className="animate-spin-slow"/>
          {MODULE_ICONS[activeModule] || '🔍'}
        </div>

        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62', letterSpacing:2, textTransform:'uppercase', marginBottom:4 }}>Target Identified</div>
          <div style={{ fontFamily:'Orbitron,monospace', fontSize:14, fontWeight:700, color:'#00d4ff', textShadow:'0 0 12px rgba(0,212,255,.5)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{target}</div>
          <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#5a8ba8', marginTop:3 }}>Module: {activeModule?.toUpperCase()} · {results.length} findings</div>
        </div>

        {/* Risk badge */}
        <div style={{ padding:'4px 12px', fontFamily:'Orbitron,monospace', fontSize:9, fontWeight:700, letterSpacing:2, border:`1px solid ${RISK_COLORS[risk]}`, color:RISK_COLORS[risk], background:RISK_BG[risk], boxShadow:`0 0 12px ${RISK_COLORS[risk]}44`, flexShrink:0, textTransform:'uppercase' }}>
          {RISK_LABEL[risk]}
        </div>
      </div>

      {/* Stat boxes */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
        {[
          { num: subdomains || found, label:'Subdomains', col:'#00d4ff' },
          { num: ports,              label:'Open Ports', col:'#00ff9d' },
          { num: breaches,           label:'Breaches',   col:'#ffaa00' },
          { num: exposed,            label:'Exposed',    col:'#ff2d55' },
        ].map(s => (
          <div key={s.label} style={{ background:'#050d14', border:'1px solid #0d2438', padding:'10px 12px', textAlign:'center' }}>
            <div style={{ fontFamily:'Orbitron,monospace', fontSize:20, fontWeight:700, color:s.col, lineHeight:1, marginBottom:4 }}>{s.num}</div>
            <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:8, letterSpacing:1.5, color:'#5a8ba8', textTransform:'uppercase' }}>{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function StatBox({ num, label, color }) {
  return (
    <div style={{ background:'#050d14', border:'1px solid #0d2438', padding:'10px 12px', textAlign:'center' }}>
      <div style={{ fontFamily:'Orbitron,monospace', fontSize:20, fontWeight:700, color, lineHeight:1, marginBottom:4 }}>{num}</div>
      <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:8, letterSpacing:1.5, color:'#5a8ba8', textTransform:'uppercase' }}>{label}</div>
    </div>
  )
}
import React, { useState } from 'react'
import { useScanStore } from '../store/scanStore'
import { STATUS_COLORS, RISK_COLORS, truncate } from '../utils/helpers'
import { TargetCard } from './Cards'

const STATUS_BORDER = { found:'#00ff9d', not_found:'#2a4a62', partial:'#ffaa00', exposed:'#ff2d55', live:'#00ff9d', offline:'#2a4a62' }
const STATUS_LABEL  = { found:'FOUND', not_found:'NOT FOUND', partial:'PARTIAL', exposed:'EXPOSED', live:'LIVE', offline:'OFFLINE', masked:'MASKED' }

function SectionTitle({ label }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8, marginTop:4 }}>
      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, letterSpacing:2, textTransform:'uppercase', color:'#2a4a62' }}>{label}</span>
      <div style={{ flex:1, height:1, background:'#0d2438' }}/>
    </div>
  )
}

function ResultRow({ r }) {
  const [hov, setHov] = useState(false)
  const borderCol = STATUS_BORDER[r.status] || '#2a4a62'
  const statusCol = STATUS_COLORS[r.status] || '#2a4a62'

  return (
    <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        display:'flex', alignItems:'center', gap:12, padding:'8px 12px',
        background: hov ? '#0f1e2e' : '#0b1520',
        border:`1px solid ${hov ? '#0f3a5a' : 'transparent'}`,
        borderLeft:`2px solid ${borderCol}`,
        marginBottom:4, cursor:'pointer', transition:'all .15s',
        opacity: r.status === 'not_found' ? .45 : 1,
        animation:'slide-in .2s ease-out',
      }}>
      <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#c8e6f5', width:130, flexShrink:0, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
        {r.platform}
      </div>
      <div style={{ flex:1, fontSize:11, color:'#5a8ba8', fontFamily:'Share Tech Mono,monospace', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
        {truncate(r.data, 70)}
      </div>
      <div style={{ fontSize:9, fontFamily:'Share Tech Mono,monospace', letterSpacing:1, padding:'2px 6px', color:statusCol, border:`1px solid ${statusCol}33`, textTransform:'uppercase', flexShrink:0 }}>
        {STATUS_LABEL[r.status] || r.status?.toUpperCase()}
      </div>
    </div>
  )
}

export default function ResultsPanel() {
  const { results, target, activeModule, scanStatus } = useScanStore()
  const [filter, setFilter] = useState('all')

  // Group results by category
  const categories = {}
  results.forEach(r => {
    const cat = r.category || 'general'
    if (!categories[cat]) categories[cat] = []
    categories[cat].push(r)
  })

  const filtered = filter === 'all' ? results : results.filter(r => r.status === filter)

  return (
    <div style={{ display:'flex', flexDirection:'column', background:'#080f18', overflow:'hidden', height:'100%' }}>
      {/* Header */}
      <div style={{ padding:'10px 16px', background:'#050d14', borderBottom:'1px solid #0d2438', display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
        <div style={{ width:6, height:6, borderRadius:'50%', background:'#00d4ff', boxShadow:'0 0 8px #00d4ff' }}/>
        <span style={{ fontFamily:'Orbitron,monospace', fontSize:10, fontWeight:600, letterSpacing:2, textTransform:'uppercase', color:'#5a8ba8' }}>Intelligence Results</span>
        <span style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>
          [{activeModule?.toUpperCase()} MODULE]{target ? ` — ${target}` : ''}
        </span>
      </div>

      {/* Filter tabs */}
      {results.length > 0 && (
        <div style={{ display:'flex', gap:4, padding:'8px 16px', borderBottom:'1px solid #0d2438', flexShrink:0 }}>
          {['all','found','exposed','partial','not_found'].map(f => (
            <div key={f} onClick={() => setFilter(f)}
              style={{ padding:'3px 10px', fontFamily:'Share Tech Mono,monospace', fontSize:9, letterSpacing:1, textTransform:'uppercase', cursor:'pointer', border:`1px solid ${filter===f ? '#0f3a5a':'transparent'}`, color: filter===f ? '#00d4ff' : '#2a4a62', background: filter===f ? 'rgba(0,212,255,.05)':'none' }}>
              {f}
            </div>
          ))}
          <span style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>{filtered.length} results</span>
        </div>
      )}

      {/* Scrollable content */}
      <div style={{ flex:1, overflowY:'auto', padding:16 }}>

        {/* Empty state */}
        {scanStatus === 'idle' && (
          <div style={{ textAlign:'center', padding:'60px 20px', color:'#2a4a62' }}>
            <div style={{ fontSize:40, marginBottom:16, opacity:.3 }}>🔍</div>
            <div style={{ fontFamily:'Orbitron,monospace', fontSize:12, letterSpacing:2, marginBottom:8 }}>AWAITING TARGET</div>
            <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11 }}>Enter a target above and click EXECUTE to begin intelligence gathering</div>
          </div>
        )}

        {/* Scanning state */}
        {scanStatus === 'running' && results.length === 0 && (
          <div style={{ textAlign:'center', padding:'40px 20px', color:'#5a8ba8' }}>
            <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11 }}>
              <span className="animate-spin-fast" style={{ display:'inline-block', marginRight:8, color:'#00d4ff' }}>◈</span>
              Gathering intelligence...
            </div>
          </div>
        )}

        {/* Target card */}
        {target && <TargetCard/>}

        {/* Results by category */}
        {filter === 'all'
          ? Object.entries(categories).map(([cat, items]) => (
              <div key={cat} style={{ marginBottom:16 }}>
                <SectionTitle label={cat.replace(/_/g,' ')}/>
                {items.map((r, i) => <ResultRow key={r.id || i} r={r}/>)}
              </div>
            ))
          : (
            <div>
              <SectionTitle label={`${filter} results`}/>
              {filtered.map((r, i) => <ResultRow key={r.id || i} r={r}/>)}
              {filtered.length === 0 && <div style={{ color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:11 }}>No {filter} results</div>}
            </div>
          )
        }
      </div>
    </div>
  )
}
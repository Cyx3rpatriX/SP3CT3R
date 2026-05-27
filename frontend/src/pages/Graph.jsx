import React from 'react'
import GraphView from '../components/GraphView'
import { useScanStore } from '../store/scanStore'

export default function Graph() {
  const { results } = useScanStore()
  return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
      <div style={{ padding:'10px 20px', background:'#050d14', borderBottom:'1px solid #0d2438', display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
        <div style={{ width:6, height:6, borderRadius:'50%', background:'#00d4ff', boxShadow:'0 0 8px #00d4ff' }}/>
        <span style={{ fontFamily:'Orbitron,monospace', fontSize:10, fontWeight:600, letterSpacing:2, textTransform:'uppercase', color:'#5a8ba8' }}>Entity Relationship Graph</span>
        <span style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>{results.filter(r=>r.status!=='not_found').length} nodes</span>
      </div>
      <div style={{ flex:1, overflow:'hidden' }}>
        <GraphView/>
      </div>
    </div>
  )
}
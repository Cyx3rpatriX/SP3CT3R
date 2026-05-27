import React, { useState } from 'react'
import { useScanStore } from '../store/scanStore'
import { MODULE_ICONS, RISK_COLORS, formatElapsed } from '../utils/helpers'

function Panel({ children, style={} }) {
  return <div style={{ background:'#080f18', border:'1px solid #0d2438', ...style }}>{children}</div>
}
function PanelHeader({ title, tag }) {
  return (
    <div style={{ padding:'10px 16px', background:'#050d14', borderBottom:'1px solid #0d2438', display:'flex', alignItems:'center', gap:10 }}>
      <div style={{ width:6, height:6, borderRadius:'50%', background:'#00d4ff', boxShadow:'0 0 8px #00d4ff' }}/>
      <span style={{ fontFamily:'Orbitron,monospace', fontSize:10, fontWeight:600, letterSpacing:2, textTransform:'uppercase', color:'#5a8ba8' }}>{title}</span>
      {tag && <span style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>{tag}</span>}
    </div>
  )
}

export default function Reports() {
  const { results, target, activeModule, summary, history } = useScanStore()
  const [fmt, setFmt] = useState('json')

  const exportData = () => {
    const data = { target, module: activeModule, summary, results, exported_at: new Date().toISOString() }
    const content = fmt === 'json' ? JSON.stringify(data, null, 2) : resultsToCSV(results)
    const blob = new Blob([content], { type: fmt === 'json' ? 'application/json' : 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `sp3ct3r_${target}_${Date.now()}.${fmt}`; a.click()
  }

  const resultsToCSV = (rows) => {
    const header = 'category,platform,data,status,risk_level'
    const lines = rows.map(r => `${r.category},${r.platform},"${r.data}",${r.status},${r.risk_level}`)
    return [header, ...lines].join('\n')
  }

  return (
    <div style={{ flex:1, overflow:'auto', padding:24, background:'#020408' }}>
      <div style={{ marginBottom:24 }}>
        <h1 style={{ fontFamily:'Orbitron,monospace', fontSize:18, color:'#00d4ff', letterSpacing:3, textShadow:'0 0 16px rgba(0,212,255,.4)', marginBottom:4 }}>INTELLIGENCE REPORTS</h1>
        <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#2a4a62' }}>Export and review gathered intelligence data</div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        {/* Export panel */}
        <Panel>
          <PanelHeader title="Export Report" tag={target ? `[${target}]` : '[NO SCAN]'}/>
          <div style={{ padding:20 }}>
            {!target ? (
              <div style={{ color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:11, textAlign:'center', padding:'30px 0' }}>Run a scan first to generate a report</div>
            ) : (
              <>
                <div style={{ marginBottom:16 }}>
                  {[
                    { label:'Target',   value: target },
                    { label:'Module',   value: activeModule?.toUpperCase() },
                    { label:'Findings', value: results.length },
                    { label:'Found',    value: results.filter(r=>r.status==='found').length },
                    { label:'Exposed',  value: results.filter(r=>r.status==='exposed').length },
                  ].map(({label, value}) => (
                    <div key={label} style={{ display:'flex', justifyContent:'space-between', padding:'6px 0', borderBottom:'1px solid #0d2438' }}>
                      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62', textTransform:'uppercase', letterSpacing:1 }}>{label}</span>
                      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#c8e6f5' }}>{value}</span>
                    </div>
                  ))}
                </div>

                <div style={{ display:'flex', gap:8, marginBottom:16 }}>
                  {['json','csv'].map(f => (
                    <div key={f} onClick={() => setFmt(f)}
                      style={{ padding:'5px 16px', fontFamily:'Share Tech Mono,monospace', fontSize:10, textTransform:'uppercase', letterSpacing:1, border:`1px solid ${fmt===f ? '#00d4ff':'#0d2438'}`, color: fmt===f ? '#00d4ff':'#5a8ba8', cursor:'pointer', background: fmt===f ? 'rgba(0,212,255,.08)':'none' }}>
                      {f.toUpperCase()}
                    </div>
                  ))}
                </div>

                <button onClick={exportData} style={{ width:'100%', padding:'10px', background:'#00d4ff', border:'none', color:'#020408', fontFamily:'Orbitron,monospace', fontSize:11, fontWeight:700, letterSpacing:2, cursor:'pointer', clipPath:'polygon(8px 0%,100% 0%,calc(100% - 8px) 100%,0% 100%)' }}>
                  EXPORT {fmt.toUpperCase()}
                </button>
              </>
            )}
          </div>
        </Panel>

        {/* Summary panel */}
        <Panel>
          <PanelHeader title="Scan Summary"/>
          <div style={{ padding:20 }}>
            {results.length === 0 ? (
              <div style={{ color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:11, textAlign:'center', padding:'30px 0' }}>No scan data available</div>
            ) : (
              <div>
                {/* Category breakdown */}
                {(() => {
                  const cats = {}
                  results.forEach(r => { cats[r.category] = (cats[r.category]||0)+1 })
                  return Object.entries(cats).map(([cat, count]) => (
                    <div key={cat} style={{ display:'flex', alignItems:'center', gap:10, padding:'6px 0', borderBottom:'1px solid #0d2438' }}>
                      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#c8e6f5', flex:1, textTransform:'uppercase' }}>{cat}</span>
                      <div style={{ width:80, height:4, background:'#0d2438', position:'relative' }}>
                        <div style={{ position:'absolute', left:0, top:0, height:'100%', width:`${Math.min(100,(count/results.length)*100)}%`, background:'#00d4ff' }}/>
                      </div>
                      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#00d4ff', width:24, textAlign:'right' }}>{count}</span>
                    </div>
                  ))
                })()}
              </div>
            )}
          </div>
        </Panel>
      </div>
    </div>
  )
}
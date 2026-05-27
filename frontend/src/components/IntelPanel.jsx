import React from 'react'
import { useScanStore } from '../store/scanStore'

const SOCIAL_PLATFORMS = [
  { name:'Twitter', icon:'🐦' }, { name:'LinkedIn', icon:'💼' },
  { name:'GitHub',  icon:'🐙' }, { name:'Instagram',icon:'📸' },
  { name:'Facebook',icon:'📘' }, { name:'Discord',  icon:'🎮' },
  { name:'YouTube', icon:'▶'  }, { name:'TikTok',   icon:'🎵' },
  { name:'Reddit',  icon:'💬' },
]

function KVRow({ label, value, valueColor }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', padding:'6px 0', borderBottom:'1px solid #0d2438', gap:8 }}>
      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, letterSpacing:1, color:'#2a4a62', textTransform:'uppercase', flexShrink:0 }}>{label}</span>
      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color: valueColor || '#c8e6f5', textAlign:'right', wordBreak:'break-all' }}>{value || '—'}</span>
    </div>
  )
}

function SectionTitle({ label }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, letterSpacing:2, textTransform:'uppercase', color:'#2a4a62' }}>{label}</span>
      <div style={{ flex:1, height:1, background:'#0d2438' }}/>
    </div>
  )
}

function ThreatBar({ name, pct, color, icon }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:10, padding:'7px 0', borderBottom:'1px solid #0d2438' }}>
      <span style={{ fontSize:11, width:16, flexShrink:0 }}>{icon}</span>
      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#c8e6f5', flex:1 }}>{name}</span>
      <div style={{ width:60, height:4, background:'#0d2438', position:'relative', flexShrink:0 }}>
        <div style={{ height:'100%', width:`${pct}%`, background:color, position:'absolute', left:0, top:0 }}/>
      </div>
      <span style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, width:28, textAlign:'right', color, flexShrink:0 }}>{pct}%</span>
    </div>
  )
}

export default function IntelPanel() {
  const { results, target } = useScanStore()

  // Extract geo data from results
  const geoResult  = results.find(r => r.category === 'geolocation' && r.platform === 'City')
  const ipResult   = results.find(r => r.platform === 'IP Address')
  const asnResult  = results.find(r => r.platform === 'Organization / ASN' || r.platform === 'ISP / ASN')
  const countryR   = results.find(r => r.platform === 'Country')
  const ispResult  = results.find(r => r.platform === 'ISP' || r.platform === 'Hostname')
  const sslIssuer  = results.find(r => r.platform === 'SSL Issuer')
  const sslExpiry  = results.find(r => r.platform === 'SSL Valid Until')
  const sslSans    = results.find(r => r.platform === 'SSL SANs')

  // Social hits
  const socialResults = results.filter(r => r.category === 'social')
  const socialMap  = {}
  socialResults.forEach(r => { socialMap[r.platform?.toLowerCase()] = r.status })

  // Threat indicators (synthesized)
  const exposedCount = results.filter(r => r.status === 'exposed').length
  const highRiskCount = results.filter(r => r.risk_level === 'high').length
  const openPorts = results.filter(r => r.category === 'port').length
  const breachCount = results.filter(r => r.category === 'breach' && r.status === 'found').length

  const threats = [
    { name:'Exposed Services', pct: Math.min(100, exposedCount * 25),    color:'#ff2d55', icon:'🔴' },
    { name:'High Risk Findings',pct: Math.min(100, highRiskCount * 15),  color:'#ffaa00', icon:'🟠' },
    { name:'Open Ports',        pct: Math.min(100, openPorts * 10),      color:'#ffcc00', icon:'🟡' },
    { name:'Data Breaches',     pct: Math.min(100, breachCount * 33),    color:'#00ff9d', icon:'🟢' },
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', background:'#080f18', overflow:'hidden', height:'100%' }}>
      {/* Header */}
      <div style={{ padding:'10px 16px', background:'#050d14', borderBottom:'1px solid #0d2438', display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
        <div style={{ width:6, height:6, borderRadius:'50%', background:'#00ff9d', boxShadow:'0 0 8px #00ff9d' }}/>
        <span style={{ fontFamily:'Orbitron,monospace', fontSize:10, fontWeight:600, letterSpacing:2, textTransform:'uppercase', color:'#5a8ba8' }}>Entity Intelligence</span>
        <span style={{ marginLeft:'auto', fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>[CORRELATED]</span>
      </div>

      {/* Scrollable body */}
      <div style={{ flex:1, overflowY:'auto', padding:16 }}>

        {!target && (
          <div style={{ color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:11, textAlign:'center', paddingTop:40 }}>
            Entity intelligence will appear here after a scan
          </div>
        )}

        {/* Geolocation */}
        {(geoResult || ipResult) && (
          <div style={{ marginBottom:20 }}>
            <SectionTitle label="Geolocation"/>
            {/* Fake map grid */}
            <div style={{ height:120, background:'#050d14', border:'1px solid #0d2438', position:'relative', overflow:'hidden', marginBottom:12 }}>
              <div style={{ position:'absolute', inset:0, backgroundImage:'linear-gradient(rgba(0,212,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.06) 1px,transparent 1px)', backgroundSize:'20px 20px' }}/>
              <div style={{ position:'absolute', top:'40%', left:'55%', fontSize:16, filter:'drop-shadow(0 0 6px #00d4ff)', animation:'pulse-dot 2s infinite' }}>📍</div>
              <div style={{ position:'absolute', bottom:8, left:10, fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#00d4ff' }}>🌍 {geoResult?.data || 'Unknown Location'}</div>
              <div style={{ position:'absolute', top:8, right:10, fontFamily:'Share Tech Mono,monospace', fontSize:8, color:'#2a4a62' }}>
                {results.find(r => r.platform === 'Location (LatLon)')?.data || ''}
              </div>
            </div>
            <KVRow label="IP"      value={ipResult?.data} />
            <KVRow label="ASN"     value={asnResult?.data} />
            <KVRow label="Country" value={countryR?.data} />
            <KVRow label="ISP"     value={ispResult?.data} />
          </div>
        )}

        {/* Threat indicators */}
        <div style={{ marginBottom:20 }}>
          <SectionTitle label="Threat Indicators"/>
          {threats.map(t => <ThreatBar key={t.name} {...t}/>)}
          {results.length === 0 && <div style={{ color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:10 }}>No threat data yet</div>}
        </div>

        {/* Social presence */}
        <div style={{ marginBottom:20 }}>
          <SectionTitle label="Social Presence"/>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:6 }}>
            {SOCIAL_PLATFORMS.map(p => {
              const key = p.name.toLowerCase().replace('/','').replace(' ','')
              const hit = Object.keys(socialMap).some(k => k.includes(key.slice(0,5)))
              return (
                <div key={p.name} style={{ padding:'8px 6px', background:'#050d14', border:`1px solid ${hit ? 'rgba(0,255,157,.3)' : '#0d2438'}`, textAlign:'center', cursor:'pointer', opacity: hit ? 1 : .35, transition:'all .15s' }}>
                  <div style={{ fontSize:14, marginBottom:4 }}>{p.icon}</div>
                  <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:8, color: hit ? '#00ff9d' : '#5a8ba8', letterSpacing:1 }}>{p.name}</div>
                </div>
              )
            })}
          </div>
        </div>

        {/* SSL Certificate */}
        {sslIssuer && (
          <div style={{ marginBottom:20 }}>
            <SectionTitle label="SSL Certificate"/>
            <KVRow label="Issuer"     value={sslIssuer?.data} />
            <KVRow label="Valid Until" value={sslExpiry?.data} valueColor="#00ff9d" />
            <KVRow label="SANs"       value={sslSans?.data} />
          </div>
        )}

        {/* DNS summary */}
        {results.filter(r => r.category === 'dns').length > 0 && (
          <div style={{ marginBottom:20 }}>
            <SectionTitle label="DNS Summary"/>
            {results.filter(r => r.category === 'dns').slice(0,6).map((r,i) => (
              <KVRow key={i} label={r.platform.replace(' Record','')} value={r.data?.slice(0,40)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
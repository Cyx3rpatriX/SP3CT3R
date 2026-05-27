import React, { useState } from 'react'

const API_KEYS = [
  { key:'SHODAN_API_KEY',      label:'Shodan',        desc:'Port scanning, service fingerprinting',    url:'https://shodan.io' },
  { key:'IPINFO_API_KEY',      label:'IPInfo',        desc:'Enhanced IP geolocation & ASN data',       url:'https://ipinfo.io' },
  { key:'HIBP_API_KEY',        label:'HaveIBeenPwned',desc:'Email breach database lookups',            url:'https://haveibeenpwned.com' },
  { key:'VIRUSTOTAL_API_KEY',  label:'VirusTotal',    desc:'Malware & reputation analysis',            url:'https://virustotal.com' },
  { key:'HUNTER_API_KEY',      label:'Hunter.io',     desc:'Email discovery & validation',             url:'https://hunter.io' },
  { key:'WHOISXML_API_KEY',    label:'WhoisXML',      desc:'Extended WHOIS & DNS history',             url:'https://whoisxmlapi.com' },
  { key:'NUMVERIFY_API_KEY',   label:'NumVerify',     desc:'Phone number carrier & validation',        url:'https://numverify.com' },
  { key:'ABUSEIPDB_KEY',       label:'AbuseIPDB',     desc:'IP reputation & abuse reports',            url:'https://abuseipdb.com' },
]

function KeyRow({ keyName, label, desc, url }) {
  const [val, setVal] = useState('')
  const [saved, setSaved] = useState(false)
  const [show, setShow] = useState(false)

  const save = () => {
    if (val.trim()) { setSaved(true); setTimeout(() => setSaved(false), 2000) }
  }

  return (
    <div style={{ background:'#0b1520', border:'1px solid #0d2438', padding:16, marginBottom:8 }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:10 }}>
        <div>
          <div style={{ fontFamily:'Orbitron,monospace', fontSize:11, color:'#00d4ff', letterSpacing:1, marginBottom:4 }}>{label}</div>
          <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#5a8ba8' }}>{desc}</div>
        </div>
        <a href={url} target="_blank" rel="noreferrer" style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62', textDecoration:'none', letterSpacing:1 }}>GET KEY ↗</a>
      </div>
      <div style={{ display:'flex', gap:8, alignItems:'center' }}>
        <div style={{ flex:1, display:'flex', alignItems:'center', border:'1px solid #0f3a5a', background:'#050d14', padding:'0 10px', gap:8, height:34 }}>
          <span style={{ color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:10, flexShrink:0 }}>{keyName}=</span>
          <input type={show ? 'text' : 'password'} value={val} onChange={e => setVal(e.target.value)}
            placeholder="Enter API key..."
            style={{ flex:1, background:'none', border:'none', outline:'none', fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#c8e6f5' }}
          />
          <span onClick={() => setShow(!show)} style={{ cursor:'pointer', color:'#2a4a62', fontSize:11 }}>{show ? '🙈':'👁'}</span>
        </div>
        <button onClick={save} style={{ padding:'8px 16px', background: saved ? '#00ff9d22' : '#00d4ff', border: saved ? '1px solid #00ff9d' : 'none', color: saved ? '#00ff9d' : '#020408', fontFamily:'Orbitron,monospace', fontSize:9, letterSpacing:1, cursor:'pointer', flexShrink:0 }}>
          {saved ? '✓ SAVED' : 'SAVE'}
        </button>
      </div>
    </div>
  )
}

export default function Settings() {
  return (
    <div style={{ flex:1, overflow:'auto', padding:24, background:'#020408' }}>
      <div style={{ marginBottom:24 }}>
        <h1 style={{ fontFamily:'Orbitron,monospace', fontSize:18, color:'#00d4ff', letterSpacing:3, textShadow:'0 0 16px rgba(0,212,255,.4)', marginBottom:4 }}>SETTINGS</h1>
        <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#2a4a62' }}>Configure API keys and platform preferences</div>
      </div>

      {/* Warning */}
      <div style={{ background:'rgba(255,170,0,.06)', border:'1px solid rgba(255,170,0,.2)', padding:12, marginBottom:24, display:'flex', gap:10, alignItems:'flex-start' }}>
        <span style={{ color:'#ffaa00', fontSize:14, flexShrink:0 }}>⚠</span>
        <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:10, color:'#ffaa00' }}>
          API keys are stored locally in your browser session only. For production use, set them in your <code>.env</code> file on the backend server.
        </div>
      </div>

      {/* API Keys */}
      <div style={{ marginBottom:32 }}>
        <div style={{ fontFamily:'Orbitron,monospace', fontSize:12, color:'#5a8ba8', letterSpacing:2, marginBottom:16 }}>API KEY CONFIGURATION</div>
        {API_KEYS.map(k => <KeyRow key={k.key} {...k}/>)}
      </div>

      {/* Scan defaults */}
      <div>
        <div style={{ fontFamily:'Orbitron,monospace', fontSize:12, color:'#5a8ba8', letterSpacing:2, marginBottom:16 }}>SCAN DEFAULTS</div>
        <div style={{ background:'#0b1520', border:'1px solid #0d2438', padding:16 }}>
          {[
            { label:'Concurrent Threads', val:'10', note:'Parallel scan workers' },
            { label:'Request Timeout (s)', val:'30', note:'Per-source timeout' },
            { label:'Max Results',         val:'1000', note:'Cap per scan session' },
          ].map(s => (
            <div key={s.label} style={{ display:'flex', alignItems:'center', gap:16, padding:'10px 0', borderBottom:'1px solid #0d2438' }}>
              <div style={{ flex:1 }}>
                <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#c8e6f5', marginBottom:2 }}>{s.label}</div>
                <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62' }}>{s.note}</div>
              </div>
              <input defaultValue={s.val}
                style={{ width:80, background:'#050d14', border:'1px solid #0f3a5a', padding:'6px 10px', fontFamily:'Share Tech Mono,monospace', fontSize:11, color:'#00d4ff', outline:'none', textAlign:'center' }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
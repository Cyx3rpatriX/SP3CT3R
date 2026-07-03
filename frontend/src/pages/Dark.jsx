import React, { useState, useEffect, useRef } from 'react'
import { useScanStore } from '../store/scanStore'
import { startScan } from '../services/api'
import { useWebSocket } from '../hooks/useWebSocket'
import { LOG_COLORS, STATUS_COLORS, RISK_COLORS, truncate, formatElapsed } from '../utils/helpers'
import Terminal from '../components/Terminal'

// ── Constants ─────────────────────────────────────────────────
const SEVERITY_COLORS = {
  critical: '#ff2d55', high: '#ff6b35', medium: '#ffaa00',
  low: '#00d4ff', info: '#2a4a62',
}
const SEVERITY_BG = {
  critical: 'rgba(255,45,85,.12)', high: 'rgba(255,107,53,.1)',
  medium: 'rgba(255,170,0,.08)', low: 'rgba(0,212,255,.06)', info: 'rgba(42,74,98,.1)',
}
const SOURCE_ICONS = {
  breach: '🔓', paste: '📋', tor: '🧅', threat_intel: '☣',
  commercial_plugin: '🔌', default: '◈',
}

const COMMERCIAL_PLUGINS = [
  { name: 'Flare',            key: 'FLARE_API_KEY',           status: 'inactive', desc: 'Dark web monitoring + stealer logs', url: 'https://flare.io' },
  { name: 'Recorded Future',  key: 'RECORDED_FUTURE_API_KEY', status: 'inactive', desc: 'Enterprise threat intelligence',     url: 'https://recordedfuture.com' },
  { name: 'DeHashed',         key: 'DEHASHED_API_KEY',        status: 'inactive', desc: 'Credential + breach database',       url: 'https://dehashed.com' },
  { name: 'VirusTotal',       key: 'VIRUSTOTAL_API_KEY',      status: 'inactive', desc: 'Malware & reputation analysis',      url: 'https://virustotal.com' },
]

// ── Sub-components ────────────────────────────────────────────

function PanelHeader({ accent = '#00d4ff', title, tag, children }) {
  return (
    <div style={{ padding: '10px 16px', background: '#050d14', borderBottom: '1px solid #0d2438', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
      <div style={{ width: 6, height: 6, borderRadius: '50%', background: accent, boxShadow: `0 0 8px ${accent}` }} />
      <span style={{ fontFamily: 'Orbitron,monospace', fontSize: 10, fontWeight: 600, letterSpacing: 2, textTransform: 'uppercase', color: '#5a8ba8' }}>{title}</span>
      {tag && <span style={{ marginLeft: 'auto', fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: '#2a4a62' }}>{tag}</span>}
      {children}
    </div>
  )
}

function TorStatusPanel({ torStatus }) {
  const connected = torStatus?.connected === 'yes'
  const col = connected ? '#00ff9d' : torStatus?.checked ? '#ff2d55' : '#ffaa00'
  const label = connected ? 'ACTIVE' : torStatus?.checked ? 'OFFLINE' : 'CHECKING...'

  return (
    <div style={{ background: '#080f18', border: '1px solid #0d2438', overflow: 'hidden' }}>
      <PanelHeader accent={col} title="Tor Network Status" tag="[ANONYMITY LAYER]" />
      <div style={{ padding: 16 }}>
        {/* Status indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 16px', background: '#050d14', border: `1px solid ${col}33`, marginBottom: 14 }}>
          <div style={{ position: 'relative', width: 48, height: 48, flexShrink: 0 }}>
            <div style={{ position: 'absolute', inset: 0, border: `2px solid ${col}`, borderRadius: '50%', boxShadow: `0 0 16px ${col}55` }}
              className={connected ? 'animate-spin-slow' : ''} />
            <div style={{ position: 'absolute', inset: 6, background: `${col}22`, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>🧅</div>
          </div>
          <div>
            <div style={{ fontFamily: 'Orbitron,monospace', fontSize: 14, fontWeight: 700, color: col, letterSpacing: 2, textShadow: `0 0 12px ${col}` }}>{label}</div>
            <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#5a8ba8', marginTop: 4 }}>
              {connected
                ? `Exit node: ${torStatus?.exit_ip || '...'} · ${torStatus?.latency_ms || '?'}ms`
                : 'SOCKS5 127.0.0.1:9050 — not reachable'}
            </div>
          </div>
          <div style={{ marginLeft: 'auto', padding: '4px 12px', border: `1px solid ${col}`, fontFamily: 'Orbitron,monospace', fontSize: 9, color: col, letterSpacing: 2 }}>
            {connected ? 'ANONYMIZED' : 'CLEARNET'}
          </div>
        </div>

        {/* Setup guide if offline */}
        {!connected && (
          <div style={{ background: 'rgba(255,170,0,.05)', border: '1px solid rgba(255,170,0,.15)', padding: '10px 14px' }}>
            <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#ffaa00', marginBottom: 8 }}>⚠ Tor not running — scan proceeds on clearnet</div>
            <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#5a8ba8', lineHeight: 1.8 }}>
              To enable Tor routing:<br />
              <span style={{ color: '#00d4ff' }}>sudo apt install tor</span> then <span style={{ color: '#00d4ff' }}>sudo service tor start</span><br />
              Set <span style={{ color: '#00ff9d' }}>TOR_ENABLED=true</span> in <span style={{ color: '#2a4a62' }}>.env</span>
            </div>
          </div>
        )}

        {connected && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8 }}>
            {[
              { label: 'Exit IP',   value: torStatus?.exit_ip || '—' },
              { label: 'Country',   value: torStatus?.exit_country || '—' },
              { label: 'Latency',   value: torStatus?.latency_ms ? `${torStatus.latency_ms}ms` : '—' },
            ].map(s => (
              <div key={s.label} style={{ background: '#050d14', border: '1px solid #0d2438', padding: '8px 12px', textAlign: 'center' }}>
                <div style={{ fontFamily: 'Orbitron,monospace', fontSize: 11, color: '#00ff9d', marginBottom: 3 }}>{s.value}</div>
                <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 8, color: '#2a4a62', textTransform: 'uppercase', letterSpacing: 1 }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function FindingCard({ r }) {
  const [expanded, setExpanded] = useState(false)
  const cat = r.category || 'general'
  const sev = r.risk_level || 'info'
  const icon = SOURCE_ICONS[cat] || SOURCE_ICONS.default
  const col  = SEVERITY_COLORS[sev]
  const bg   = SEVERITY_BG[sev]

  return (
    <div onClick={() => setExpanded(!expanded)}
      style={{ background: '#0b1520', border: `1px solid ${col}33`, borderLeft: `3px solid ${col}`, marginBottom: 8, cursor: 'pointer', transition: 'all .2s', animation: 'slide-in .25s ease-out' }}
      onMouseEnter={e => e.currentTarget.style.background = '#0f1e2e'}
      onMouseLeave={e => e.currentTarget.style.background = '#0b1520'}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px' }}>
        <span style={{ fontSize: 16, flexShrink: 0 }}>{icon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 11, color: '#c8e6f5', marginBottom: 3 }}>{r.platform}</div>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#5a8ba8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{truncate(r.data, 85)}</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
          <div style={{ padding: '2px 8px', background: bg, border: `1px solid ${col}55`, fontFamily: 'Orbitron,monospace', fontSize: 8, color: col, letterSpacing: 1, textTransform: 'uppercase' }}>{sev}</div>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 8, color: '#2a4a62', textTransform: 'uppercase', letterSpacing: 1 }}>{cat.replace('_',' ')}</div>
        </div>
      </div>
      {expanded && (
        <div style={{ padding: '0 14px 12px', borderTop: '1px solid #0d2438' }}>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#5a8ba8', lineHeight: 1.8, marginTop: 10, wordBreak: 'break-all' }}>{r.data}</div>
          {r.raw?.url && (
            <a href={r.raw.url} target="_blank" rel="noreferrer"
              style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: '#00d4ff', textDecoration: 'none', letterSpacing: 1 }}>
              VIEW SOURCE ↗
            </a>
          )}
        </div>
      )}
    </div>
  )
}

function SummaryStats({ results }) {
  const counts = {
    breaches:    results.filter(r => r.category === 'breach').length,
    pastes:      results.filter(r => r.category === 'paste').length,
    threat:      results.filter(r => r.category === 'threat_intel').length,
    critical:    results.filter(r => r.risk_level === 'critical').length,
    high:        results.filter(r => r.risk_level === 'high').length,
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 8, marginBottom: 16 }}>
      {[
        { num: counts.breaches, label: 'Breaches',    col: '#ff2d55' },
        { num: counts.pastes,   label: 'Paste Hits',  col: '#ffaa00' },
        { num: counts.threat,   label: 'Threat IOCs', col: '#a855f7' },
        { num: counts.critical, label: 'Critical',    col: '#ff2d55' },
        { num: counts.high,     label: 'High Risk',   col: '#ff6b35' },
      ].map(s => (
        <div key={s.label} style={{ background: '#0b1520', border: '1px solid #0d2438', padding: '10px 12px', textAlign: 'center' }}>
          <div style={{ fontFamily: 'Orbitron,monospace', fontSize: 20, fontWeight: 700, color: s.col, lineHeight: 1, marginBottom: 4 }}>{s.num}</div>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 8, letterSpacing: 1.5, color: '#5a8ba8', textTransform: 'uppercase' }}>{s.label}</div>
        </div>
      ))}
    </div>
  )
}

function CommercialPlugins() {
  return (
    <div style={{ background: '#080f18', border: '1px solid #0d2438', overflow: 'hidden' }}>
      <PanelHeader accent="#a855f7" title="Commercial Threat Intel APIs" tag="[PLUG-INS]" />
      <div style={{ padding: 16 }}>
        {COMMERCIAL_PLUGINS.map(p => (
          <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '10px 14px', background: '#0b1520', border: '1px solid #0d2438', marginBottom: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#2a4a62', flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'Orbitron,monospace', fontSize: 11, color: '#c8e6f5', marginBottom: 3 }}>{p.name}</div>
              <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: '#2a4a62' }}>{p.desc}</div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <div style={{ padding: '3px 10px', fontFamily: 'Share Tech Mono,monospace', fontSize: 9, border: '1px solid #2a4a62', color: '#2a4a62', letterSpacing: 1 }}>INACTIVE</div>
              <a href={p.url} target="_blank" rel="noreferrer"
                style={{ padding: '3px 10px', fontFamily: 'Share Tech Mono,monospace', fontSize: 9, border: '1px solid #0f3a5a', color: '#00d4ff', letterSpacing: 1, textDecoration: 'none' }}>
                GET KEY ↗
              </a>
            </div>
          </div>
        ))}
        <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: '#2a4a62', marginTop: 8, lineHeight: 1.8 }}>
          Set API keys in <span style={{ color: '#00d4ff' }}>.env</span> to activate plug-ins.<br />
          Each activated key unlocks deeper intelligence sourcing automatically.
        </div>
      </div>
    </div>
  )
}

// ── Main Dark Page ────────────────────────────────────────────

export default function Dark() {
  const [target, setTarget]       = useState('')
  const [loading, setLoading]     = useState(false)
  const [scanId, setScanId]       = useState(null)
  const [torStatus, setTorStatus] = useState({ checked: false })
  const [activeFilter, setFilter] = useState('all')

  const { startScan: storeStart, results, scanStatus, addLog, progress, found, elapsed } = useScanStore()
  const { connect } = useWebSocket(null)

  // Check Tor status on mount
  useEffect(() => {
    fetch('/api/v1/darkweb/tor-status')
      .then(r => r.json())
      .then(d => setTorStatus({ checked: true, connected: d.tor_available ? 'yes' : 'no', ...d }))
      .catch(() => setTorStatus({ checked: true, connected: 'no' }))
  }, [])

  const handleScan = async () => {
    if (!target.trim() || loading) return
    setLoading(true)
    try {
      const res = await startScan(target.trim(), 'darkweb')
      const id  = res.data.scan_id
      setScanId(id)
      storeStart(id, target.trim(), 'darkweb')
      connect(id)
    } catch (e) {
      addLog('ERROR', `Failed to start dark web scan: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Filter results for this page (darkweb module only + category filter)
  const darkResults = results.filter(r =>
    activeFilter === 'all' || r.category === activeFilter
  )

  const FILTERS = [
    { key: 'all',               label: 'ALL' },
    { key: 'breach',            label: 'BREACHES' },
    { key: 'paste',             label: 'PASTES' },
    { key: 'threat_intel',      label: 'THREAT INTEL' },
    { key: 'tor',               label: 'TOR' },
    { key: 'commercial_plugin', label: 'PLUG-INS' },
  ]

  const bars = Math.round(progress / 5)
  const barStr = '█'.repeat(bars) + '░'.repeat(20 - bars)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden', background: '#020408' }}>

      {/* ── Dark Web Scan Bar ── */}
      <div style={{ padding: '12px 20px', background: '#050d14', borderBottom: '1px solid #0d2438', display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
        {/* Dark web indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 14px', border: '1px solid rgba(168,85,247,.3)', background: 'rgba(168,85,247,.06)', flexShrink: 0 }}>
          <span style={{ fontSize: 12 }}>🕶</span>
          <span style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#a855f7', letterSpacing: 1 }}>DARK WEB</span>
        </div>

        {/* Input */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', border: '1px solid #0f3a5a', background: '#0b1520', padding: '0 14px', gap: 10, height: 38, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 2, background: '#a855f7', boxShadow: '0 0 10px #a855f7' }} />
          <span style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 12, color: '#a855f7', whiteSpace: 'nowrap' }}>MONITOR://</span>
          <input value={target} onChange={e => setTarget(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScan()}
            placeholder="Enter email, domain, IP, or keyword to monitor..."
            style={{ flex: 1, background: 'none', border: 'none', outline: 'none', fontFamily: 'Share Tech Mono,monospace', fontSize: 13, color: '#c8e6f5', caretColor: '#a855f7' }}
          />
        </div>

        {/* Scan button */}
        <button onClick={handleScan} disabled={loading || scanStatus === 'running' || !target.trim()}
          style={{
            padding: '9px 28px', background: loading || scanStatus === 'running' ? '#0d2438' : '#a855f7',
            border: 'none', color: loading || scanStatus === 'running' ? '#5a8ba8' : '#fff',
            fontFamily: 'Orbitron,monospace', fontSize: 11, fontWeight: 700, letterSpacing: 2,
            cursor: loading || scanStatus === 'running' ? 'not-allowed' : 'pointer',
            textTransform: 'uppercase', clipPath: 'polygon(10px 0%,100% 0%,calc(100% - 10px) 100%,0% 100%)',
            boxShadow: loading || scanStatus === 'running' ? 'none' : '0 0 20px rgba(168,85,247,.4)',
            whiteSpace: 'nowrap',
          }}>
          {loading ? '...' : scanStatus === 'running' ? 'SCANNING' : 'MONITOR'}
        </button>
      </div>

      {/* ── Progress bar ── */}
      <div style={{ height: 2, background: '#0d2438', flexShrink: 0 }}>
        <div style={{ height: '100%', width: `${progress}%`, background: 'linear-gradient(90deg,#a855f7,#ff2d55)', transition: 'width .4s', boxShadow: '0 0 10px rgba(168,85,247,.5)' }} />
      </div>

      {/* ── Status strip ── */}
      <div style={{ padding: '5px 20px', background: 'rgba(0,13,20,.97)', borderBottom: '1px solid #0d2438', display: 'flex', alignItems: 'center', gap: 20, flexShrink: 0 }}>
        <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: scanStatus === 'running' ? '#a855f7' : scanStatus === 'completed' ? '#00ff9d' : '#2a4a62', display: 'flex', alignItems: 'center', gap: 6 }}>
          {scanStatus === 'running' && <span className="animate-spin-fast">◈</span>}
          {scanStatus === 'running' ? `MONITORING — ${target}` : scanStatus === 'completed' ? `COMPLETE — ${found} findings` : 'READY — Enter a target to begin monitoring'}
        </div>
        {scanStatus !== 'idle' && <>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#5a8ba8' }}>Found: <span style={{ color: '#00ff9d' }}>{found}</span></div>
          <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#5a8ba8' }}>Elapsed: <span style={{ color: '#c8e6f5' }}>{formatElapsed(elapsed)}</span></div>
          {scanStatus === 'running' && <div style={{ marginLeft: 'auto', fontFamily: 'Share Tech Mono,monospace', fontSize: 10, color: '#a855f7' }}>{Math.round(progress)}% {barStr}</div>}
        </>}
      </div>

      {/* ── Main 3-column layout ── */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 320px', gridTemplateRows: '1fr 200px', gap: 1, background: '#0d2438', overflow: 'hidden' }}>

        {/* ── LEFT: Findings ── */}
        <div style={{ background: '#080f18', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader accent="#ff2d55" title="Dark Intelligence Findings" tag={`[${results.length} FINDINGS]`} />

          {/* Filter bar */}
          <div style={{ display: 'flex', gap: 4, padding: '8px 16px', borderBottom: '1px solid #0d2438', flexShrink: 0, flexWrap: 'wrap' }}>
            {FILTERS.map(f => (
              <div key={f.key} onClick={() => setFilter(f.key)}
                style={{ padding: '3px 10px', fontFamily: 'Share Tech Mono,monospace', fontSize: 9, letterSpacing: 1, cursor: 'pointer', border: `1px solid ${activeFilter === f.key ? '#ff2d55' : 'transparent'}`, color: activeFilter === f.key ? '#ff2d55' : '#2a4a62', background: activeFilter === f.key ? 'rgba(255,45,85,.08)' : 'none' }}>
                {f.label} {f.key !== 'all' && `(${results.filter(r => r.category === f.key).length})`}
              </div>
            ))}
          </div>

          {/* Results scroll */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            {scanStatus === 'idle' && (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: '#2a4a62' }}>
                <div style={{ fontSize: 48, marginBottom: 16, opacity: .2 }}>🕶</div>
                <div style={{ fontFamily: 'Orbitron,monospace', fontSize: 12, letterSpacing: 2, marginBottom: 8, color: '#5a8ba8' }}>DARK WEB MONITOR READY</div>
                <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 11, lineHeight: 1.8 }}>
                  Enter an email, domain, IP, or keyword above.<br />
                  SP3CT3R will check breach databases, paste dumps,<br />
                  threat intelligence feeds, and Tor connectivity.
                </div>
              </div>
            )}

            {scanStatus === 'running' && results.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: '#5a8ba8' }}>
                <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 11 }}>
                  <span className="animate-spin-fast" style={{ display: 'inline-block', marginRight: 8, color: '#a855f7' }}>◈</span>
                  Scanning dark web intelligence sources...
                </div>
              </div>
            )}

            {results.length > 0 && <SummaryStats results={results} />}
            {darkResults.map((r, i) => <FindingCard key={r.id || i} r={r} />)}
          </div>
        </div>

        {/* ── RIGHT: Intel Panel ── */}
        <div style={{ gridColumn: 2, gridRow: '1/3', background: '#080f18', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <PanelHeader accent="#a855f7" title="Threat Context" tag="[CORRELATED]" />
          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>

            {/* Tor status */}
            <div style={{ marginBottom: 16 }}>
              <TorStatusPanel torStatus={torStatus} />
            </div>

            {/* Risk breakdown */}
            {results.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, letterSpacing: 2, color: '#2a4a62', textTransform: 'uppercase', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Risk Breakdown <div style={{ flex: 1, height: 1, background: '#0d2438' }} />
                </div>
                {['critical','high','medium','low','info'].map(sev => {
                  const count = results.filter(r => r.risk_level === sev).length
                  const pct   = results.length ? Math.round((count / results.length) * 100) : 0
                  const col   = SEVERITY_COLORS[sev]
                  return (
                    <div key={sev} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '5px 0', borderBottom: '1px solid #0d2438' }}>
                      <span style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: col, width: 55, textTransform: 'uppercase' }}>{sev}</span>
                      <div style={{ flex: 1, height: 4, background: '#0d2438', position: 'relative' }}>
                        <div style={{ position: 'absolute', left: 0, height: '100%', width: `${pct}%`, background: col }} />
                      </div>
                      <span style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: col, width: 24, textAlign: 'right' }}>{count}</span>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Category breakdown */}
            {results.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, letterSpacing: 2, color: '#2a4a62', textTransform: 'uppercase', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                  Sources <div style={{ flex: 1, height: 1, background: '#0d2438' }} />
                </div>
                {['breach','paste','threat_intel','tor','commercial_plugin'].map(cat => {
                  const count = results.filter(r => r.category === cat).length
                  const icon  = SOURCE_ICONS[cat]
                  return (
                    <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid #0d2438' }}>
                      <span style={{ fontSize: 12, width: 18 }}>{icon}</span>
                      <span style={{ fontFamily: 'Share Tech Mono,monospace', fontSize: 9, color: '#c8e6f5', flex: 1, textTransform: 'uppercase' }}>{cat.replace('_',' ')}</span>
                      <span style={{ fontFamily: 'Orbitron,monospace', fontSize: 11, color: count ? '#00d4ff' : '#2a4a62' }}>{count}</span>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Commercial plug-ins */}
            <CommercialPlugins />
          </div>
        </div>

        {/* ── BOTTOM: Terminal ── */}
        <div style={{ background: '#080f18' }}>
          <Terminal />
        </div>
      </div>
    </div>
  )
}




// import React from 'react'
// export default function Dark() {
//   return (
//     <div style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center', background:'#020408' }}>
//       <div style={{ textAlign:'center', color:'#2a4a62' }}>
//         <div style={{ fontSize:48, marginBottom:16, opacity:.2 }}>🔧</div>
//         <div style={{ fontFamily:'Orbitron,monospace', fontSize:14, letterSpacing:3, marginBottom:8, color:'#5a8ba8' }}>DARK</div>
//         <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11 }}>Module coming in the next phase</div>
//       </div>
//     </div>
//   )
// }

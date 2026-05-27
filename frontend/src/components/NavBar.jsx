import React, { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useScanStore } from '../store/scanStore'
import { healthCheck } from '../services/api'

const TABS = [
  { label: 'Dashboard',      path: '/' },
  { label: 'Investigations', path: '/investigations' },
  { label: 'Graph View',     path: '/graph' },
  { label: 'Reports',        path: '/reports' },
  { label: 'Threat Feed',    path: '/threats' },
  { label: 'Settings',       path: '/settings' },
]

export default function Navbar() {
  const [online, setOnline] = useState(false)
  const { scanStatus } = useScanStore()

  useEffect(() => {
    const check = async () => {
      try { await healthCheck(); setOnline(true) }
      catch { setOnline(false) }
    }
    check()
    const id = setInterval(check, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <nav style={{
      height: 52, background: '#050d14', borderBottom: '1px solid #0d2438',
      display: 'flex', alignItems: 'center', padding: '0 20px',
      flexShrink: 0, position: 'relative', zIndex: 10,
    }}>
      {/* gradient underline */}
      <div style={{
        position:'absolute', bottom:0, left:0, right:0, height:1,
        background:'linear-gradient(90deg, transparent, #00d4ff, #00ff9d, transparent)',
        opacity:.5, pointerEvents:'none',
      }}/>

      {/* Logo */}
      <div style={{ display:'flex', alignItems:'center', gap:10, marginRight:32, flexShrink:0 }}>
        <div style={{ position:'relative', width:28, height:28, display:'flex', alignItems:'center', justifyContent:'center' }}>
          <div style={{
            position:'absolute', width:36, height:36,
            border:'1px solid rgba(0,212,255,0.3)', borderRadius:'50%',
          }} className="animate-spin-slow"/>
          <div style={{
            width:28, height:28, border:'2px solid #00d4ff', borderRadius:'50%',
            display:'flex', alignItems:'center', justifyContent:'center',
            boxShadow:'0 0 20px rgba(0,212,255,0.35)',
          }}>
            <div style={{
              width:10, height:10, background:'#00d4ff', borderRadius:'50%',
              boxShadow:'0 0 10px #00d4ff',
            }} className="animate-pulse-dot"/>
          </div>
        </div>
        <span style={{
          fontFamily:'Orbitron,monospace', fontSize:18, fontWeight:900,
          letterSpacing:3, color:'#00d4ff',
          textShadow:'0 0 16px rgba(0,212,255,0.6)',
        }}>SP3CT3R</span>
      </div>

      {/* Nav tabs */}
      <div style={{ display:'flex', gap:2, flex:1 }}>
        {TABS.map(t => (
          <NavLink key={t.path} to={t.path} end={t.path=='/'}
            style={({ isActive }) => ({
              padding:'6px 16px',
              fontFamily:'Rajdhani,sans-serif', fontSize:12, fontWeight:600,
              letterSpacing:'1.5px', textTransform:'uppercase',
              color: isActive ? '#00d4ff' : '#5a8ba8',
              border: `1px solid ${isActive ? '#00d4ff' : 'transparent'}`,
              background: isActive ? 'rgba(0,212,255,.08)' : 'none',
              boxShadow: isActive ? '0 0 20px rgba(0,212,255,0.35)' : 'none',
              textDecoration:'none', whiteSpace:'nowrap', transition:'all .2s',
              cursor:'pointer',
            })}
          >{t.label}</NavLink>
        ))}
      </div>

      {/* Right controls */}
      <div style={{ display:'flex', alignItems:'center', gap:16, marginLeft:'auto' }}>
        <div style={{
          display:'flex', alignItems:'center', gap:6,
          fontFamily:'Share Tech Mono,monospace', fontSize:10,
          color: online ? '#00ff9d' : '#ff2d55',
          padding:'4px 10px',
          border:`1px solid ${online ? 'rgba(0,255,157,.2)' : 'rgba(255,45,85,.2)'}`,
          background: online ? 'rgba(0,255,157,.05)' : 'rgba(255,45,85,.05)',
        }}>
          <div style={{
            width:6, height:6, borderRadius:'50%',
            background: online ? '#00ff9d' : '#ff2d55',
            boxShadow: online ? '0 0 8px #00ff9d' : '0 0 8px #ff2d55',
          }} className="animate-pulse-dot"/>
          {online ? 'SYSTEMS ONLINE' : 'ENGINE OFFLINE'}
        </div>
        {['🔔','⚙','👤'].map((icon, i) => (
          <div key={i} style={{
            width:32, height:32, border:'1px solid #0d2438',
            background:'#0b1520', color:'#5a8ba8',
            display:'flex', alignItems:'center', justifyContent:'center',
            cursor:'pointer', fontSize:14,
          }}>{icon}</div>
        ))}
      </div>
    </nav>
  )
}
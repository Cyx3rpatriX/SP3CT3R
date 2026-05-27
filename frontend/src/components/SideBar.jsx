import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useScanStore } from '../store/scanStore'

const SCAN_MODULES = [
  { icon: '🌐', label: 'Domain',  path: '/',          module: 'domain'   },
  { icon: '👤', label: 'User',    path: '/username',  module: 'username' },
  { icon: '✉',  label: 'Email',   path: '/email',     module: 'email'    },
  { icon: '📱', label: 'Phone',   path: '/phone',     module: 'phone'    },
  { icon: '🖥',  label: 'IP',     path: '/ip',        module: 'ip'       },
  { icon: '🧍', label: 'Person',  path: '/person',    module: 'person'   },
]
const TOOLS = [
  { icon: '🕸', label: 'Graph',  path: '/graph'   },
  { icon: '🕶', label: 'Dark',   path: '/dark'    },
  { icon: '📋', label: 'Report', path: '/reports' },
]
const SYS = [
  { icon: '🔌', label: 'Plugin', path: '/plugins'  },
  { icon: '🔑', label: 'Keys',   path: '/settings' },
]

function SideBtn({ icon, label, path, module, badge }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { setActiveModule } = useScanStore()
  const active = location.pathname === path || (path === '/' && location.pathname === '/')

  return (
    <div onClick={() => { navigate(path); if (module) setActiveModule(module) }}
      style={{
        width: 44, height: 44, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 3,
        cursor: 'pointer', border: `1px solid ${active ? '#00d4ff' : 'transparent'}`,
        background: active ? 'rgba(0,212,255,.1)' : 'none',
        position: 'relative', transition: 'all .2s', flexShrink: 0,
      }}
      onMouseEnter={e => { if (!active) { e.currentTarget.style.borderColor='#0f3a5a'; e.currentTarget.style.background='#0f1e2e' }}}
      onMouseLeave={e => { if (!active) { e.currentTarget.style.borderColor='transparent'; e.currentTarget.style.background='none' }}}
    >
      {active && <div style={{ position:'absolute', left:-1, top:8, bottom:8, width:2, background:'#00d4ff', boxShadow:'0 0 8px #00d4ff' }}/>}
      <span style={{ fontSize: 16, lineHeight: 1 }}>{icon}</span>
      <span style={{ fontSize: 7, letterSpacing: 1, textTransform: 'uppercase', color: active ? '#00d4ff' : '#2a4a62', fontFamily: 'Share Tech Mono,monospace' }}>{label}</span>
      {badge && <div style={{ position:'absolute', top:4, right:4, width:14, height:14, background:'#ff2d55', borderRadius:'50%', fontSize:8, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'Share Tech Mono,monospace', color:'#fff', fontWeight:700 }}>{badge}</div>}
    </div>
  )
}

function SectionLabel({ text }) {
  return <div style={{ fontSize:8, letterSpacing:2, color:'#2a4a62', textTransform:'uppercase', margin:'8px 0 4px', fontFamily:'Share Tech Mono,monospace' }}>{text}</div>
}

function Divider() {
  return <div style={{ width:30, height:1, background:'#0d2438', margin:'4px 0' }}/>
}

export default function Sidebar() {
  return (
    <aside style={{ width:64, background:'#050d14', borderRight:'1px solid #0d2438', display:'flex', flexDirection:'column', alignItems:'center', padding:'12px 0', gap:4, flexShrink:0, overflowY:'auto' }}>
      <SectionLabel text="SCAN"/>
      {SCAN_MODULES.map(m => <SideBtn key={m.path} {...m}/>)}
      <Divider/>
      <SectionLabel text="TOOLS"/>
      {TOOLS.map(m => <SideBtn key={m.path} {...m}/>)}
      <Divider/>
      <SectionLabel text="SYS"/>
      {SYS.map(m => <SideBtn key={m.path} {...m}/>)}
    </aside>
  )
}
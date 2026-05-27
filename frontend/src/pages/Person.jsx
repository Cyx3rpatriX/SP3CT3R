import React from 'react'
export default function Person() {
  return (
    <div style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center', background:'#020408' }}>
      <div style={{ textAlign:'center', color:'#2a4a62' }}>
        <div style={{ fontSize:48, marginBottom:16, opacity:.2 }}>🔧</div>
        <div style={{ fontFamily:'Orbitron,monospace', fontSize:14, letterSpacing:3, marginBottom:8, color:'#5a8ba8' }}>PERSON</div>
        <div style={{ fontFamily:'Share Tech Mono,monospace', fontSize:11 }}>Module coming in the next phase</div>
      </div>
    </div>
  )
}

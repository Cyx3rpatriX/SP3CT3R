import React from 'react'
import ScanBar from '../components/ScanBar'
import StatusBar from '../components/StatusBar'
import ResultsPanel from '../components/ResultsPanel'
import IntelPanel from '../components/IntelPanel'
import Terminal from '../components/Terminal'
import { useScanStore } from '../store/scanStore'
import { useEffect } from 'react'

export default function EmailPage() {
  const { setActiveModule } = useScanStore()

  useEffect(() => {
    setActiveModule('email')
  }, [])

  return (
    <div style={{ display:'flex', flexDirection:'column', flex:1, overflow:'hidden' }}>
      <ScanBar/>
      <StatusBar/>
      <div style={{ flex:1, display:'grid', gridTemplateColumns:'1fr 300px', gridTemplateRows:'1fr 200px', gap:1, background:'#0d2438', overflow:'hidden' }}>
        <ResultsPanel/>
        <div style={{ gridColumn:2, gridRow:'1/3' }}><IntelPanel/></div>
        <Terminal/>
      </div>
    </div>
  )
}

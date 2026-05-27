import React from 'react'
import { Routes, Route } from 'react-router-dom'
import NavBar from './components/NavBar'
import SideBar from './components/SideBar'

// Pages
import Home          from './pages/Home'
import Domain        from './pages/Domain'
import Email         from './pages/Email'
import Username      from './pages/Username'
import Phone         from './pages/Phone'
import IP            from './pages/IP'
import Graph         from './pages/Graph'
import Reports       from './pages/Reports'
import Settings      from './pages/Settings'
import Investigations from './pages/Investigations'
import Threats       from './pages/Threats'
import Plugins       from './pages/Plugins'
import Dark          from './pages/Dark'
import Person        from './pages/Person'

export default function App() {
  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', background:'#020408', color:'#c8e6f5', overflow:'hidden' }}>
      <NavBar/>
      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
        <SideBar/>
        <main style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
          <Routes>
            <Route path="/"               element={<Home/>}/>
            <Route path="/domain"         element={<Domain/>}/>
            <Route path="/email"          element={<Email/>}/>
            <Route path="/username"       element={<Username/>}/>
            <Route path="/phone"          element={<Phone/>}/>
            <Route path="/ip"             element={<IP/>}/>
            <Route path="/person"         element={<Person/>}/>
            <Route path="/graph"          element={<Graph/>}/>
            <Route path="/reports"        element={<Reports/>}/>
            <Route path="/settings"       element={<Settings/>}/>
            <Route path="/investigations" element={<Investigations/>}/>
            <Route path="/threats"        element={<Threats/>}/>
            <Route path="/plugins"        element={<Plugins/>}/>
            <Route path="/dark"           element={<Dark/>}/>
          </Routes>
        </main>
      </div>
    </div>
  )
}

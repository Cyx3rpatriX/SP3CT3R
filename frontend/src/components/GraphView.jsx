import React, { useEffect, useRef } from 'react'
import { useScanStore } from '../store/scanStore'
import * as d3 from 'd3'
import { RISK_COLORS, MODULE_COLORS } from '../utils/helpers'

const TYPE_COLORS = { domain:'#00d4ff', ip:'#ffaa00', social:'#a855f7', dns:'#00ff9d', subdomain:'#00d4ff', geolocation:'#ffaa00', ssl:'#00ff9d', port:'#ff2d55', email:'#00ff9d', general:'#5a8ba8' }

export default function GraphView() {
  const svgRef = useRef()
  const { results, target } = useScanStore()

  useEffect(() => {
    if (!svgRef.current || results.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const W = svgRef.current.clientWidth || 800
    const H = svgRef.current.clientHeight || 500

    // Build nodes and links
    const nodes = [{ id: 'target', label: target, type: 'target', r: 24 }]
    const links = []
    const seen  = new Set(['target'])

    results.forEach((r, i) => {
      if (r.status === 'not_found') return
      const id = `${r.category}-${i}`
      if (!seen.has(id)) {
        seen.add(id)
        nodes.push({ id, label: r.platform, type: r.category, data: r.data, r: 10 })
        links.push({ source: 'target', target: id, status: r.status })
      }
    })

    // D3 force simulation
    const sim = d3.forceSimulation(nodes)
      .force('link',   d3.forceLink(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(W/2, H/2))
      .force('collision', d3.forceCollide(d => d.r + 12))

    const g = svg.append('g')

    // Zoom
    svg.call(d3.zoom().scaleExtent([.2, 4]).on('zoom', e => g.attr('transform', e.transform)))

    // Links
    const link = g.append('g').selectAll('line').data(links).enter().append('line')
      .attr('stroke', '#0f3a5a').attr('stroke-width', 1).attr('stroke-opacity', .6)

    // Nodes
    const node = g.append('g').selectAll('g').data(nodes).enter().append('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) sim.alphaTarget(.3).restart(); d.fx=d.x; d.fy=d.y })
        .on('drag',  (e, d) => { d.fx=e.x; d.fy=e.y })
        .on('end',   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null })
      )

    node.append('circle')
      .attr('r', d => d.r || 10)
      .attr('fill', d => d.type === 'target' ? '#00d4ff22' : `${TYPE_COLORS[d.type] || '#5a8ba8'}22`)
      .attr('stroke', d => d.type === 'target' ? '#00d4ff' : TYPE_COLORS[d.type] || '#5a8ba8')
      .attr('stroke-width', d => d.type === 'target' ? 2 : 1)
      .attr('filter', d => d.type === 'target' ? 'drop-shadow(0 0 8px #00d4ff)' : 'none')

    node.append('text')
      .attr('dy', d => (d.r || 10) + 12)
      .attr('text-anchor', 'middle')
      .attr('fill', '#5a8ba8')
      .attr('font-family', 'Share Tech Mono,monospace')
      .attr('font-size', 8)
      .text(d => d.label?.slice(0, 18))

    // Target center icon
    node.filter(d => d.type === 'target').append('text')
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('fill', '#00d4ff').attr('font-size', 12).text('◎')

    sim.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => sim.stop()
  }, [results, target])

  return (
    <div style={{ width:'100%', height:'100%', background:'#050d14', position:'relative' }}>
      {/* Grid overlay */}
      <div style={{ position:'absolute', inset:0, backgroundImage:'linear-gradient(rgba(0,212,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.04) 1px,transparent 1px)', backgroundSize:'40px 40px', pointerEvents:'none' }}/>

      {results.length === 0 ? (
        <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'#2a4a62', fontFamily:'Share Tech Mono,monospace', fontSize:12, textAlign:'center' }}>
          <div>
            <div style={{ fontSize:40, marginBottom:12, opacity:.2 }}>🕸</div>
            <div>Run a scan to generate the entity graph</div>
          </div>
        </div>
      ) : (
        <>
          <div style={{ position:'absolute', top:12, left:12, fontFamily:'Share Tech Mono,monospace', fontSize:9, color:'#2a4a62', zIndex:1 }}>
            {results.filter(r=>r.status!=='not_found').length} nodes · Drag to explore · Scroll to zoom
          </div>
          <svg ref={svgRef} style={{ width:'100%', height:'100%' }}/>
        </>
      )}
    </div>
  )
}
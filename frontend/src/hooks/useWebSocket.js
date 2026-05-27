/**
 * SP3CT3R WebSocket Hook
 * Connects to backend WS, streams live scan data into the store
 */
import { useEffect, useRef, useCallback } from 'react'
import { useScanStore } from '../store/scanStore'

export function useWebSocket(scanId) {
  const wsRef = useRef(null)
  const { addResult, addLog, updateProgress, completeScan, failScan, setWsRef } = useScanStore()

  const connect = useCallback((id) => {
    if (!id) return
    const clientId = id
    const url = `ws://${window.location.hostname}:8000/ws/${clientId}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      addLog('INFO', `WebSocket connected — streaming scan ${id}`)
      // Subscribe to this scan's events
      ws.send(JSON.stringify({ type: 'subscribe', scan_id: id }))
    }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        handleMessage(msg)
      } catch { /* ignore malformed */ }
    }

    ws.onerror = () => addLog('ERROR', 'WebSocket connection error')
    ws.onclose = () => addLog('INFO', 'WebSocket disconnected')

    setWsRef(ws)
    return ws
  }, [])

  const handleMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'log':
        addLog(msg.data?.level || 'INFO', msg.data?.message || '')
        break
      case 'result':
        addResult(msg.data)
        break
      case 'progress':
        updateProgress(msg.data?.progress || 0, msg.data?.found || 0, msg.data?.total || 0)
        break
      case 'complete':
        completeScan(msg.data || {})
        addLog('OK', '✅ Scan complete')
        break
      case 'error':
        failScan()
        addLog('ERROR', msg.data?.message || 'Scan failed')
        break
      default:
        break
    }
  }, [addLog, addResult, updateProgress, completeScan, failScan])

  useEffect(() => {
    if (scanId) {
      const ws = connect(scanId)
      return () => ws?.close()
    }
  }, [scanId])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
  }, [])

  return { connect, disconnect }
}
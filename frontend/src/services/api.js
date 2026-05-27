/**
 * SP3CT3R API Service
 * All HTTP calls to the FastAPI backend
 */
import axios from 'axios'

const BASE = '/api/v1'

const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// ── Scan API ────────────────────────────────────────

export const startScan = (target, module, options = {}) =>
  api.post('/scans/start', { target, module, options })

export const getScan = (scanId) =>
  api.get(`/scans/${scanId}`)

export const listScans = (limit = 20) =>
  api.get(`/scans/?limit=${limit}`)

export const cancelScan = (scanId) =>
  api.delete(`/scans/${scanId}`)

// ── Health ─────────────────────────────────────────

export const healthCheck = () =>
  axios.get('/health')

export default api
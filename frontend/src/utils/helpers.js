/** SP3CT3R Frontend Helpers */

export const formatElapsed = (s) => {
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
}

export const detectModule = (target) => {
  target = target.trim()
  if (/^[\d.]+$/.test(target)) return 'ip'
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(target)) return 'email'
  if (/^\+?[\d\s\-\(\)]{7,15}$/.test(target)) return 'phone'
  if (/^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/.test(target)) return 'domain'
  return 'username'
}

export const RISK_COLORS = {
  critical: '#ff2d55', high: '#ff2d55', medium: '#ffaa00',
  low: '#00d4ff', info: '#2a4a62',
}

export const STATUS_COLORS = {
  found: '#00ff9d', not_found: '#2a4a62', partial: '#ffaa00',
  exposed: '#ff2d55', live: '#00ff9d', offline: '#2a4a62',
}

export const MODULE_COLORS = {
  domain: '#00d4ff', email: '#00ff9d', username: '#a855f7',
  ip: '#ffaa00', phone: '#ff2d55', person: '#00d4ff',
}

export const MODULE_ICONS = {
  domain: '🌐', email: '✉', username: '👤',
  ip: '🖥', phone: '📱', person: '🧍',
}

export const LOG_COLORS = {
  INFO: '#00d4ff', OK: '#00ff9d', WARN: '#ffaa00',
  ERROR: '#ff2d55', DATA: '#a855f7',
}

export const truncate = (str, n = 80) =>
  str && str.length > n ? str.slice(0, n) + '…' : str
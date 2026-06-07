import { ElMessage } from 'element-plus'
import type { FeedSyncReport } from '../api/client'

export function apiErrorMessage(error: unknown, fallback: string) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string; message?: string } } }).response
    return response?.data?.detail || response?.data?.message || fallback
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export function syncSuggestion(message?: string) {
  const text = (message || '').toLowerCase()
  if (text.includes('timeout') || text.includes('timed out')) {
    return '建议稍后重试，并确认当前网络或代理可以访问该站点。'
  }
  if (text.includes('403')) {
    return '站点可能屏蔽了自动抓取请求，可以在浏览器中检查源地址或更换 Feed URL。'
  }
  if (text.includes('404')) {
    return 'Feed 地址可能已失效，请打开原站点确认新的 RSS/Atom 地址。'
  }
  if (text.includes('dns') || text.includes('getaddrinfo') || text.includes('name resolution')) {
    return '域名解析失败，请检查网络、代理或订阅源域名是否正确。'
  }
  if (text.includes('ssl')) {
    return '站点证书或 HTTPS 握手失败，请稍后重试或确认链接是否可在浏览器访问。'
  }
  if (text.includes('invalid rss') || text.includes('invalid atom') || text.includes('parse')) {
    return '返回内容不像有效 RSS/Atom，请确认填入的是订阅源 XML 地址。'
  }
  if (text.includes('connection failed') || text.includes('network error')) {
    return '网络连接失败，请确认外网访问、代理设置或源站状态。'
  }
  return '建议打开源地址确认 RSS/Atom 是否可访问，并查看同步日志。'
}

export function statusTagType(status?: string) {
  if (status === 'success' || status === 'imported') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'pending' || status === 'skipped') return 'warning'
  return 'info'
}

export function showSyncReportMessage(report: FeedSyncReport) {
  if (report.total === 0) {
    ElMessage.warning('当前没有可同步的订阅')
    return
  }
  if (report.failed > 0 && report.success === 0) {
    ElMessage.error(`同步失败：${report.failed} 个订阅失败，已显示具体原因`)
    return
  }
  if (report.failed > 0) {
    ElMessage.warning(`同步完成：${report.success} 个成功，${report.failed} 个失败`)
    return
  }
  ElMessage.success(`全部订阅同步完成：${report.success} 个成功`)
}

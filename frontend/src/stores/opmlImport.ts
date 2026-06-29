import { defineStore } from 'pinia'
import type { Feed, OPMLImportItem, OPMLImportReport } from '../api/client'

function emptyReport(files = 0): OPMLImportReport {
  return {
    files,
    total: 0,
    imported: 0,
    partial: 0,
    skipped: 0,
    failed: 0,
    results: []
  }
}

function countReport(files: number, results: OPMLImportItem[]): OPMLImportReport {
  const normalizedResults = results.map(normalizeImportItem)
  return {
    files,
    total: normalizedResults.length,
    imported: normalizedResults.filter((item) => item.status === 'imported').length,
    partial: normalizedResults.filter((item) => item.status === 'partial').length,
    skipped: normalizedResults.filter((item) => item.status === 'skipped').length,
    failed: normalizedResults.filter((item) => item.status === 'failed').length,
    results: normalizedResults
  }
}

function normalizedImportUrl(value?: string | null) {
  const trimmed = (value ?? '').trim()
  if (!trimmed) return ''

  try {
    const url = new URL(trimmed)
    const pathname = url.pathname === '/' ? '' : url.pathname.replace(/\/$/, '')
    return `${url.protocol}//${url.host.toLowerCase()}${pathname}${url.search}`
  } catch {
    return trimmed.replace(/\/$/, '')
  }
}

function isSameImportItem(current: OPMLImportItem, incoming: OPMLImportItem) {
  return current.source_file === incoming.source_file && normalizedImportUrl(current.url) === normalizedImportUrl(incoming.url)
}

function normalizeImportItem(item: OPMLImportItem): OPMLImportItem {
  if (item.status !== 'pending') return item
  return {
    ...item,
    message: '正在上传'
  }
}

export const useOpmlImportStore = defineStore('opmlImport', {
  state: () => ({
    importing: false,
    report: null as OPMLImportReport | null
  }),
  actions: {
    start(files: number, results: OPMLImportItem[]) {
      this.importing = true
      this.report = countReport(files, results)
    },
    setParsed(report: OPMLImportReport) {
      this.report = countReport(report.files, report.results)
    },
    mergeItem(item: OPMLImportItem) {
      const current = this.report ?? emptyReport(1)
      const results = [...current.results]
      const index = results.findIndex((existing) => isSameImportItem(existing, item))
      if (index >= 0) {
        results.splice(index, 1, item)
      } else {
        results.push(item)
      }
      this.report = countReport(current.files, results)
    },
    finish(report?: OPMLImportReport | null) {
      if (report) this.report = countReport(report.files, report.results)
      this.importing = false
    },
    upsertImportedFeed(feed: Feed) {
      if (!this.report) return
      this.report = {
        ...this.report,
        results: this.report.results.map((item) => (item.feed?.id === feed.id ? { ...item, feed } : item))
      }
    }
  }
})

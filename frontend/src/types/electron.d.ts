export {}

declare global {
  interface Window {
    rssReaderDesktop?: {
      apiBaseUrl: string
      platform: string
    }
  }
}

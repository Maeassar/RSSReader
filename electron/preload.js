const { contextBridge, ipcRenderer } = require('electron')

const apiArg = process.argv.find((arg) => arg.startsWith('--rssreader-api-base-url='))
const apiBaseUrl = apiArg ? apiArg.split('=')[1] : ''

contextBridge.exposeInMainWorld('rssReaderDesktop', {
  apiBaseUrl,
  platform: process.platform,
  openExternal: (url) => ipcRenderer.invoke('rssreader:open-external', url),
  saveMarkdown: (payload) => ipcRenderer.invoke('rssreader:save-markdown', payload)
})

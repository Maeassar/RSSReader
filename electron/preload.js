const { contextBridge } = require('electron')

const apiArg = process.argv.find((arg) => arg.startsWith('--rssreader-api-base-url='))
const apiBaseUrl = apiArg ? apiArg.split('=')[1] : ''

contextBridge.exposeInMainWorld('rssReaderDesktop', {
  apiBaseUrl,
  platform: process.platform
})

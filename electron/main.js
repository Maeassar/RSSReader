const { app, BrowserWindow, Menu, dialog, ipcMain, net: electronNet, protocol, shell } = require('electron')
const { spawn } = require('child_process')
const fs = require('fs/promises')
const http = require('http')
const nodeNet = require('net')
const path = require('path')
const { pathToFileURL } = require('url')

const useBuiltFrontend = process.env.RSSREADER_USE_BUILT_FRONTEND === '1'
const isDev = !app.isPackaged && !useBuiltFrontend
let backendProcess = null
let apiBaseUrl = process.env.RSSREADER_BACKEND_URL || ''

app.setName('Ripple')
if (process.platform === 'win32') {
  app.setAppUserModelId('io.github.ripple.desktop')
}

const applicationMenu = Menu.buildFromTemplate([
  ...(process.platform === 'darwin' ? [{ role: 'appMenu' }] : []),
  { role: 'editMenu' },
  { role: 'viewMenu' },
  { role: 'windowMenu' }
])
Menu.setApplicationMenu(applicationMenu)

function appIconPath() {
  const iconName = process.platform === 'win32' ? 'icon.ico' : 'icon.png'
  return app.isPackaged
    ? path.join(app.getAppPath(), 'build', iconName)
    : path.join(__dirname, '..', 'build', iconName)
}

function settingsFilePath() {
  return path.join(app.getPath('userData'), 'desktop-settings.json')
}

async function readDesktopSettings() {
  try {
    const raw = await fs.readFile(settingsFilePath(), 'utf8')
    return JSON.parse(raw)
  } catch (error) {
    return {}
  }
}

async function writeDesktopSettings(settings) {
  await fs.writeFile(settingsFilePath(), JSON.stringify(settings, null, 2), 'utf8')
}

async function fileExists(targetPath) {
  try {
    await fs.access(targetPath)
    return true
  } catch (error) {
    return false
  }
}

function ensureMarkdownExtension(targetPath) {
  return path.extname(targetPath).toLowerCase() === '.md' ? targetPath : `${targetPath}.md`
}

async function makeUniqueFilePath(targetPath) {
  const normalizedTargetPath = ensureMarkdownExtension(targetPath)
  if (!(await fileExists(normalizedTargetPath))) {
    return normalizedTargetPath
  }

  const extension = path.extname(normalizedTargetPath)
  const directory = path.dirname(normalizedTargetPath)
  const baseName = path.basename(normalizedTargetPath, extension)
  let suffix = 2

  while (true) {
    const candidatePath = path.join(directory, `${baseName}-${suffix}${extension}`)
    if (!(await fileExists(candidatePath))) {
      return candidatePath
    }
    suffix += 1
  }
}

function registerDesktopIpcHandlers() {
  ipcMain.handle('rssreader:open-external', async (_event, url) => {
    if (!isExternalUrl(url)) {
      return { ok: false, message: 'Unsupported external URL' }
    }
    await shell.openExternal(url)
    return { ok: true }
  })

  ipcMain.handle('rssreader:save-markdown', async (_event, payload) => {
    const content = typeof payload?.content === 'string' ? payload.content : ''
    const suggestedFilename = typeof payload?.suggestedFilename === 'string' && payload.suggestedFilename
      ? payload.suggestedFilename
      : 'digest.md'
    const settings = await readDesktopSettings()
    const initialDirectory = settings.lastExportDirectory || app.getPath('documents') || app.getPath('home')
    const defaultPath = await makeUniqueFilePath(path.join(initialDirectory, suggestedFilename))
    const result = await dialog.showSaveDialog({
      title: 'Export Markdown',
      defaultPath,
      filters: [
        { name: 'Markdown', extensions: ['md'] }
      ]
    })

    if (result.canceled || !result.filePath) {
      return { canceled: true }
    }

    const finalPath = await makeUniqueFilePath(result.filePath)
    await fs.writeFile(finalPath, content, 'utf8')
    await writeDesktopSettings({
      ...settings,
      lastExportDirectory: path.dirname(finalPath)
    })
    return { canceled: false, filePath: finalPath }
  })
}

function isExternalUrl(url) {
  if (typeof url !== 'string' || !url.trim()) return false
  try {
    const parsed = new URL(url)
    return ['http:', 'https:', 'mailto:'].includes(parsed.protocol)
  } catch (error) {
    return false
  }
}

function openExternalUrl(url) {
  if (!isExternalUrl(url)) return false
  shell.openExternal(url).catch((error) => {
    console.error(`Failed to open external URL ${url}:`, error)
  })
  return true
}

function isSameOriginUrl(left, right) {
  try {
    return new URL(left).origin === new URL(right).origin
  } catch (error) {
    return false
  }
}

protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true
    }
  }
])

function getBackendExecutablePath() {
  const executableName = process.platform === 'win32' ? 'RSSReaderBackend.exe' : 'RSSReaderBackend'
  return app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'RSSReaderBackend', executableName)
    : path.join(__dirname, '..', 'backend', 'desktop_server.py')
}

function findFreePort(host = '127.0.0.1') {
  return new Promise((resolve, reject) => {
    const server = nodeNet.createServer()
    server.once('error', reject)
    server.listen(0, host, () => {
      const address = server.address()
      const port = typeof address === 'object' && address ? address.port : 8000
      server.close(() => resolve(port))
    })
  })
}

function waitForHealth(baseUrl, retries = 60) {
  return new Promise((resolve, reject) => {
    let attempts = 0

    const check = () => {
      attempts += 1
      const request = http.get(`${baseUrl}/api/health`, (response) => {
        response.resume()
        if (response.statusCode && response.statusCode >= 200 && response.statusCode < 300) {
          resolve()
          return
        }
        retry()
      })

      request.on('error', retry)
      request.setTimeout(1000, () => {
        request.destroy()
        retry()
      })
    }

    const retry = () => {
      if (attempts >= retries) {
        reject(new Error(`Backend did not become healthy at ${baseUrl}`))
        return
      }
      setTimeout(check, 500)
    }

    check()
  })
}

function waitForUrl(url, retries = 60) {
  return new Promise((resolve, reject) => {
    let attempts = 0

    const check = () => {
      attempts += 1
      const request = http.get(url, (response) => {
        response.resume()
        if (response.statusCode && response.statusCode >= 200 && response.statusCode < 500) {
          resolve()
          return
        }
        retry()
      })

      request.on('error', retry)
      request.setTimeout(1000, () => {
        request.destroy()
        retry()
      })
    }

    const retry = () => {
      if (attempts >= retries) {
        reject(new Error(`URL did not become available: ${url}`))
        return
      }
      setTimeout(check, 500)
    }

    check()
  })
}

function registerFrontendProtocol() {
  const frontendRoot = path.join(app.getAppPath(), 'frontend', 'dist')

  protocol.handle('app', (request) => {
    const requestUrl = new URL(request.url)
    const requestPath = decodeURIComponent(requestUrl.pathname === '/' ? '/index.html' : requestUrl.pathname)
    const filePath = path.normalize(path.join(frontendRoot, requestPath))

    if (!filePath.startsWith(frontendRoot)) {
      return new Response('Forbidden', { status: 403 })
    }

    return electronNet.fetch(pathToFileURL(filePath).toString())
  })
}

async function startBackend() {
  if (apiBaseUrl) {
    await waitForHealth(apiBaseUrl)
    return
  }

  const host = '127.0.0.1'
  const port = await findFreePort(host)
  apiBaseUrl = `http://${host}:${port}`
  const backendPath = getBackendExecutablePath()
  const env = {
    ...process.env,
    RSSREADER_HOST: host,
    RSSREADER_PORT: String(port),
    RSSREADER_DB_PATH: path.join(app.getPath('userData'), 'app.db')
  }

  if (app.isPackaged) {
    backendProcess = spawn(backendPath, [], { env, windowsHide: true, stdio: 'ignore' })
  } else {
    backendProcess = spawn(process.env.PYTHON || 'python', [backendPath], {
      cwd: path.join(__dirname, '..', 'backend'),
      env,
      windowsHide: true,
      stdio: 'inherit'
    })
  }

  backendProcess.on('exit', (code) => {
    if (code !== 0 && code !== null) {
      console.error(`RSSReader backend exited with code ${code}`)
    }
  })

  await waitForHealth(apiBaseUrl)
}

async function createWindow() {
  const mainWindow = new BrowserWindow({
    title: 'Ripple',
    icon: appIconPath(),
    autoHideMenuBar: true,
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
      additionalArguments: [`--rssreader-api-base-url=${apiBaseUrl}`]
    }
  })

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedUrl) => {
    console.error(`Renderer failed to load ${validatedUrl}: ${errorCode} ${errorDescription}`)
  })

  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    console.error(`Renderer process gone: ${details.reason}`)
  })

  mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    console.log(`[renderer:${level}] ${message} (${sourceId}:${line})`)
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    const currentUrl = mainWindow.webContents.getURL()
    if (!isSameOriginUrl(url, currentUrl) && openExternalUrl(url)) {
      return { action: 'deny' }
    }
    return { action: 'allow' }
  })

  mainWindow.webContents.on('will-navigate', (event, url) => {
    const currentUrl = mainWindow.webContents.getURL()
    if (url !== currentUrl && !isSameOriginUrl(url, currentUrl) && openExternalUrl(url)) {
      event.preventDefault()
    }
  })

  if (isDev) {
    const frontendUrl = process.env.RSSREADER_FRONTEND_URL || 'http://127.0.0.1:5173'
    await waitForUrl(frontendUrl)
    await mainWindow.loadURL(frontendUrl)
  } else {
    await mainWindow.loadURL('app://rssreader/index.html')
  }

  if (process.env.RSSREADER_OPEN_DEVTOOLS === '1') {
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  }
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill()
    backendProcess = null
  }
}

app.whenReady().then(async () => {
  if (!isDev || useBuiltFrontend) {
    registerFrontendProtocol()
  }
  registerDesktopIpcHandlers()
  await startBackend()
  await createWindow()

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow()
    }
  })
})

app.on('before-quit', stopBackend)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

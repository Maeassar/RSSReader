const { spawn } = require('child_process')
const path = require('path')

const rootDir = path.resolve(__dirname, '..')
const venvPython = process.platform === 'win32'
  ? path.join(rootDir, '.venv', 'Scripts', 'python.exe')
  : path.join(rootDir, '.venv', 'bin', 'python')
const children = []

function run(command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: rootDir,
    env: { ...process.env, ...options.env },
    shell: process.platform === 'win32',
    stdio: 'inherit'
  })
  children.push(child)
  child.on('exit', (code) => {
    if (code && !shuttingDown) {
      shutdown(code)
    }
  })
  return child
}

let shuttingDown = false

function shutdown(code = 0) {
  shuttingDown = true
  for (const child of children) {
    if (!child.killed) {
      child.kill()
    }
  }
  process.exit(code)
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

run('npm', ['run', 'dev', '--prefix', 'frontend'])

setTimeout(() => {
  run('npx', ['electron', '.'], {
    env: {
      PYTHON: venvPython,
      RSSREADER_FRONTEND_URL: 'http://127.0.0.1:5173',
      RSSREADER_OPEN_DEVTOOLS: '1'
    }
  })
}, 1500)

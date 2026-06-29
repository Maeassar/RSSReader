const { spawnSync } = require('child_process')
const path = require('path')

const rootDir = path.resolve(__dirname, '..')
const separator = process.platform === 'win32' ? ';' : ':'
const executableName = process.platform === 'win32' ? 'RSSReaderBackend.exe' : 'RSSReaderBackend'
const fs = require('fs')
const venvNames = ['.venv1', '.venv']
const pythonCommand = venvNames
  .map((venvName) => process.platform === 'win32'
    ? path.join(rootDir, venvName, 'Scripts', 'python.exe')
    : path.join(rootDir, venvName, 'bin', 'python'))
  .find((pythonPath) => fs.existsSync(pythonPath)) || 'python'

console.log(`Using Python for backend build: ${pythonCommand}`)

const result = spawnSync(
  pythonCommand,
  [
    '-m',
    'PyInstaller',
    '--noconfirm',
    '--clean',
    '--name',
    executableName.replace(/\.exe$/, ''),
    '--add-data',
    `schema.sql${separator}.`,
    '--collect-all',
    'pydantic',
    '--collect-all',
    'pydantic_core',
    '--hidden-import',
    'backports.tarfile',
    '--exclude-module',
    'pkg_resources',
    '--exclude-module',
    'setuptools',
    'desktop_server.py'
  ],
  {
    cwd: path.join(rootDir, 'backend'),
    stdio: 'inherit',
    shell: process.platform === 'win32'
  }
)

process.exit(result.status || 0)

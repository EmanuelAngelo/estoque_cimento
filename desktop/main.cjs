const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let backendProc = null

function getBackendCommand() {
  // In production (installed), backend is bundled into resources/backend
  if (app.isPackaged) {
    const exe = path.join(process.resourcesPath, 'backend', 'estoque-cimento-backend.exe')
    return { command: exe, args: [] }
  }

  // Dev mode: run python script directly (expects venv at ../venv)
  const repoRoot = path.resolve(__dirname, '..')
  const pythonExe = path.join(repoRoot, 'venv', 'Scripts', 'python.exe')
  const script = path.join(repoRoot, 'desktop_backend.py')
  return { command: pythonExe, args: [script] }
}

function startBackend() {
  const { command, args } = getBackendCommand()

  const env = {
    ...process.env,
    ESTOQUE_CIMENTO_DESKTOP: '1',
    ESTOQUE_CIMENTO_PORT: '8000',
    // store db.sqlite3 in a user-writable directory
    ESTOQUE_CIMENTO_DATA_DIR: app.getPath('userData'),
    // tell Django where the Vite dist is (used to serve the SPA in desktop mode)
    ESTOQUE_CIMENTO_FRONTEND_DIST: app.isPackaged
      ? path.join(process.resourcesPath, 'frontend_dist')
      : path.join(path.resolve(__dirname, '..'), 'frontend', 'dist'),
  }

  backendProc = spawn(command, args, {
    env,
    stdio: 'ignore',
    windowsHide: true,
  })

  backendProc.on('exit', () => {
    backendProc = null
  })
}

async function waitForBackend() {
  const url = 'http://127.0.0.1:8000/api/health/'
  const timeoutMs = 30_000
  const started = Date.now()

  while (Date.now() - started < timeoutMs) {
    try {
      const res = await fetch(url)
      if (res.ok) return
    } catch {
      // ignore
    }
    await new Promise((r) => setTimeout(r, 250))
  }

  throw new Error('Backend não iniciou a tempo.')
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
  })

  await win.loadURL('http://127.0.0.1:8000/')
  win.show()
}

app.whenReady().then(async () => {
  startBackend()
  await waitForBackend()
  await createWindow()
})

app.on('window-all-closed', () => {
  if (backendProc) {
    try {
      backendProc.kill()
    } catch {
      // ignore
    }
  }
  app.quit()
})

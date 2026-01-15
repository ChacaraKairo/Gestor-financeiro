import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

// 1. Imports para rodar o Backend
const { spawn } = require('child_process')
const path = require('path')

let apiProcess = null

// 2. Função para iniciar o Backend
function startBackend() {
  // Se estiver em Desenvolvimento (npm run dev), NÃO roda o exe (você roda manual)
  if (!app.isPackaged) {
    console.log('Modo DEV: Inicie o backend manualmente no terminal.')
    return
  }

  // Se estiver em Produção (Instalado), roda o exe da pasta resources
  const scriptPath = path.join(process.resourcesPath, 'api.exe')
  console.log(`Iniciando Backend em: ${scriptPath}`)

  apiProcess = spawn(scriptPath)

  apiProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`)
  })

  apiProcess.stderr.on('data', (data) => {
    console.error(`Backend Erro: ${data}`)
  })
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200, // Aumentei um pouco para caber os gráficos
    height: 800,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  // 3. Inicia o Backend assim que o App abrir
  startBackend()

  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.on('ping', () => console.log('pong'))

  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// 4. Mata o Backend quando fechar a janela
app.on('before-quit', () => {
  if (apiProcess) {
    apiProcess.kill()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
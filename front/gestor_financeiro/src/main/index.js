import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

let apiProcess = null

function startBackend() {
  if (!app.isPackaged) {
    console.log('Modo DEV: Backend deve ser iniciado manualmente.')
    return
  }

  // Define onde procurar o api.exe (Prioridade para a pasta resources raiz)
  const resourcesFolder = process.resourcesPath
  const possiblePaths = [
    path.join(resourcesFolder, 'api.exe'),
    path.join(resourcesFolder, 'app.asar.unpacked', 'resources', 'api.exe'), // Às vezes o builder joga aqui
    path.join(resourcesFolder, 'resources', 'api.exe')
  ]

  let scriptPath = null
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) {
      scriptPath = p
      break
    }
  }

  if (!scriptPath) {
    dialog.showErrorBox('Erro Fatal', `O arquivo api.exe não foi encontrado.\nProcurado em:\n${possiblePaths.join('\n')}`)
    return
  }

  // --- O SEGREDO ESTÁ AQUI ---
  // Dizemos para o spawn rodar COM BASE na pasta do executável
  const options = {
    cwd: path.dirname(scriptPath), // <--- Força a pasta correta
    windowsHide: true // Oculta a janela preta (mude para false se quiser ver para debug)
  }

  // Tenta iniciar
  try {
    apiProcess = spawn(scriptPath, [], options)

    // Captura erros de inicialização (ex: permissão, arquivo corrompido)
    apiProcess.on('error', (err) => {
      dialog.showErrorBox('Erro ao Iniciar Backend', `Detalhe: ${err.message}`)
    })

    // Captura se o Backend fechar sozinho de repente
    apiProcess.on('close', (code) => {
      if (code !== 0 && code !== null) {
        // Opcional: Avisar se fechar com erro, mas cuidado para não spamar
        console.log(`Backend fechou com código: ${code}`)
      }
    })

  } catch (e) {
    dialog.showErrorBox('Exceção', `Erro ao tentar executar spawn: ${e}`)
  }
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
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
  startBackend() // Inicia o Python

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
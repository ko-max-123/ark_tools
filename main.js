const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');

let mainWindow;

app.on('ready', () => {
  mainWindow = new BrowserWindow({
    width: 2000,
    height: 1000,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');

  // 開発者ツールを自動的に開く
  mainWindow.webContents.openDevTools();
});

ipcMain.on('capture-screen', (event) => {
  console.log('capture-screen event received'); // デバッグ用ログ
  exec('python -c "from tag_analysis import capture_window; capture_window()"', (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error.message}`);
      event.reply('capture-error', error.message);
      return;
    }
    if (stderr) {
      console.error(`Stderr: ${stderr}`);
      event.reply('capture-error', stderr);
      return;
    }
    console.log(stdout);
    event.reply('capture-success', 'キャプチャが成功しました');
    
  });
});
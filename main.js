const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const { execFile } = require('child_process'); // execFileをインポート

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
  // 実行可能ファイルのパスを指定
  const exePath = path.join(process.resourcesPath, 'tag_analysis.exe');

  // 実行可能ファイルを実行
  execFile(exePath, (error, stdout, stderr) => {
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
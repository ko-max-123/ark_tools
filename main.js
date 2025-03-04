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
    event.reply('capture-success', 'キャプチャが終了しました');
  });
});

ipcMain.on('open-detail-window', (event, name, img) => {
  const detailWindow = new BrowserWindow({
    width: 1000,
    height: 1000,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  detailWindow.loadFile('detail.html');

  // 開発者ツールを自動的に開く
  detailWindow.webContents.openDevTools();

  // ウィンドウが読み込まれた後にデータを送信
  detailWindow.webContents.on('did-finish-load', () => {
    detailWindow.webContents.send('detail-data', name, img);
  });
});


ipcMain.on('open-item_detail-window', (event, itemId) => {
  const item_detailWindow = new BrowserWindow({
    width: 1000,
    height: 1000,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  item_detailWindow.loadFile('item_detail.html');

  // 開発者ツールを自動的に開く
  item_detailWindow.webContents.openDevTools();

  // ウィンドウが読み込まれた後にデータを送信
  item_detailWindow.webContents.on('did-finish-load', () => {
    item_detailWindow.webContents.send('detail-data', itemId);
  });
});

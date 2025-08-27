const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;

// ログ出力用の関数（シンプル版）
function writeLog(message, type = 'INFO') {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${type}] ${message}\n`;
  
  // コンソールに出力
  console.log(logMessage.trim());
  
  // ログファイルに保存
  try {
    const logDir = path.join(app.getPath('userData'), 'logs');
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    const logFile = path.join(logDir, 'arktools.log');
    fs.appendFileSync(logFile, logMessage, { encoding: 'utf8' });
    
  } catch (error) {
    console.error('ログファイル書き込みエラー:', error);
  }
}

// アプリ起動時の初期化
app.whenReady().then(() => {
  writeLog('アプリ起動開始');
  
  // 基本的なシステム情報のみ出力
  writeLog(`プラットフォーム: ${process.platform}`);
  writeLog(`Node.js バージョン: ${process.version}`);
  writeLog(`Electron バージョン: ${process.versions.electron}`);
  
  // 基本的なディレクトリ作成のみ
  try {
    const userDataPath = app.getPath('userData');
    const tempPath = app.getPath('temp');
    
    // 必要なディレクトリのみ作成
    const requiredDirs = [
      path.join(userDataPath, 'logs'),
      path.join(tempPath, 'Arktools')
    ];
    
    requiredDirs.forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        writeLog(`ディレクトリ作成: ${dir}`);
      }
    });
    
  } catch (error) {
    writeLog(`ディレクトリ作成エラー: ${error.message}`, 'ERROR');
  }
});

app.on('ready', () => {
  writeLog('アプリ準備完了');
  
  // 基本的なキャッシュ設定のみ
  app.commandLine.appendSwitch('--disable-gpu-cache');
  app.commandLine.appendSwitch('--disable-disk-cache');
  
  mainWindow = new BrowserWindow({
    width: 375,
    height: 667,
    minWidth: 320,
    minHeight: 568,
    maxWidth: 800,
    maxHeight: 1200,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: false,
      webSecurity: false
    },
    show: false,
    titleBarStyle: 'default',
    resizable: true,
    minimizable: true,
    maximizable: true,
    fullscreenable: true,
    useContentSize: true,
    center: true
  });

  mainWindow.loadFile('index.html');

  // ウィンドウが準備できてから表示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    writeLog('メインウィンドウ表示');
    
    // 開発モードでのみ開発者ツールを開く
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  });

  // 本番モードでは開発者ツールを無効化
  if (process.env.NODE_ENV !== 'development') {
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow.webContents.closeDevTools();
    });
  }
});

// ウィンドウが閉じられたときの処理
app.on('window-all-closed', () => {
  writeLog('アプリ終了');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// アクティブになったときの処理（macOS用）
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    // createWindow関数が定義されていない場合は何もしない
    writeLog('activate event received but no createWindow function');
  }
});

ipcMain.on('capture-screen', (event) => {
  writeLog('capture-screen event received');
  
  // ビルドされたアプリでの正しいパスを取得
  let pythonScriptPath;
  let tagImgPath;
  
  if (app.isPackaged) {
    // ビルドされたアプリの場合
    pythonScriptPath = path.join(process.resourcesPath, 'app.asar.unpacked', 'tag_analysis.py');
    tagImgPath = path.join(process.resourcesPath, 'app.asar.unpacked', 'tag_img');
  } else {
    // 開発モードの場合
    pythonScriptPath = path.join(__dirname, 'tag_analysis.py');
    tagImgPath = path.join(__dirname, 'tag_img');
  }
  
  writeLog(`Python script path: ${pythonScriptPath}`);
  writeLog(`Tag img path: ${tagImgPath}`);
  
  // ファイルの存在確認
  if (!require('fs').existsSync(pythonScriptPath)) {
    writeLog(`Python script not found: ${pythonScriptPath}`, 'ERROR');
    event.reply('capture-error', 'Pythonスクリプトが見つかりません');
    return;
  }
  
  if (!require('fs').existsSync(tagImgPath)) {
    writeLog(`Tag img folder not found: ${tagImgPath}`, 'ERROR');
    event.reply('capture-error', 'タグ画像フォルダが見つかりません');
    return;
  }
  
  // 埋め込みPython環境を使用してPythonを実行
  let pythonExecutable;
  let pythonEnv = {};
  
  if (app.isPackaged) {
    // ビルドされたアプリの場合、埋め込みPython環境を使用
    const embeddedPythonPath = path.join(process.resourcesPath, 'app.asar.unpacked', 'embedded_python');
    if (process.platform === 'win32') {
      pythonExecutable = path.join(embeddedPythonPath, 'python.exe');
      pythonEnv = {
        ...process.env,
        PYTHONPATH: path.join(embeddedPythonPath, 'Lib', 'site-packages'),
        PATH: `${embeddedPythonPath};${path.join(embeddedPythonPath, 'Scripts')};${process.env.PATH}`,
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1',
        PYTHONLEGACYWINDOWSSTDIO: 'utf-8',
        PYTHONHASHSEED: '0',
        PYTHONDONTWRITEBYTECODE: '1',
        SCRIPT_DIR: path.dirname(pythonScriptPath),
        WORKING_DIR: process.cwd()
      };
    } else {
      pythonExecutable = path.join(embeddedPythonPath, 'bin', 'python3');
      pythonEnv = {
        ...process.env,
        PYTHONPATH: path.join(embeddedPythonPath, 'lib', 'python3.8', 'site-packages'),
        PATH: `${path.join(embeddedPythonPath, 'bin')}:${process.env.PATH}`,
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1',
        PYTHONHASHSEED: '0',
        PYTHONDONTWRITEBYTECODE: '1',
        SCRIPT_DIR: path.dirname(pythonScriptPath),
        WORKING_DIR: process.cwd()
      };
    }
  } else {
    // 開発モードの場合、システムのPythonを使用
    pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
    pythonEnv = {
      ...process.env,
      PYTHONIOENCODING: 'utf-8',
      PYTHONUTF8: '1',
      PYTHONLEGACYWINDOWSSTDIO: 'utf-8',
      PYTHONHASHSEED: '0',
      PYTHONDONTWRITEBYTECODE: '1',
      SCRIPT_DIR: path.dirname(pythonScriptPath),
      WORKING_DIR: process.cwd()
    };
  }
  
  writeLog(`Using Python executable: ${pythonExecutable}`);
  
  const pythonProcess = spawn(pythonExecutable, [pythonScriptPath], {
      cwd: path.dirname(pythonScriptPath),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: pythonEnv
  });

  let outputData = '';
  let errorData = '';

  pythonProcess.stdout.setEncoding('utf-8');
  pythonProcess.stderr.setEncoding('utf-8');

  pythonProcess.stdout.on('data', (data) => {
      outputData += data.toString();
      writeLog(`Python stdout: ${data.toString()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      writeLog(`Python stderr: ${data.toString()}`);
  });

  pythonProcess.on('close', (code) => {
      writeLog(`Python process exited with code ${code}`);
      if (code === 0) {
          // レポートファイルのパスを取得
          let reportPath;
          if (app.isPackaged) {
              reportPath = path.join(process.resourcesPath, 'app.asar.unpacked', 'report.txt');
          } else {
              reportPath = path.join(__dirname, 'report.txt');
          }
          
          writeLog(`Report file path for renderer: ${reportPath}`);
          
          // レポートファイルの存在確認
          if (require('fs').existsSync(reportPath)) {
              event.reply('capture-success', 'キャプチャが成功しました', reportPath);
          } else {
              writeLog(`Report file not found after capture: ${reportPath}`, 'ERROR');
              event.reply('capture-success', 'キャプチャが成功しましたが、レポートファイルが見つかりません');
          }
      } else {
          event.reply('capture-error', `Pythonスクリプトがエラーコード ${code} で終了しました`);
      }
  });

  pythonProcess.on('error', (error) => {
      writeLog(`Python process error: ${error.message}`, 'ERROR');
      event.reply('capture-error', `Pythonプロセスエラー: ${error.message}`);
  });
});

// ログファイルをクリアするIPCハンドラー
ipcMain.on('clear-logs', (event) => {
  try {
    const logDir = path.join(app.getPath('userData'), 'logs');
    const logFile = path.join(logDir, 'arktools.log');
    
    if (fs.existsSync(logFile)) {
      fs.writeFileSync(logFile, '', { encoding: 'utf8' });
      writeLog('ログファイルをクリアしました');
      event.reply('logs-cleared', 'ログファイルをクリアしました');
    } else {
      event.reply('logs-cleared', 'ログファイルが見つかりません');
    }
  } catch (error) {
    writeLog(`ログファイルクリアエラー: ${error.message}`, 'ERROR');
    event.reply('logs-cleared', `ログファイルのクリアに失敗しました: ${error.message}`);
  }
});
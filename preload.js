const { contextBridge, ipcRenderer } = require('electron');

// レンダラープロセス向けAPIを作成
contextBridge.exposeInMainWorld('electronAPI', {
  sendParseResult: (result) => ipcRenderer.send('parse-result', result),
  onUpdateSelection: (callback) => ipcRenderer.on('update-selection', (event, result) => callback(result))
  
});

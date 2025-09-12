const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // File operations
  selectFile: () => ipcRenderer.invoke('select-file'),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  
  // Dialog operations
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Store operations
  getStoreValue: (key) => ipcRenderer.invoke('get-store-value', key),
  setStoreValue: (key, value) => ipcRenderer.invoke('set-store-value', key, value),
  getAllStoreValues: () => ipcRenderer.invoke('get-store-all'),
  clearStore: () => ipcRenderer.invoke('clear-store'),
  
  // API calls
  apiCall: (options) => ipcRenderer.invoke('api-call', options),
  
  // File operations
  openFile: (fileUrl) => ipcRenderer.invoke('open-file', fileUrl),
  openFileData: (fileData, filename) => ipcRenderer.invoke('open-file-data', fileData, filename),
  
  // Menu events
  onMenuNewDocument: (callback) => ipcRenderer.on('menu-new-document', callback),
  onMenuOpenDocument: (callback) => ipcRenderer.on('menu-open-document', callback),
  onMenuSettings: (callback) => ipcRenderer.on('menu-settings', callback),
  
  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});

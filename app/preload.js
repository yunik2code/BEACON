const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Auth methods
  googleAuth: () => ipcRenderer.invoke('google-oauth'),
  storeToken: (token) => ipcRenderer.invoke('store-token', token),
  getToken: () => ipcRenderer.invoke('get-token'),
  clearToken: () => ipcRenderer.invoke('clear-token'),
  
  // User methods
  storeUser: (user) => ipcRenderer.invoke('store-user', user),
  getUser: () => ipcRenderer.invoke('get-user'),
  
  // API fetch method
  apiFetch: async (endpoint, options = {}) => {
    const token = await ipcRenderer.invoke('get-token');
    return ipcRenderer.invoke('api-fetch', endpoint, options, token);
  }
});
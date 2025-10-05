const { app, BrowserWindow, ipcMain, session } = require('electron');
const path = require('path');
const Store = require('electron-store');

const store = new Store();
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the login page
  mainWindow.loadFile('src/pages/login.html');

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

// Handle Google OAuth
ipcMain.handle('google-oauth', async () => {
  return new Promise((resolve, reject) => {
    const authWindow = new BrowserWindow({
      width: 500,
      height: 600,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=743628186063-d3m3lahc8d5bhvuoc81rvdsbolh6t754.apps.googleusercontent.com` +
      `&redirect_uri=http://localhost:8000/auth/callback` +
      `&response_type=token` +
      `&scope=email profile`;

    authWindow.loadURL(googleAuthUrl);

    // Listen for redirect with token
    authWindow.webContents.on('will-redirect', (event, url) => {
      const urlParams = new URL(url);
      const hash = urlParams.hash;
      
      if (hash) {
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        
        if (accessToken) {
          authWindow.close();
          resolve(accessToken);
        }
      }
    });

    authWindow.on('closed', () => {
      reject(new Error('Authentication window closed'));
    });
  });
});

// Token management
ipcMain.handle('store-token', async (event, token) => {
  store.set('authToken', token);
  return true;
});

ipcMain.handle('get-token', async () => {
  return store.get('authToken');
});

ipcMain.handle('clear-token', async () => {
  store.delete('authToken');
  return true;
});

// Store user data
ipcMain.handle('store-user', async (event, user) => {
  store.set('user', user);
  return true;
});

ipcMain.handle('get-user', async () => {
  return store.get('user');
});

// Replace the api-fetch handler in main.js with this:
ipcMain.handle('api-fetch', async (event, endpoint, options = {}, token) => {
  const http = require('http');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return new Promise((resolve, reject) => {
    const requestOptions = {
      hostname: '127.0.0.1',  // Use IPv4 explicitly
      port: 8000,
      path: endpoint,
      method: options.method || 'GET',
      headers: headers
    };
    
    const req = http.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            ok: res.statusCode >= 200 && res.statusCode < 300,
            status: res.statusCode,
            data: jsonData
          });
        } catch (e) {
          resolve({
            ok: res.statusCode >= 200 && res.statusCode < 300,
            status: res.statusCode,
            data: data
          });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
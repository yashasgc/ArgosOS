console.log('Minimal test starting...');
console.log('process.type:', process.type);
console.log('process.versions.electron:', process.versions.electron);

try {
  const { app } = require('electron');
  console.log('app object:', typeof app);
  
  if (app) {
    console.log('App is available!');
    app.whenReady().then(() => {
      console.log('App is ready!');
      const { BrowserWindow } = require('electron');
      const win = new BrowserWindow({ width: 400, height: 300 });
      win.loadURL('data:text/html,<h1>Hello from Electron!</h1>');
    });
  } else {
    console.log('App is undefined');
  }
} catch (error) {
  console.error('Error:', error.message);
}

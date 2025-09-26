console.log('Starting simple Electron test...');
console.log('process.type:', process.type);
console.log('process.versions:', process.versions);

try {
  const { app, BrowserWindow } = require('electron');
  console.log('Electron imported successfully');
  console.log('app object:', typeof app);
  console.log('BrowserWindow object:', typeof BrowserWindow);
  
  if (app) {
    console.log('app.whenReady available:', typeof app.whenReady);
    app.whenReady().then(() => {
      console.log('App is ready!');
      const win = new BrowserWindow({ width: 800, height: 600 });
      win.loadURL('data:text/html,<h1>Hello from Electron!</h1>');
    });
  } else {
    console.log('app object is undefined');
  }
} catch (error) {
  console.error('Error importing Electron:', error);
}

const path = require('path');

module.exports = {
  appId: 'com.argos.os',
  productName: 'ArgosOS',
  directories: {
    output: 'dist-electron',
    buildResources: 'build'
  },
  files: [
    'dist/**/*',
    'electron/**/*',
    'node_modules/**/*',
    '!node_modules/.cache/**/*',
    '!node_modules/electron/**/*',
    '!node_modules/electron-builder/**/*'
  ],
  extraResources: [
    {
      from: '../../app',
      to: 'app',
      filter: ['**/*']
    },
    {
      from: '../../requirements.txt',
      to: 'requirements.txt'
    },
    {
      from: '../../pyproject.toml',
      to: 'pyproject.toml'
    },
    {
      from: '../../data',
      to: 'data',
      filter: ['**/*']
    },
    {
      from: '../../start.py',
      to: 'start.py'
    }
  ],
  mac: {
    category: 'public.app-category.productivity',
    target: [
      {
        target: 'dmg',
        arch: ['x64', 'arm64']
      }
    ],
    icon: 'build/icon.icns',
    // Bundle Python runtime
    extraResources: [
      {
        from: 'python-runtime',
        to: 'python-runtime',
        filter: ['**/*']
      }
    ]
  },
  win: {
    target: [
      {
        target: 'nsis',
        arch: ['x64']
      }
    ],
    icon: 'build/icon.ico',
    extraResources: [
      {
        from: 'python-runtime',
        to: 'python-runtime',
        filter: ['**/*']
      }
    ]
  },
  linux: {
    target: [
      {
        target: 'AppImage',
        arch: ['x64']
      }
    ],
    icon: 'build/icon.png',
    extraResources: [
      {
        from: 'python-runtime',
        to: 'python-runtime',
        filter: ['**/*']
      }
    ]
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    installerIcon: 'build/icon.ico',
    uninstallerIcon: 'build/icon.ico',
    installerHeaderIcon: 'build/icon.ico',
    createDesktopShortcut: true,
    createStartMenuShortcut: true
  },
  dmg: {
    title: 'ArgosOS Installer',
    icon: 'build/icon.icns',
    background: 'build/dmg-background.png',
    contents: [
      { x: 130, y: 220 },
      { x: 410, y: 220, type: 'link', path: '/Applications' }
    ]
  }
};
export interface ElectronAPI {
  // File operations
  selectFile: () => Promise<string | null>;
  selectFolder: () => Promise<string | null>;
  
  // Dialog operations
  showMessageBox: (options: {
    type?: 'info' | 'warning' | 'error' | 'question';
    title?: string;
    message: string;
    detail?: string;
    buttons?: string[];
  }) => Promise<{ response: number }>;
  
  // App info
  getAppVersion: () => Promise<string>;
  
  // Store operations
  getStoreValue: (key: string) => Promise<any>;
  setStoreValue: (key: string, value: any) => Promise<void>;
  getAllStoreValues: () => Promise<Record<string, any>>;
  clearStore: () => Promise<void>;
  
  // API calls
  apiCall: (options: {
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    endpoint: string;
    data?: any;
  }) => Promise<{ success: boolean; data?: any; error?: string }>;
  
  // Menu events
  onMenuNewDocument: (callback: () => void) => void;
  onMenuOpenDocument: (callback: (event: any, filePath: string) => void) => void;
  onMenuSettings: (callback: () => void) => void;
  
  // Remove listeners
  removeAllListeners: (channel: string) => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

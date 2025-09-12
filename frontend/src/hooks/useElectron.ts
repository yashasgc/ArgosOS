import { useEffect, useCallback } from 'react';

export const useElectron = () => {
  const isElectron = typeof window !== 'undefined' && window.electronAPI;

  const selectFile = useCallback(async () => {
    if (!isElectron) return null;
    return await window.electronAPI.selectFile();
  }, [isElectron]);

  const selectFolder = useCallback(async () => {
    if (!isElectron) return null;
    return await window.electronAPI.selectFolder();
  }, [isElectron]);

  const showMessageBox = useCallback(async (options: {
    type?: 'info' | 'warning' | 'error' | 'question';
    title?: string;
    message: string;
    detail?: string;
    buttons?: string[];
  }) => {
    if (!isElectron) {
      alert(options.message);
      return { response: 0 };
    }
    return await window.electronAPI.showMessageBox(options);
  }, [isElectron]);

  const getAppVersion = useCallback(async () => {
    if (!isElectron) return '1.0.0';
    return await window.electronAPI.getAppVersion();
  }, [isElectron]);

  const getStoreValue = useCallback(async (key: string) => {
    if (!isElectron) return null;
    return await window.electronAPI.getStoreValue(key);
  }, [isElectron]);

  const setStoreValue = useCallback(async (key: string, value: any) => {
    if (!isElectron) return;
    await window.electronAPI.setStoreValue(key, value);
  }, [isElectron]);

  const getAllStoreValues = useCallback(async () => {
    if (!isElectron) return {};
    return await window.electronAPI.getAllStoreValues();
  }, [isElectron]);

  const clearStore = useCallback(async () => {
    if (!isElectron) return;
    await window.electronAPI.clearStore();
  }, [isElectron]);

  const apiCall = useCallback(async (options: {
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    endpoint: string;
    data?: any;
  }) => {
    if (!isElectron) {
      // Fallback to regular fetch for web
      try {
        const response = await fetch(`http://localhost:8000${options.endpoint}`, {
          method: options.method,
          headers: options.data instanceof FormData ? {} : {
            'Content-Type': 'application/json',
          },
          body: options.data instanceof FormData ? options.data : (options.data ? JSON.stringify(options.data) : undefined),
        });
        const data = await response.json();
        return { success: response.ok, data, error: response.ok ? undefined : data.detail };
      } catch (error) {
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
    return await window.electronAPI.apiCall(options);
  }, [isElectron]);

  // Menu event handlers
  useEffect(() => {
    if (!isElectron) return;

    const handleNewDocument = () => {
      // Trigger new document action
      console.log('New document requested');
    };

    const handleOpenDocument = (_event: any, filePath: string) => {
      // Handle file open
      console.log('Open document:', filePath);
    };

    const handleSettings = () => {
      // Open settings
      console.log('Settings requested');
    };

    window.electronAPI.onMenuNewDocument(handleNewDocument);
    window.electronAPI.onMenuOpenDocument(handleOpenDocument);
    window.electronAPI.onMenuSettings(handleSettings);

    return () => {
      window.electronAPI.removeAllListeners('menu-new-document');
      window.electronAPI.removeAllListeners('menu-open-document');
      window.electronAPI.removeAllListeners('menu-settings');
    };
  }, [isElectron]);

  return {
    isElectron,
    selectFile,
    selectFolder,
    showMessageBox,
    getAppVersion,
    getStoreValue,
    setStoreValue,
    getAllStoreValues,
    clearStore,
    apiCall,
  };
};

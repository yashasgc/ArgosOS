import { useEffect, useCallback } from 'react';

export const useElectron = () => {
  const isElectron = typeof window !== 'undefined' && window.electronAPI;


  const apiCall = useCallback(async (options: {
    method: 'GET' | 'POST' | 'PUT' | 'DELETE';
    endpoint: string;
    data?: any;
  }) => {
    // Always use web fallback (fetch) for file uploads since FormData doesn't work through Electron IPC
    if (!isElectron || (options.data instanceof FormData)) {
      // Fallback to regular fetch for web
      try {
        const response = await fetch(`http://localhost:8000${options.endpoint}?t=${Date.now()}`, {
          method: options.method,
          headers: options.data instanceof FormData ? {} : {
            'Content-Type': 'application/json',
          },
          body: options.data instanceof FormData ? options.data : (options.data ? JSON.stringify(options.data) : undefined),
        });
        const data = await response.json();
        
        const errorMessage = response.ok ? undefined : (
          data.detail || 
          data.message || 
          data.error ||
          `HTTP ${response.status}: ${response.statusText}`
        );
        return { success: response.ok, data, error: errorMessage };
      } catch (error) {
        console.error('API call failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
    
    try {
      const result = await window.electronAPI.apiCall(options);
      return result;
    } catch (error) {
      console.error('Electron API error:', error);
      throw error;
    }
  }, [isElectron]);

  // Menu event handlers
  useEffect(() => {
    if (!isElectron) return;

    const handleNewDocument = () => {
      // Trigger new document action
    };

    const handleOpenDocument = (_event: any, filePath: string) => {
      // Handle file open
    };

    const handleSettings = () => {
      // Open settings
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
    apiCall,
  };
};

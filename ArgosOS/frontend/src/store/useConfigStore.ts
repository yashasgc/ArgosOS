import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ConfigState {
  apiBaseUrl: string;
  openaiApiKey: string;
  setApiBaseUrl: (url: string) => void;
  setOpenaiApiKey: (key: string) => void;
  reset: () => void;
}

export const useConfigStore = create<ConfigState>()(
  persist(
    (set) => ({
      apiBaseUrl: 'http://localhost:8000',
      openaiApiKey: '',
      setApiBaseUrl: (url: string) => {
        set({ apiBaseUrl: url });
        localStorage.setItem('argos_api_base_url', url);
      },
      setOpenaiApiKey: (key: string) => set({ openaiApiKey: key }),
      reset: () => {
        set({ apiBaseUrl: 'http://localhost:8000', openaiApiKey: '' });
        localStorage.removeItem('argos_api_base_url');
      },
    }),
    {
      name: 'argos-config',
      partialize: (state) => ({ 
        apiBaseUrl: state.apiBaseUrl, 
        openaiApiKey: state.openaiApiKey 
      }),
    }
  )
);

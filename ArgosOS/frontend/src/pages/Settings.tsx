import { useState, useEffect } from 'react';
import { useConfigStore } from '../store/useConfigStore';
import { Server, Key, Save, RotateCcw, CheckCircle, AlertCircle } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function SettingsPage() {
  const { apiBaseUrl, openaiApiKey, setApiBaseUrl, setOpenaiApiKey, reset } = useConfigStore();
  
  const [localApiBaseUrl, setLocalApiBaseUrl] = useState(apiBaseUrl);
  const [localOpenaiApiKey, setLocalOpenaiApiKey] = useState(openaiApiKey);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [connectionMessage, setConnectionMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    setLocalApiBaseUrl(apiBaseUrl);
    setLocalOpenaiApiKey(openaiApiKey);
  }, [apiBaseUrl, openaiApiKey]);

  const testConnection = async () => {
    setIsTestingConnection(true);
    setConnectionStatus('idle');
    setConnectionMessage('');

    let originalBaseURL: string | null = null;
    
    try {
      // Temporarily set the base URL for testing
      originalBaseURL = localStorage.getItem('argos_api_base_url');
      localStorage.setItem('argos_api_base_url', localApiBaseUrl);
      
      await apiClient.health();
      
      setConnectionStatus('success');
      setConnectionMessage('Connection successful! API is responding.');
      
      // Restore original base URL
      if (originalBaseURL) {
        localStorage.setItem('argos_api_base_url', originalBaseURL);
      } else {
        localStorage.removeItem('argos_api_base_url');
      }
    } catch (error: any) {
      setConnectionStatus('error');
      setConnectionMessage(error.response?.data?.detail || 'Connection failed. Please check your API URL.');
      
      // Restore original base URL
      if (originalBaseURL) {
        localStorage.setItem('argos_api_base_url', originalBaseURL);
      } else {
        localStorage.removeItem('argos_api_base_url');
      }
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');

    let originalBaseURL: string | null = null;
    
    try {
      // Test connection before saving
      originalBaseURL = localStorage.getItem('argos_api_base_url');
      localStorage.setItem('argos_api_base_url', localApiBaseUrl);
      
      await apiClient.health();
      
      // Save to store
      setApiBaseUrl(localApiBaseUrl);
      setOpenaiApiKey(localOpenaiApiKey);
      
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error: any) {
      setSaveStatus('error');
      setConnectionMessage('Cannot save invalid API URL. Please test connection first.');
      
      // Restore original base URL
      if (originalBaseURL) {
        localStorage.setItem('argos_api_base_url', originalBaseURL);
      } else {
        localStorage.removeItem('argos_api_base_url');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    reset();
    setLocalApiBaseUrl('http://localhost:8000');
    setLocalOpenaiApiKey('');
    setConnectionStatus('idle');
    setConnectionMessage('');
    setSaveStatus('idle');
  };

  const hasChanges = localApiBaseUrl !== apiBaseUrl || localOpenaiApiKey !== openaiApiKey;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Settings</h1>
            <p className="text-lg text-gray-600">
              Configure your ArgosOS connection and API settings
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          {/* API Configuration */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Server className="h-5 w-5 mr-2 text-blue-600" />
              API Configuration
            </h2>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="api-base-url" className="block text-sm font-medium text-gray-700 mb-2">
                  API Base URL
                </label>
                <div className="flex space-x-3">
                  <input
                    type="url"
                    id="api-base-url"
                    value={localApiBaseUrl}
                    onChange={(e) => setLocalApiBaseUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={testConnection}
                    disabled={isTestingConnection || !localApiBaseUrl.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {isTestingConnection ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <CheckCircle className="h-4 w-4" />
                    )}
                    <span>Test</span>
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  The base URL where your ArgosOS backend is running
                </p>
              </div>

              {/* Connection Status */}
              {connectionStatus !== 'idle' && (
                <div className={`p-3 rounded-md ${
                  connectionStatus === 'success' 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex items-center">
                    {connectionStatus === 'success' ? (
                      <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
                    )}
                    <span className={`text-sm ${
                      connectionStatus === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {connectionMessage}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* OpenAI Configuration */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Key className="h-5 w-5 mr-2 text-green-600" />
              OpenAI Configuration (Optional)
            </h2>
            
            <div>
              <label htmlFor="openai-api-key" className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                id="openai-api-key"
                value={localOpenaiApiKey}
                onChange={(e) => setLocalOpenaiApiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-sm text-gray-500 mt-1">
                Required for AI-powered search features. Your key is stored locally and never sent to our servers.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <div className="flex space-x-3">
              <button
                onClick={handleSave}
                disabled={!hasChanges || isSaving}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSaving ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span>Save Changes</span>
              </button>
              
              <button
                onClick={handleReset}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center space-x-2"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Reset to Defaults</span>
              </button>
            </div>

            {/* Save Status */}
            {saveStatus === 'success' && (
              <div className="flex items-center text-green-600">
                <CheckCircle className="h-5 w-5 mr-2" />
                <span className="text-sm font-medium">Settings saved!</span>
              </div>
            )}
            
            {saveStatus === 'error' && (
              <div className="flex items-center text-red-600">
                <AlertCircle className="h-5 w-5 mr-2" />
                <span className="text-sm font-medium">Save failed</span>
              </div>
            )}
          </div>
        </div>

        {/* Current Configuration Info */}
        <div className="mt-8 bg-gray-50 rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">API Base URL:</span>
              <span className="ml-2 text-gray-600 font-mono">{apiBaseUrl}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">OpenAI API Key:</span>
              <span className="ml-2 text-gray-600">
                {openaiApiKey ? '••••••••' + openaiApiKey.slice(-4) : 'Not set'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

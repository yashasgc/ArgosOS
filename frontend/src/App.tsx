import { useState, useEffect } from 'react';
import { Upload, FileText, Search, X, Sparkles, Settings, Eye, EyeOff } from 'lucide-react';
import { useElectron } from './hooks/useElectron';
import FileUpload from './components/FileUpload';
import './index.css';

interface Document {
  id: string;
  title: string;
  summary?: string;
  created_at: number;
  mime_type?: string;
  size_bytes?: number;
  tags: string[];
}

type TabId = 'upload' | 'documents' | 'search' | 'settings';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  count: number | null;
}

function App() {
  const { isElectron, apiCall } = useElectron();
  const [activeTab, setActiveTab] = useState<TabId>('upload');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Document[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [llmAvailable, setLlmAvailable] = useState<boolean | null>(null);
  const [directAnswer, setDirectAnswer] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKeySaved, setApiKeySaved] = useState(false);
  const [apiKeyStatus, setApiKeyStatus] = useState<{ configured: boolean; encrypted: boolean } | null>(null);


  const [loading, setLoading] = useState(false);


  const handleDeleteDocument = async (documentId: string) => {
    try {
      const result = await apiCall({
        method: 'DELETE',
        endpoint: `/api/documents/${documentId}`
      });

      if (result.success) {
        // Remove from local state
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
        setSearchResults(prev => prev.filter(doc => doc.id !== documentId));
        console.log('Document deleted successfully');
      } else {
        console.error('Failed to delete document:', result.error);
        // You could add a toast notification here
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      // You could add a toast notification here
    }
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);
    try {
      const result = await apiCall({
        method: 'GET',
        endpoint: `/api/search?query=${encodeURIComponent(query)}&limit=20`
      });

      if (result.success) {
        setSearchResults(result.data.results.documents || []);
        setLlmAvailable(result.data.results.llm_available || false);
        setDirectAnswer(result.data.results.processed_content?.direct_answer || null);
      } else {
        console.error('Search failed:', result.error);
        setSearchResults([]);
        setLlmAvailable(null);
        setDirectAnswer(null);
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // Load documents on startup
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const result = await apiCall({
          method: 'GET',
          endpoint: '/api/documents'
        });

        if (result.success) {
          setDocuments(result.data.documents || []);
        }
      } catch (error) {
        console.error('Failed to load documents:', error);
      }
    };

    loadDocuments();
  }, []);

  // Handle Enter key press for search
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      handleSearch(searchQuery);
    }
  };

  // Handle search button click
  const handleSearchClick = () => {
    if (searchQuery.trim()) {
      handleSearch(searchQuery);
    }
  };

  const checkApiKeyStatus = async () => {
    try {
      const result = await apiCall({
        method: 'GET',
        endpoint: '/v1/api-key/status'
      });
      
      if (result.success) {
        setApiKeyStatus(result.data);
      }
    } catch (error) {
      console.error('Failed to check API key status:', error);
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) return;
    
    setLoading(true);
    try {
      const result = await apiCall({
        method: 'POST',
        endpoint: '/v1/api-key',
        data: { api_key: apiKey, service: 'openai' }
      });

      if (result.success && result.data.encrypted) {
        setApiKeySaved(true);
        setTimeout(() => setApiKeySaved(false), 3000);
        // Add a small delay to ensure the save is fully processed
        await new Promise(resolve => setTimeout(resolve, 100));
        await checkApiKeyStatus();
        setApiKey(''); // Clear the input for security
      } else {
        // Handle case where API key was rejected
        const errorMessage = result.data?.message || result.error || 'Failed to save API key';
        alert(`API key rejected: ${errorMessage}`);
        setApiKey(''); // Clear the input
      }
    } catch (error) {
      console.error('Error saving API key:', error);
      alert('Failed to save API key. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearApiKey = async () => {
    if (loading) return; // Prevent multiple clicks
    
    setLoading(true);
    try {
      const result = await apiCall({
        method: 'DELETE',
        endpoint: '/v1/api-key'
      });

      if (result.success) {
        setApiKeyStatus({ configured: false, encrypted: false });
        setApiKey('');
      } else {
        throw new Error(result.error || 'Failed to clear API key');
      }
    } catch (error) {
      console.error('Error clearing API key:', error);
      alert('Failed to clear API key. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Search results are now handled by the backend API

  const tabs: Tab[] = [
    { id: 'upload', label: 'Upload Documents', icon: Upload, count: null },
    { id: 'documents', label: 'Document Library', icon: FileText, count: documents.length },
    { id: 'search', label: 'AI Search', icon: Search, count: null },
    { id: 'settings', label: 'Settings', icon: Settings, count: null }
  ];

  const handleOpenDocument = async (documentId: string) => {
    try {
      const result = await apiCall({
        method: 'GET',
        endpoint: `/api/documents/${documentId}/content`
      });

      if (result.success) {
        console.log('Document content loaded:', result);
        const documentData = result.data;
        // For text files, show content in a modal within the app
        if (documentData.mime_type?.startsWith('text/')) {
          console.log('Creating modal for text file:', documentData.mime_type);
          // Create a modal overlay
          const modal = document.createElement('div');
          modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            box-sizing: border-box;
          `;
          
          const modalContent = document.createElement('div');
          modalContent.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 24px;
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            position: relative;
          `;
          
          const closeButton = document.createElement('button');
          closeButton.innerHTML = '✕';
          closeButton.style.cssText = `
            position: absolute;
            top: 12px;
            right: 12px;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #666;
            padding: 4px;
            border-radius: 4px;
          `;
          closeButton.onclick = () => document.body.removeChild(modal);
          
          const title = document.createElement('h2');
          title.textContent = documentData.title;
          title.style.cssText = `
            margin: 0 0 16px 0;
            font-size: 24px;
            font-weight: 600;
            color: #1f2937;
          `;
          
          const content = document.createElement('pre');
          content.textContent = documentData.content;
          content.style.cssText = `
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            color: #374151;
            background: #f9fafb;
            padding: 16px;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
          `;
          
          modalContent.appendChild(closeButton);
          modalContent.appendChild(title);
          modalContent.appendChild(content);
          modal.appendChild(modalContent);
          
          // Close on backdrop click
          modal.onclick = (e) => {
            if (e.target === modal) {
              document.body.removeChild(modal);
            }
          };
          
          document.body.appendChild(modal);
        } else {
          console.log('Opening file directly:', documentData.mime_type);
          // For PDFs and other files, open them with system default application
          const downloadUrl = `http://localhost:8000/api/documents/${documentId}/download`;
          if (isElectron) {
            console.log('Opening file with system default application');
            // Download file first, then open with system default app
            try {
              const response = await fetch(downloadUrl);
              const arrayBuffer = await response.arrayBuffer();
              const uint8Array = new Uint8Array(arrayBuffer);
              
              // Pass the file data directly to Electron
              await window.electronAPI.openFileData(uint8Array, documentData.title || 'document.pdf');
            } catch (error) {
              console.error('Failed to open file:', error);
              // Fallback to window.open
              window.open(downloadUrl, '_blank');
            }
          } else {
            console.log('Opening file in browser');
            window.open(downloadUrl, '_blank');
          }
        }
      } else {
        console.error('Failed to open document:', result.error);
      }
    } catch (error) {
      console.error('Error opening document:', error);
    }
  };

  const renderDocumentCard = (doc: Document, showDelete = true) => (
    <div 
      key={doc.id} 
      className="card hover-lift cursor-pointer"
      onDoubleClick={() => handleOpenDocument(doc.id)}
      title="Double-click to open document"
    >
      <div className="flex items-start justify-between mb-3">
        <FileText className="w-8 h-8 text-blue-600 flex-shrink-0" />
        <div className="flex gap-2">
          <div
            className="text-slate-400 hover:text-blue-500 transition-colors p-2 hover:bg-blue-50 rounded-lg"
            title="Double-click to open document"
          >
            <Eye className="w-5 h-5" />
          </div>
          {showDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevent double-click from triggering
                handleDeleteDocument(doc.id);
              }}
              className="text-slate-400 hover:text-red-500 transition-colors p-2 hover:bg-red-50 rounded-lg"
              title="Delete document"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{doc.title}</h3>
      {doc.summary && doc.summary.trim() && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{doc.summary}</p>
      )}
      {doc.tags && doc.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {doc.tags.slice(0, 3).map((tag, index) => (
            <span key={index} className="px-2 py-1 bg-gray-100 rounded-full text-xs">
              {tag}
            </span>
          ))}
          {doc.tags.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 rounded-full text-xs">
              +{doc.tags.length - 3} more
            </span>
          )}
        </div>
      )}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  );

  const renderUploadTab = () => (
    <div className="animate-fade-in">
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Upload Your Documents</h2>
      <p className="text-gray-600 mb-8">
        Drag and drop files here or click to browse. Our AI will analyze and transform your documents into intelligent, searchable knowledge.
      </p>
      
      <FileUpload onUploadSuccess={(document) => {
        setDocuments(prev => [document, ...prev]);
        setActiveTab('documents');
      }} />
      
      <div className="mt-8 flex items-center justify-center text-sm text-gray-500">
        <Sparkles className="w-4 h-4 mr-2" />
        AI-Powered Analysis
        {isElectron && (
          <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
            Desktop App
          </span>
        )}
      </div>
    </div>
  );

  const renderDocumentsTab = () => (
    <div className="animate-fade-in">
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Document Library</h2>
      {documents.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-lg text-gray-500 mb-2">No documents yet</p>
          <p className="text-gray-400">Upload your first document to get started</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {documents.map(doc => renderDocumentCard(doc, true))}
        </div>
      )}
    </div>
  );

  const renderSearchTab = () => (
    <div className="animate-fade-in">
      <h2 className="text-3xl font-bold text-gray-900 mb-6">AI Search</h2>
      <div className="max-w-2xl mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search through your documents... (Press Enter to search)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="w-full px-10 pr-20 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all"
          />
          <button
            onClick={handleSearchClick}
            disabled={!searchQuery.trim() || searchLoading}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {searchLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              'Search'
            )}
          </button>
        </div>
      </div>
      
      {(searchQuery && searchResults.length > 0) || searchLoading ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Search Results for "{searchQuery}"
            </h3>
            {llmAvailable !== null && (
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                llmAvailable 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {llmAvailable ? '🤖 AI-Powered Search' : '📚 Using oldschool way (no API key found)'}
              </div>
            )}
          </div>
          {searchLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-gray-600">Searching...</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Direct Answer */}
              {directAnswer && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">Answer:</h3>
                  <p className="text-blue-800 whitespace-pre-wrap">{directAnswer}</p>
                </div>
              )}
              
              {/* Search Results */}
              {searchResults.length === 0 ? (
                <p className="text-gray-500">No documents found matching your search.</p>
              ) : (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Related Documents:</h3>
                  {searchResults.map(doc => renderDocumentCard(doc, false))}
                </div>
              )}
            </div>
          )}
        </div>
      ) : searchQuery && !searchLoading ? (
        <div className="text-center py-8">
          <p className="text-gray-500">Press Enter or click Search to find documents.</p>
        </div>
      ) : null}
    </div>
  );

  const renderSettingsTab = () => (
    <div className="animate-fade-in">
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Settings</h2>
      
      <div className="max-w-2xl space-y-8">
        {/* OpenAI API Key Section */}
        <div className="card">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">OpenAI API Configuration</h3>
            <p className="text-gray-600">
              Configure your OpenAI API key securely. The key is encrypted and stored on the backend server.
            </p>
          </div>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key
              </label>
              <div className="relative">
                <input
                  id="api-key"
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="input pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Your API key is encrypted and stored securely on the backend server.
              </p>
            </div>
            
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleSaveApiKey}
                disabled={!apiKey.trim() || loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {loading ? 'Saving...' : 'Save API Key'}
              </button>
              <button
                onClick={handleClearApiKey}
                disabled={loading}
                className="bg-red-100 text-red-700 px-4 py-2 rounded-lg hover:bg-red-200 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {loading ? 'Clearing...' : 'Clear Key'}
              </button>
            </div>
            
            {apiKeySaved && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-green-800 text-sm font-medium">
                  ✅ API key saved and encrypted successfully!
                </p>
              </div>
            )}
          </div>
        </div>

        {/* API Key Status */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">API Key Status</h3>
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${apiKeyStatus?.configured ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-gray-700">
              {apiKeyStatus?.configured ? 'API key is configured and encrypted' : 'No API key configured'}
            </span>
          </div>
          {apiKeyStatus?.configured && (
            <p className="text-sm text-gray-500 mt-2">
              Status: Encrypted and stored securely on backend
            </p>
          )}
        </div>

        {/* Usage Information */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Information</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <p>• API key is encrypted using Fernet encryption before storage</p>
            <p>• Key is stored securely on the backend server, not in your browser</p>
            <p>• Encryption key is stored separately for additional security</p>
            <p>• You can clear the key at any time for security</p>
            <p>• Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">OpenAI Platform</a></p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'upload': return renderUploadTab();
      case 'documents': return renderDocumentsTab();
      case 'search': return renderSearchTab();
      case 'settings': return renderSettingsTab();
      default: return null;
    }
  };

  // Load API key status on component mount
  useEffect(() => {
    checkApiKeyStatus();
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">ArgosOS</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map(({ id, label, icon: Icon, count }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`relative px-6 py-4 font-medium text-sm transition-all duration-200 whitespace-nowrap ${
                  activeTab === id
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-5 h-5" />
                  <span>{label}</span>
                  {count !== null && (
                    <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded-full text-xs font-semibold">
                      {count}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderTabContent()}
      </main>
    </div>
  );
}

export default App;

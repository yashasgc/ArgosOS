import { useState } from 'react';
import SearchResultCard from '../components/SearchResultCard';
import { apiClient } from '../lib/api';
import type { Document } from '../lib/api';
import { Search, Sparkles, Loader2, AlertCircle, FileText } from 'lucide-react';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Document[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await apiClient.search(query.trim());
      setSearchResults(response.data.documents);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch(e);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setSearchResults([]);
    setError(null);
    setHasSearched(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              AI-Powered Search
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Ask questions in natural language or search for specific content across all your documents.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-6 w-6 text-gray-400" />
            </div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question or search for content... (e.g., 'What are the key points about machine learning?' or 'Find documents about project planning')"
              className="w-full pl-12 pr-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
              disabled={isSearching}
            />
            <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
              {isSearching ? (
                <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
              ) : (
                <button
                  type="submit"
                  disabled={!query.trim()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Search</span>
                </button>
              )}
            </div>
          </div>
          
          {/* Search Tips */}
          <div className="mt-4 text-sm text-gray-600">
            <p className="flex items-center justify-center">
              <Sparkles className="h-4 w-4 mr-2 text-blue-500" />
              Try asking questions like "What are the main topics?" or "Find documents about..."
            </p>
          </div>
        </form>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-400 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Search Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Search Results */}
        {hasSearched && !isSearching && (
          <div>
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Search Results
                </h2>
                <p className="text-gray-600 mt-1">
                  {searchResults.length === 0 
                    ? 'No results found' 
                    : `Found ${searchResults.length} document${searchResults.length === 1 ? '' : 's'}`
                  }
                </p>
              </div>
              {hasSearched && (
                <button
                  onClick={clearSearch}
                  className="text-sm text-gray-500 hover:text-gray-700 border border-gray-300 px-3 py-1 rounded-md hover:bg-gray-50"
                >
                  Clear Search
                </button>
              )}
            </div>

            {/* Results */}
            {searchResults.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                <p className="text-gray-600 mb-4">
                  Try adjusting your search terms or ask a different question.
                </p>
                <div className="text-sm text-gray-500">
                  <p>Search tips:</p>
                  <ul className="mt-2 space-y-1">
                    <li>• Use different keywords or synonyms</li>
                    <li>• Try shorter, more general terms</li>
                    <li>• Check spelling and grammar</li>
                    <li>• Use quotes for exact phrases</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {searchResults.map((document) => (
                  <SearchResultCard
                    key={document.id}
                    document={document}
                    query={query}
                    onClick={() => console.log('View document:', document.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Initial State */}
        {!hasSearched && !isSearching && (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <Search className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to search</h3>
            <p className="text-gray-600">
              Enter your question or search terms above to find relevant documents.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

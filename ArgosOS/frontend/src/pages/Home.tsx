import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import FileCard from '../components/FileCard';
import type { Document } from '../lib/api';
import { Upload, FileText, Search, Zap } from 'lucide-react';

export default function Home() {
  const [recentUploads, setRecentUploads] = useState<Document[]>([]);

  const handleUploadSuccess = (document: Document) => {
    setRecentUploads(prev => [document, ...prev.slice(0, 4)]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to ArgosOS
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Your intelligent document management system. Upload, organize, and search through your documents with AI-powered insights.
            </p>
            
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
              <div className="bg-blue-50 p-4 rounded-lg">
                <Upload className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-900">{recentUploads.length}</div>
                <div className="text-sm text-blue-600">Documents</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <Search className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-900">AI</div>
                <div className="text-sm text-green-600">Powered Search</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <Zap className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-900">Fast</div>
                <div className="text-sm text-purple-600">Processing</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Upload Your Documents
          </h2>
          <p className="text-lg text-gray-600">
            Drag and drop files or click to browse. We'll process and index them for easy searching.
          </p>
        </div>
        
        <FileUpload onUploadSuccess={handleUploadSuccess} />
      </div>

      {/* Recent Uploads */}
      {recentUploads.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Recently Uploaded
            </h2>
            <p className="text-lg text-gray-600">
              Your latest documents are ready for searching and organization.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recentUploads.map((document) => (
              <FileCard
                key={document.id}
                document={document}
                onClick={() => console.log('View document:', document.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Features Section */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose ArgosOS?
            </h2>
            <p className="text-lg text-gray-600">
              Powerful features designed for modern document management
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Easy Upload</h3>
              <p className="text-gray-600">
                Drag and drop files or use the file picker. We support PDF, TXT, DOC, and more.
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <Search className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Search</h3>
              <p className="text-gray-600">
                Find documents by content, tags, or ask questions in natural language.
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 p-3 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                <FileText className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Organized</h3>
              <p className="text-gray-600">
                Automatic tagging and categorization to keep your documents organized.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

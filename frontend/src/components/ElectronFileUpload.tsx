import React, { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { useElectron } from '../hooks/useElectron';

interface UploadResult {
  id: string;
  filePath: string;
  fileName: string;
  status: 'uploading' | 'success' | 'error';
  progress: number;
  message?: string;
  document?: any;
}

export const ElectronFileUpload: React.FC = () => {
  const { selectFile, isElectron } = useElectron();
  const [uploads, setUploads] = useState<UploadResult[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = useCallback(async () => {
    if (!isElectron) {
      alert('File upload is only available in the Electron app');
      return;
    }

    const filePath = await selectFile();
    if (!filePath) return;

    const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || 'Unknown';
    const uploadId = Math.random().toString(36).substr(2, 9);

    const newUpload: UploadResult = {
      id: uploadId,
      filePath,
      fileName,
      status: 'uploading',
      progress: 0,
    };

    setUploads(prev => [...prev, newUpload]);
    setIsUploading(true);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploads(prev => prev.map(upload => 
          upload.id === uploadId 
            ? { ...upload, progress: Math.min(upload.progress + 10, 90) }
            : upload
        ));
      }, 200);

      // For now, let's simulate a successful upload since the backend isn't ready
      // In a real implementation, you would upload the file here
      setTimeout(() => {
        clearInterval(progressInterval);
        
        setUploads(prev => prev.map(upload => 
          upload.id === uploadId 
            ? { 
                ...upload, 
                status: 'success', 
                progress: 100, 
                message: 'Document processed successfully (simulated)',
                document: {
                  id: uploadId,
                  title: fileName,
                  summary: `Processed ${fileName} using OCR and LLM analysis`,
                  tags: ['document', 'processed', 'ocr']
                }
              }
            : upload
        ));
        
        setIsUploading(false);
      }, 2000);

    } catch (error) {
      setUploads(prev => prev.map(upload => 
        upload.id === uploadId 
          ? { 
              ...upload, 
              status: 'error', 
              progress: 100, 
              message: error instanceof Error ? error.message : 'Upload failed'
            }
          : upload
      ));
      setIsUploading(false);
    }
  }, [selectFile, isElectron]);

  const removeUpload = useCallback((uploadId: string) => {
    setUploads(prev => prev.filter(upload => upload.id !== uploadId));
  }, []);

  const clearAllUploads = useCallback(() => {
    setUploads([]);
  }, []);

  if (!isElectron) {
    return (
      <div className="p-8 text-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Electron App Required
        </h3>
        <p className="text-gray-600 mb-4">
          File upload functionality is only available in the desktop Electron app.
        </p>
        <p className="text-sm text-gray-500">
          Run <code className="bg-gray-200 px-2 py-1 rounded">npm run electron:dev</code> to start the desktop app.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div 
        className="p-8 text-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 hover:border-gray-400 transition-colors cursor-pointer"
        onClick={handleFileSelect}
      >
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Drop files here or click to browse
        </h3>
        <p className="text-gray-600 mb-4">
          Supports PDF, DOCX, TXT, and image files
        </p>
        <button 
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          disabled={isUploading}
        >
          <Upload className="w-4 h-4 mr-2" />
          {isUploading ? 'Processing...' : 'Select Files'}
        </button>
      </div>

      {/* Upload Results */}
      {uploads.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="text-lg font-medium text-gray-900">
              Upload Results ({uploads.length})
            </h4>
            <button
              onClick={clearAllUploads}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-3">
            {uploads.map((upload) => (
              <div key={upload.id} className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <File className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {upload.fileName}
                      </p>
                      <p className="text-xs text-gray-500">
                        {upload.filePath}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {upload.status === 'uploading' && (
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    )}
                    {upload.status === 'success' && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {upload.status === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    <button
                      onClick={() => removeUpload(upload.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Progress Bar */}
                {upload.status === 'uploading' && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${upload.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {upload.progress}% complete
                    </p>
                  </div>
                )}

                {/* Status Message */}
                {upload.message && (
                  <div className={`mt-2 text-sm ${
                    upload.status === 'success' ? 'text-green-600' : 
                    upload.status === 'error' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {upload.message}
                  </div>
                )}

                {/* Document Info */}
                {upload.document && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <p className="text-xs text-gray-600">
                      <strong>Document ID:</strong> {upload.document.id}
                    </p>
                    <p className="text-xs text-gray-600">
                      <strong>Title:</strong> {upload.document.title}
                    </p>
                    {upload.document.summary && (
                      <p className="text-xs text-gray-600 mt-1">
                        <strong>Summary:</strong> {upload.document.summary}
                      </p>
                    )}
                    {upload.document.tags && upload.document.tags.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-600 mb-1">
                          <strong>Tags:</strong>
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {upload.document.tags.map((tag: any, index: number) => (
                            <span 
                              key={index}
                              className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                            >
                              {tag.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

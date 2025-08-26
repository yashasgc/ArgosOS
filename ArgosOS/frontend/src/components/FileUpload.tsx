import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { apiClient } from '../lib/api';
import type { Document } from '../lib/api';

interface FileUploadProps {
  onUploadSuccess: (document: Document) => void;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setUploadStatus('idle');
    setUploadMessage('');

    try {
      const response = await apiClient.upload(file);
      setUploadStatus('success');
      setUploadMessage('File uploaded successfully!');
      onUploadSuccess(response.data.document);
      
      // Reset after 3 seconds
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadMessage('');
      }, 3000);
    } catch (error: any) {
      setUploadStatus('error');
      setUploadMessage(error.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setUploadStatus('idle');
    setUploadMessage('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Upload Area */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400',
          uploading && 'opacity-50 pointer-events-none'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {uploadStatus === 'idle' && (
          <>
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <div className="mt-4">
              <p className="text-lg font-medium text-gray-900">
                Drop files here or click to upload
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Supports PDF, TXT, DOC, and other text-based formats
              </p>
            </div>
            <input
              type="file"
              className="hidden"
              id="file-upload"
              onChange={handleFileSelect}
              accept=".pdf,.txt,.doc,.docx,.md,.rtf"
            />
            <label
              htmlFor="file-upload"
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
            >
              Choose File
            </label>
          </>
        )}

        {uploading && (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Uploading...</span>
          </div>
        )}

        {uploadStatus === 'success' && (
          <div className="flex items-center justify-center text-green-600">
            <CheckCircle className="h-8 w-8 mr-2" />
            <span className="text-lg font-medium">{uploadMessage}</span>
            <button
              onClick={resetUpload}
              className="ml-4 p-1 hover:bg-green-100 rounded-full"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="flex items-center justify-center text-red-600">
            <AlertCircle className="h-8 w-8 mr-2" />
            <span className="text-lg font-medium">{uploadMessage}</span>
            <button
              onClick={resetUpload}
              className="ml-4 p-1 hover:bg-red-100 rounded-full"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>

      {/* File Info */}
      {uploadStatus === 'success' && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <File className="h-5 w-5 text-green-600 mr-2" />
            <span className="text-sm text-green-800">
              File processed and stored successfully
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

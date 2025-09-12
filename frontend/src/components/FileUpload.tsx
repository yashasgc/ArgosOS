import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { useElectron } from '../hooks/useElectron';

interface Document {
  id: string;
  title: string;
  summary: string;
  created_at: number;
  tags: string[];
}

interface FileUploadProps {
  onUploadSuccess: (document: Document) => void;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const { apiCall } = useElectron();
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error' | 'warning'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const [processingSteps, setProcessingSteps] = useState({
    uploaded: false,
    extracted: false,
    summarized: false,
    tagged: false
  });

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

  const updateProcessingStep = (step: keyof typeof processingSteps) => {
    setProcessingSteps(prev => ({ ...prev, [step]: true }));
  };

  const resetProcessingSteps = () => {
    setProcessingSteps({
      uploaded: false,
      extracted: false,
      summarized: false,
      tagged: false
    });
  };

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setUploadStatus('idle');
    setUploadMessage('');
    resetProcessingSteps();

    try {
      // Step 1: Upload file
      updateProcessingStep('uploaded');
      
      const formData = new FormData();
      formData.append('file', file, file.name);
      
      const response = await apiCall({
        method: 'POST',
        endpoint: '/api/files/upload',
        data: formData
      });

      if (!response.success) {
        let errorMsg = 'Upload failed';
        
        if (response.error) {
          if (Array.isArray(response.error)) {
            // Handle Pydantic validation errors
            errorMsg = response.error.map(err => err.msg || err.message || 'Validation error').join(', ');
          } else if (typeof response.error === 'string') {
            errorMsg = response.error;
          } else if (response.error.message) {
            errorMsg = response.error.message;
          } else {
            errorMsg = JSON.stringify(response.error);
          }
        }
        
        console.error('Upload failed:', errorMsg);
        throw new Error(errorMsg);
      }

      // Step 2: Text extraction (simulated delay)
      updateProcessingStep('extracted');
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 3: AI processing (simulated delay)
      if (response.data.document.summary) {
        updateProcessingStep('summarized');
        await new Promise(resolve => setTimeout(resolve, 300));
      }
      
      if (response.data.document.tags && response.data.document.tags.length > 0) {
        updateProcessingStep('tagged');
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Check for API key warnings
      const hasApiKeyWarnings = response.data.errors?.some((error: string) => 
        error.includes('OpenAI API key not configured')
      );

      if (hasApiKeyWarnings) {
        setUploadStatus('warning');
        setUploadMessage('File uploaded successfully, but OpenAI API key not configured. AI features (summary, tags) are disabled.');
      } else {
        setUploadStatus('success');
        setUploadMessage('File processed successfully!');
      }
      
      onUploadSuccess(response.data.document);
      
      // Reset after 5 seconds
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadMessage('');
        resetProcessingSteps();
      }, 5000);
    } catch (error: any) {
      setUploadStatus('error');
      
      console.error('Upload error:', error);
      
      let errorMessage = 'Upload failed. Please try again.';
      
      if (typeof error === 'string') {
        errorMessage = error;
      } else if (error?.message) {
        errorMessage = error.message;
      } else if (error?.error) {
        if (Array.isArray(error.error)) {
          errorMessage = error.error.map((err: any) => err.msg || err.message || 'Validation error').join(', ');
        } else if (typeof error.error === 'string') {
          errorMessage = error.error;
        } else {
          errorMessage = JSON.stringify(error.error);
        }
      } else if (error && typeof error === 'object') {
        errorMessage = JSON.stringify(error);
      } else if (error?.detail) {
        errorMessage = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
      } else if (error) {
        errorMessage = JSON.stringify(error);
      }
      
      setUploadMessage(errorMessage);
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
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Processing...</span>
            </div>
            
            {/* Processing Steps Indicator */}
            <div className="space-y-3">
              <div className="text-sm font-medium text-gray-700 text-center">Processing Steps</div>
              <div className="space-y-2">
                {/* Upload Step */}
                <div className="flex items-center space-x-3">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                    processingSteps.uploaded 
                      ? "bg-green-500 text-white" 
                      : "bg-gray-200 text-gray-500"
                  )}>
                    {processingSteps.uploaded ? <CheckCircle className="h-4 w-4" /> : "1"}
                  </div>
                  <span className={cn(
                    "text-sm",
                    processingSteps.uploaded ? "text-green-600 font-medium" : "text-gray-500"
                  )}>
                    File Uploaded
                  </span>
                </div>

                {/* Extraction Step */}
                <div className="flex items-center space-x-3">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                    processingSteps.extracted 
                      ? "bg-green-500 text-white" 
                      : processingSteps.uploaded
                        ? "bg-blue-500 text-white animate-pulse"
                        : "bg-gray-200 text-gray-500"
                  )}>
                    {processingSteps.extracted ? <CheckCircle className="h-4 w-4" /> : "2"}
                  </div>
                  <span className={cn(
                    "text-sm",
                    processingSteps.extracted ? "text-green-600 font-medium" : 
                    processingSteps.uploaded ? "text-blue-600" : "text-gray-500"
                  )}>
                    Text Extraction
                  </span>
                </div>

                {/* Summary Step */}
                <div className="flex items-center space-x-3">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                    processingSteps.summarized 
                      ? "bg-green-500 text-white" 
                      : processingSteps.extracted
                        ? "bg-blue-500 text-white animate-pulse"
                        : "bg-gray-200 text-gray-500"
                  )}>
                    {processingSteps.summarized ? <CheckCircle className="h-4 w-4" /> : "3"}
                  </div>
                  <span className={cn(
                    "text-sm",
                    processingSteps.summarized ? "text-green-600 font-medium" : 
                    processingSteps.extracted ? "text-blue-600" : "text-gray-500"
                  )}>
                    AI Summary
                  </span>
                </div>

                {/* Tags Step */}
                <div className="flex items-center space-x-3">
                  <div className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                    processingSteps.tagged 
                      ? "bg-green-500 text-white" 
                      : processingSteps.summarized
                        ? "bg-blue-500 text-white animate-pulse"
                        : "bg-gray-200 text-gray-500"
                  )}>
                    {processingSteps.tagged ? <CheckCircle className="h-4 w-4" /> : "4"}
                  </div>
                  <span className={cn(
                    "text-sm",
                    processingSteps.tagged ? "text-green-600 font-medium" : 
                    processingSteps.summarized ? "text-blue-600" : "text-gray-500"
                  )}>
                    AI Tags
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {uploadStatus === 'success' && (
          <div className="text-center space-y-3">
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
            
            {/* AI Processing Summary */}
            <div className="text-sm text-green-700 bg-green-50 p-3 rounded-lg">
              <div className="flex items-center justify-center space-x-4">
                {processingSteps.summarized && (
                  <span className="flex items-center">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    AI Summary Generated
                  </span>
                )}
                {processingSteps.tagged && (
                  <span className="flex items-center">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    AI Tags Generated
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {uploadStatus === 'warning' && (
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center text-yellow-600">
              <AlertCircle className="h-8 w-8 mr-2" />
              <span className="text-lg font-medium">{uploadMessage}</span>
              <button
                onClick={resetUpload}
                className="ml-4 p-1 hover:bg-yellow-100 rounded-full"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            {/* API Key Warning */}
            <div className="text-sm text-yellow-700 bg-yellow-50 p-3 rounded-lg">
              <div className="flex items-center justify-center">
                <AlertCircle className="h-4 w-4 mr-2" />
                <span>Configure OpenAI API key to enable AI features</span>
              </div>
            </div>
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
          <div className="space-y-2">
            <div className="flex items-center">
              <File className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-sm text-green-800 font-medium">
                File processed and stored successfully
              </span>
            </div>
            
            {/* Processing Details */}
            <div className="text-xs text-green-700 space-y-1">
              <div>✅ Text extraction completed</div>
              {processingSteps.summarized && <div>✅ AI summary generated</div>}
              {processingSteps.tagged && <div>✅ AI tags generated</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

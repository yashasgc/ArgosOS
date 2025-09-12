import { FileText, Tag, Calendar, Eye, Sparkles } from 'lucide-react';
import { cn } from '../lib/utils';

interface Document {
  id: string;
  title: string;
  summary?: string;
  created_at: number;
  mime_type?: string;
  size_bytes?: number;
  tags: string[];
}

interface FileCardProps {
  document: Document;
  onClick?: () => void;
  className?: string;
}

export default function FileCard({ document, onClick, className }: FileCardProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('text') || mimeType.includes('txt')) return '📝';
    if (mimeType.includes('doc') || mimeType.includes('word')) return '📘';
    if (mimeType.includes('md')) return '📖';
    return '📁';
  };

  const truncateSummary = (summary: string | undefined, maxLength: number = 150) => {
    if (!summary) return 'No summary available';
    if (summary.length <= maxLength) return summary;
    return summary.substring(0, maxLength) + '...';
  };

  return (
    <div
      className={cn(
        'bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getFileIcon(document.mime_type || '')}</span>
          <div>
            <h3 className="font-medium text-gray-900 truncate max-w-[200px]">
              {document.title}
            </h3>
            <p className="text-xs text-gray-500">{document.mime_type || 'Unknown type'}</p>
          </div>
        </div>
        <button className="p-1 hover:bg-gray-100 rounded">
          <Eye className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {/* Content Preview */}
      <div className="mb-3">
        <p className="text-sm text-gray-600 line-clamp-3">
          {truncateSummary(document.summary)}
        </p>
      </div>

      {/* Tags */}
      {document.tags && document.tags.length > 0 && (
        <div className="mb-3">
          <div className="flex flex-wrap gap-1">
            {document.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                <Tag className="h-3 w-3 mr-1" />
                {tag}
              </span>
            ))}
            {document.tags.length > 3 && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                +{document.tags.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            <Sparkles className="h-3 w-3 mr-1" />
            {formatFileSize(document.size_bytes || 0)}
          </div>
          <div className="flex items-center">
            <Calendar className="h-3 w-3 mr-1" />
            {formatDate(document.created_at)}
          </div>
        </div>
        <div className="flex items-center">
          <FileText className="h-3 w-3 mr-1" />
          {document.id.slice(0, 8)}...
        </div>
      </div>
    </div>
  );
}

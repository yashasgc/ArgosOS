import { Search, Tag, Calendar, File, Eye } from 'lucide-react';
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

interface SearchResultCardProps {
  document: Document;
  query: string;
  onClick?: () => void;
  className?: string;
}

export default function SearchResultCard({ document, query, onClick, className }: SearchResultCardProps) {
  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('text') || mimeType.includes('txt')) return '📝';
    if (mimeType.includes('doc') || mimeType.includes('word')) return '📘';
    if (mimeType.includes('md')) return '📖';
    return '📁';
  };

  const highlightQuery = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const getRelevantSnippet = (summary: string | undefined, query: string, maxLength: number = 200) => {
    if (!summary) return 'No summary available';
    
    if (!query.trim()) {
      return summary.length > maxLength ? summary.substring(0, maxLength) + '...' : summary;
    }

    const queryLower = query.toLowerCase();
    const summaryLower = summary.toLowerCase();
    const queryIndex = summaryLower.indexOf(queryLower);
    
    if (queryIndex === -1) {
      return summary.length > maxLength ? summary.substring(0, maxLength) + '...' : summary;
    }

    const start = Math.max(0, queryIndex - 50);
    const end = Math.min(summary.length, queryIndex + query.length + 50);
    let snippet = summary.substring(start, end);
    
    if (start > 0) snippet = '...' + snippet;
    if (end < summary.length) snippet = snippet + '...';
    
    return snippet;
  };

  const snippet = getRelevantSnippet(document.summary, query);

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
            <h3 className="font-medium text-gray-900 truncate max-w-[250px]">
              {highlightQuery(document.title, query)}
            </h3>
            <p className="text-xs text-gray-500">{document.mime_type || 'Unknown type'}</p>
          </div>
        </div>
        <button className="p-1 hover:bg-gray-100 rounded">
          <Eye className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {/* Search Result Snippet */}
      <div className="mb-3">
        <div className="flex items-start space-x-2">
          <Search className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-gray-600 leading-relaxed">
            {highlightQuery(snippet, query)}
          </p>
        </div>
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
            <File className="h-3 w-3 mr-1" />
            {(document.size_bytes || 0) > 0 ? `${((document.size_bytes || 0) / 1024).toFixed(1)} KB` : 'Unknown size'}
          </div>
          <div className="flex items-center">
            <Calendar className="h-3 w-3 mr-1" />
            {formatDate(document.created_at)}
          </div>
        </div>
        <div className="flex items-center">
          <Search className="h-3 w-3 mr-1 text-blue-500" />
          Match found
        </div>
      </div>
    </div>
  );
}

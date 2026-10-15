import React from 'react';
import ReactMarkdown from 'react-markdown';

interface MarkdownViewProps {
  content: string;
  className?: string;
}

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, className = '' }) => {
  if (!content) return null;

  return (
    <div className={`markdown-view space-y-2 text-xs leading-relaxed text-slate-200 ${className}`}>
      <ReactMarkdown
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-base font-bold text-sky-300 mt-3 mb-1.5 border-b border-slate-700/60 pb-1" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-sm font-semibold text-sky-200 mt-2.5 mb-1" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xs font-semibold text-amber-300 mt-2 mb-0.5" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="text-xs text-slate-300 leading-relaxed my-1" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-4 space-y-1 my-1.5 text-slate-300" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-4 space-y-1 my-1.5 text-slate-300" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="text-xs leading-relaxed" {...props} />
          ),
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-white" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic text-slate-400" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-2 border-sky-500 pl-3 py-1.5 my-2 bg-sky-950/20 text-slate-300 text-xs rounded-r"
              {...props}
            />
          ),
          code: ({ node, ...props }) => (
            <code className="bg-slate-800 text-amber-300 px-1.5 py-0.5 rounded font-mono text-[11px]" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

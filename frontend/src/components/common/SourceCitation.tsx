import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { PolicyCitation } from '../../types';

interface SourceCitationProps {
  citation: PolicyCitation;
  defaultExpanded?: boolean;
}

export const SourceCitationView: React.FC<SourceCitationProps> = ({
  citation,
  defaultExpanded = false,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0e1627] p-3 text-xs space-y-1.5 transition-all">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sky-400 font-medium">
          <BookOpen className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate">{citation.document_title || citation.document_id}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
            Relevance: {(citation.relevance_score * 100).toFixed(0)}%
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-slate-400 hover:text-slate-200 transition p-0.5 cursor-pointer"
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      <div className="text-[11px] text-slate-400 flex items-center gap-2">
        <FileText className="h-3 w-3" />
        <span>Section: {citation.section || 'General Guidance'}</span>
        {citation.source_file && (
          <span className="text-slate-500 font-mono text-[10px]">({citation.source_file})</span>
        )}
      </div>

      {expanded && (
        <div className="mt-2 pt-2 border-t border-slate-800/80 text-slate-300 bg-slate-950/60 p-2.5 rounded font-sans leading-relaxed text-[11px]">
          "{citation.excerpt}"
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  FileText,
  Upload,
  RefreshCw,
  Search,
  CheckCircle,
  AlertTriangle,
  FileCode,
  Layers,
  Database,
  Trash2,
  ExternalLink,
  ShieldAlert,
  Info,
  Clock,
  ChevronRight,
  Filter,
  Check,
  X,
  File,
  Copy
} from 'lucide-react';
import { api } from '../../services/api';
import { KnowledgeDocItem, KnowledgeManifestStatus } from '../../types';
import { MarkdownView } from '../../components/common/MarkdownView';
import { Modal } from '../../components/common/Modal';
import { ConfirmActionDialog } from '../../components/common/ConfirmActionDialog';

export const KnowledgeBase: React.FC = () => {
  // State
  const [documents, setDocuments] = useState<KnowledgeDocItem[]>([]);
  const [manifestStatus, setManifestStatus] = useState<KnowledgeManifestStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedFileType, setSelectedFileType] = useState('all');

  // Document Detail Drawer
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocItem | null>(null);
  const [docDetail, setDocDetail] = useState<any | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Ingestion & Action State
  const [isIngesting, setIsIngesting] = useState(false);
  const [actionDocId, setActionDocId] = useState<string | null>(null);
  const [deleteTargetDocId, setDeleteTargetDocId] = useState<string | null>(null);
  const [copiedExcerpt, setCopiedExcerpt] = useState(false);

  // Upload State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('regulations');
  const [uploading, setUploading] = useState(false);

  // Retrieval Test Playground
  const [testQuery, setTestQuery] = useState('What are the FATF recommendations for wire transfers?');
  const [testTopK, setTestTopK] = useState(3);
  const [testSearching, setTestSearching] = useState(false);
  const [testResponse, setTestResponse] = useState<any | null>(null);

  // Load Data
  useEffect(() => {
    fetchKnowledgeData();
  }, [selectedCategory, selectedFileType]);

  const fetchKnowledgeData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, docsRes] = await Promise.all([
        api.getKnowledgeStatus().catch(() => null),
        api.getKnowledgeDocuments({
          category: selectedCategory,
          file_type: selectedFileType,
          search: searchQuery
        }).catch(() => ({ total: 0, items: [] }))
      ]);

      if (statusRes) setManifestStatus(statusRes);
      if (docsRes && docsRes.items) setDocuments(docsRes.items);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch knowledge base documents.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshAll = async (force = false) => {
    setIsIngesting(true);
    setSuccessMsg(null);
    setError(null);
    try {
      const res = await api.triggerKnowledgeIngest(force);
      setSuccessMsg(`Ingestion completed: ${res.details?.total_chunks_indexed || 0} vector chunks processed.`);
      await fetchKnowledgeData();
    } catch (err: any) {
      setError(`Ingestion failed: ${err.message}`);
    } finally {
      setIsIngesting(false);
    }
  };

  const handleReindexSingle = async (docId: string) => {
    setActionDocId(docId);
    setError(null);
    try {
      await api.triggerDocumentReindex(docId);
      setSuccessMsg(`Document ${docId} successfully re-indexed.`);
      await fetchKnowledgeData();
    } catch (err: any) {
      setError(`Reindex failed: ${err.message}`);
    } finally {
      setActionDocId(null);
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    setActionDocId(docId);
    setError(null);
    try {
      await api.deleteKnowledgeDocument(docId);
      setSuccessMsg(`Document '${docId}' removed from vector index. Source file preserved in repository.`);
      if (selectedDoc?.doc_id === docId) setSelectedDoc(null);
      setDeleteTargetDocId(null);
      await fetchKnowledgeData();
    } catch (err: any) {
      setError(`Deletion error: ${err.message}`);
    } finally {
      setActionDocId(null);
    }
  };

  const handleOpenDetail = async (doc: KnowledgeDocItem) => {
    setSelectedDoc(doc);
    setLoadingDetail(true);
    try {
      const detail = await api.getKnowledgeDocumentDetail(doc.doc_id);
      setDocDetail(detail);
    } catch (e) {
      setDocDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadKnowledgeDocument(uploadFile, uploadCategory);
      setSuccessMsg(`File '${uploadFile.name}' uploaded and ingested successfully.`);
      setShowUploadModal(false);
      setUploadFile(null);
      await fetchKnowledgeData();
    } catch (err: any) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleExecuteSearchTest = async () => {
    if (!testQuery.trim()) return;
    setTestSearching(true);
    try {
      const res = await api.searchKnowledge(testQuery, testTopK);
      setTestResponse(res);
    } catch (err: any) {
      setError(`Retrieval search failed: ${err.message}`);
    } finally {
      setTestSearching(false);
    }
  };

  const categories = [
    { id: 'all', label: 'All Categories' },
    { id: 'regulations', label: 'Regulations' },
    { id: 'aml_kyc', label: 'AML / KYC' },
    { id: 'fraud_patterns', label: 'Fraud Patterns' },
    { id: 'internal_policies', label: 'Internal Policies' },
    { id: 'research', label: 'Research' },
    { id: 'dataset_documentation', label: 'Dataset Docs' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                Policies & Documents
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Document Search Index
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Indexed regulatory compliance manuals, document search index, and verified policy passages
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => handleRefreshAll(false)}
            disabled={isIngesting}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isIngesting ? 'animate-spin text-sky-400' : ''}`} />
            <span>Incremental Ingest</span>
          </button>
          <button
            onClick={() => handleRefreshAll(true)}
            disabled={isIngesting}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 text-xs font-medium transition-colors disabled:opacity-50"
          >
            <Layers className="h-3.5 w-3.5 text-sky-400" />
            <span>Re-index All</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-lg shadow-sky-600/20 transition-all"
          >
            <Upload className="h-3.5 w-3.5" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-rose-400 hover:text-rose-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {successMsg && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="ml-auto text-emerald-400 hover:text-emerald-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Overview Metric Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span>Total Documents</span>
            <FileText className="h-4 w-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {manifestStatus?.manifest.total_indexed ?? documents.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1.5">
            <span className="text-emerald-400 font-medium">
              {documents.filter(d => d.file_type === 'PDF').length} PDFs
            </span>
            <span>•</span>
            <span className="text-sky-400 font-medium">
              {documents.filter(d => d.file_type === 'MD').length} Markdown
            </span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span>Indexed Chunks</span>
            <Layers className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {manifestStatus?.manifest.total_chunks ?? documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Chroma Vector Collection Active
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span>Embedding Model</span>
            <Database className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-sm font-semibold text-slate-200 font-mono truncate">
            {manifestStatus?.embedding_model || 'all-MiniLM-L6-v2'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            384-dimensional dense vectors
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1.5">
            <span>Ingestion Health</span>
            <CheckCircle className="h-4 w-4 text-teal-400" />
          </div>
          <div className="text-base font-semibold text-teal-400 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
            {manifestStatus?.status || 'HEALTHY'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 truncate">
            Last update: {manifestStatus?.manifest.last_updated ? new Date(manifestStatus.manifest.last_updated).toLocaleTimeString() : 'Recent'}
          </div>
        </div>
      </div>

      {/* Main Content Area: Document Inventory + Search Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Document Inventory */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-4">
            {/* Search and Filters Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Filter by title, filename, or document ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-800/80 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="bg-slate-800/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.label}
                    </option>
                  ))}
                </select>

                <select
                  value={selectedFileType}
                  onChange={(e) => setSelectedFileType(e.target.value)}
                  className="bg-slate-800/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="all">All Types</option>
                  <option value="PDF">PDF</option>
                  <option value="MD">Markdown</option>
                  <option value="TXT">Plain Text</option>
                  <option value="CSV">CSV</option>
                </select>
              </div>
            </div>

            {/* Document Inventory Table */}
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-800/50 text-slate-400 font-semibold border-b border-slate-800">
                    <th className="py-2.5 px-3">Document & Provenance</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3 text-center">Pages / Chunks</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        <div className="flex items-center justify-center gap-2">
                          <RefreshCw className="h-4 w-4 animate-spin text-sky-400" />
                          <span>Loading knowledge documents...</span>
                        </div>
                      </td>
                    </tr>
                  ) : documents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        No documents found matching the filter criteria.
                      </td>
                    </tr>
                  ) : (
                    documents.map((doc) => {
                      const isPdf = doc.file_type === 'PDF';
                      const isMd = doc.file_type === 'MD';
                      return (
                        <tr
                          key={doc.id || doc.doc_id}
                          className="hover:bg-slate-800/30 transition-colors cursor-pointer group"
                          onClick={() => handleOpenDetail(doc)}
                        >
                          <td className="py-3 px-3">
                            <div className="flex items-start gap-2.5">
                              <div
                                className={`p-1.5 rounded-md mt-0.5 shrink-0 ${
                                  isPdf
                                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                    : isMd
                                    ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                }`}
                              >
                                {isPdf ? (
                                  <FileText className="h-4 w-4" />
                                ) : isMd ? (
                                  <FileCode className="h-4 w-4" />
                                ) : (
                                  <File className="h-4 w-4" />
                                )}
                              </div>
                              <div className="min-w-0">
                                <div className="font-medium text-slate-200 group-hover:text-sky-300 truncate max-w-xs sm:max-w-md">
                                  {doc.title}
                                </div>
                                <div className="text-[11px] text-slate-500 truncate flex items-center gap-2 mt-0.5">
                                  <span className="font-mono">{doc.file_name}</span>
                                  {doc.source_type && (
                                    <span
                                      className={`px-1 rounded text-[9px] uppercase font-mono ${
                                        doc.source_type === 'official_regulation'
                                          ? 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                                          : 'bg-amber-950 text-amber-300 border border-amber-800'
                                      }`}
                                    >
                                      {doc.source_type === 'official_regulation' ? 'Official' : 'Sample/Internal'}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </td>

                          <td className="py-3 px-3 font-mono text-[11px] text-slate-300">
                            {doc.file_type}
                          </td>

                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 border border-slate-700 capitalize">
                              {doc.category.replace('_', ' ')}
                            </span>
                          </td>

                          <td className="py-3 px-3 text-center">
                            <div className="font-mono text-slate-200 text-xs">
                              {doc.chunk_count} <span className="text-slate-500 text-[10px]">chunks</span>
                            </div>
                            {isPdf && doc.page_count && (
                              <div className="text-[10px] text-slate-500 font-mono">
                                {doc.page_count} pages
                              </div>
                            )}
                          </td>

                          <td className="py-3 px-3">
                            <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                              <CheckCircle className="h-3 w-3" />
                              Indexed
                            </span>
                          </td>

                          <td className="py-3 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                title="Re-index this document"
                                onClick={() => handleReindexSingle(doc.doc_id)}
                                disabled={actionDocId === doc.doc_id}
                                className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-sky-300 transition-colors disabled:opacity-40"
                              >
                                <RefreshCw className={`h-3.5 w-3.5 ${actionDocId === doc.doc_id ? 'animate-spin text-sky-400' : ''}`} />
                              </button>
                              <button
                                title="Remove from Vector Index (Preserves file)"
                                onClick={() => handleDeleteDoc(doc.doc_id)}
                                disabled={actionDocId === doc.doc_id}
                                className="p-1 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors disabled:opacity-40"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Col: RAG Semantic Retrieval Playground */}
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-4">
            <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
              <Search className="h-4 w-4 text-sky-400" />
              <span>Semantic Retrieval Playground</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Test semantic queries live against indexed PDFs and policies. Inspect citations, page numbers, and synthesized answers.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Natural Language Query</label>
                <textarea
                  rows={3}
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  className="w-full p-2.5 bg-slate-800/80 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none"
                  placeholder="e.g. What are the FATF recommendations for wire transfers?"
                />
              </div>

              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <label className="text-[11px] text-slate-400">Top Citations:</label>
                  <select
                    value={testTopK}
                    onChange={(e) => setTestTopK(Number(e.target.value))}
                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
                  >
                    <option value={2}>Top 2</option>
                    <option value={3}>Top 3</option>
                    <option value={4}>Top 4</option>
                    <option value={6}>Top 6</option>
                  </select>
                </div>

                <button
                  onClick={handleExecuteSearchTest}
                  disabled={testSearching || !testQuery.trim()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                >
                  <Search className={`h-3.5 w-3.5 ${testSearching ? 'animate-spin' : ''}`} />
                  <span>{testSearching ? 'Querying...' : 'Test Retrieval'}</span>
                </button>
              </div>
            </div>

            {/* Test Results Output */}
            {testResponse && (
              <div className="pt-3 border-t border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">
                    Results: {testResponse.results_count} Citations
                  </span>
                  {testResponse.has_evidence ? (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      Evidence Found
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      Insufficient Evidence
                    </span>
                  )}
                </div>

                {/* Synthesis Output */}
                {testResponse.synthesis && (
                  <div className="p-3 rounded-lg bg-slate-800/70 border border-slate-700/80 text-xs text-slate-200 space-y-2">
                    <div className="text-[10px] uppercase font-mono text-sky-400 font-semibold tracking-wider">
                      Synthesized Grounded Answer
                    </div>
                    <MarkdownView content={testResponse.synthesis} />
                  </div>
                )}

                {/* Retrieved Citations List */}
                <div className="space-y-2">
                  <div className="text-[11px] font-semibold text-slate-400">Retrieved Sources:</div>
                  {testResponse.citations?.map((c: any, i: number) => (
                    <div
                      key={i}
                      className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition-colors text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="font-medium text-sky-300 truncate text-[11px]">
                          {c.document_title}
                        </div>
                        <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.2 rounded border border-emerald-800">
                          Score: {(c.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                        <span className="text-slate-300">{c.source_file}</span>
                        <span>•</span>
                        <span className="text-amber-400 font-semibold">
                          {c.page_number ? `Page ${c.page_number}` : c.section}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 italic line-clamp-3">
                        "{c.excerpt}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Centered Document Detail Modal */}
      {selectedDoc && (
        <Modal
          isOpen={!!selectedDoc}
          onClose={() => setSelectedDoc(null)}
          maxWidth="4xl"
          icon={<FileText className="h-5 w-5 text-sky-400" />}
          title={selectedDoc.title}
          subtitle={`Document ID: ${selectedDoc.doc_id} • Status: ${selectedDoc.status || 'INDEXED'} • Version: ${selectedDoc.version || '1.0'}`}
          badge={
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 uppercase font-semibold">
              {selectedDoc.status || 'INDEXED'}
            </span>
          }
          actions={
            <div className="flex items-center justify-between w-full">
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition cursor-pointer"
              >
                Close
              </button>
              <div className="flex items-center gap-2.5">
                <button
                  onClick={() => handleReindexSingle(selectedDoc.doc_id)}
                  disabled={actionDocId === selectedDoc.doc_id}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 text-xs font-medium transition cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${actionDocId === selectedDoc.doc_id ? 'animate-spin' : ''}`} />
                  {actionDocId === selectedDoc.doc_id ? 'Refreshing Index...' : 'Refresh Indexed Content'}
                </button>
                <button
                  onClick={() => setDeleteTargetDocId(selectedDoc.doc_id)}
                  disabled={actionDocId === selectedDoc.doc_id}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-medium transition cursor-pointer disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Remove from Vector Index
                </button>
              </div>
            </div>
          }
        >
          <div className="space-y-5">
            {/* Metadata Fields Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase font-mono font-semibold">Format & Pages</span>
                <span className="font-mono text-slate-100 font-medium text-xs mt-0.5 block">
                  {selectedDoc.file_type} • {selectedDoc.page_count} {selectedDoc.page_count === 1 ? 'page' : 'pages'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase font-mono font-semibold">Indexed Sections</span>
                <span className="font-mono text-emerald-400 font-semibold text-xs mt-0.5 block">
                  {selectedDoc.chunk_count} vector chunks
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase font-mono font-semibold">Category</span>
                <span className="text-slate-100 capitalize font-medium text-xs mt-0.5 block truncate">
                  {selectedDoc.category.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase font-mono font-semibold">Source Type</span>
                <span className="text-slate-100 capitalize font-medium text-xs mt-0.5 block truncate">
                  {selectedDoc.source_type.replace(/_/g, ' ')}
                </span>
              </div>
            </div>

            {/* Content Hash Provenance & File Attributes */}
            <div className="p-3.5 rounded-xl bg-[#0b1220] border border-slate-800/80 text-xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span className="font-mono uppercase font-semibold text-[10px]">SHA-256 Provenance Fingerprint</span>
                {selectedDoc.file_name && (
                  <span className="font-mono text-slate-400">File: {selectedDoc.file_name}</span>
                )}
              </div>
              <div className="font-mono text-[11px] text-sky-400/90 break-all bg-slate-950 p-2 rounded-lg border border-slate-900 select-all">
                {selectedDoc.content_hash || 'SHA-256 registered on ingest'}
              </div>
            </div>

            {/* Extracted Document Content Preview */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-sky-400" />
                  Extracted Document Content Preview
                </span>
                <div className="flex items-center gap-2">
                  {docDetail?.total_characters && (
                    <span className="text-[10px] font-mono text-slate-400">
                      {docDetail.total_characters.toLocaleString()} characters total
                    </span>
                  )}
                  {docDetail?.content_preview && (
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(docDetail.content_preview);
                        setCopiedExcerpt(true);
                        setTimeout(() => setCopiedExcerpt(false), 2000);
                      }}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-mono transition cursor-pointer"
                    >
                      {copiedExcerpt ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      {copiedExcerpt ? 'Copied' : 'Copy Text'}
                    </button>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs font-mono text-slate-300 max-h-[380px] overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
                {loadingDetail ? (
                  <div className="flex items-center justify-center p-8 text-slate-500 gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-sky-400" />
                    <span>Loading extracted document preview...</span>
                  </div>
                ) : (
                  docDetail?.content_preview || 'No text preview available for this document.'
                )}
              </div>

              {docDetail?.has_more_content && (
                <div className="p-2.5 rounded-lg bg-sky-950/30 border border-sky-800/40 text-[11px] text-sky-300 flex items-center gap-2">
                  <Info className="h-3.5 w-3.5 shrink-0" />
                  <span>
                    Showing excerpt preview. Full text is indexed in the ChromaDB vector database and available during multi-agent investigations.
                  </span>
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Confirmation Dialog for Destructive Removal */}
      <ConfirmActionDialog
        isOpen={!!deleteTargetDocId}
        title="Remove Document from Vector Index"
        message={`Are you sure you want to remove '${deleteTargetDocId}' from the vector retrieval index? The original source file will be preserved in storage, but its embeddings will no longer be retrieved during risk assessments.`}
        confirmLabel="Remove from Vector Index"
        cancelLabel="Cancel"
        isDestructive={true}
        loading={actionDocId === deleteTargetDocId}
        onConfirm={() => deleteTargetDocId && handleDeleteDoc(deleteTargetDocId)}
        onCancel={() => setDeleteTargetDocId(null)}
      />

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-[#0c1324] border border-slate-800 rounded-xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                <Upload className="h-4 w-4 text-sky-400" />
                Upload Knowledge Document
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Target Category</label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="regulations">Regulations (Official Regulatory Directives)</option>
                  <option value="aml_kyc">AML / KYC Standards</option>
                  <option value="fraud_patterns">Fraud Patterns & Typologies</option>
                  <option value="internal_policies">Internal Policies & Procedures</option>
                  <option value="research">Academic & Industry Research</option>
                  <option value="dataset_documentation">Dataset Documentation</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">Select File (.pdf, .md, .txt, .html, .csv, .docx)</label>
                <input
                  type="file"
                  accept=".pdf,.md,.markdown,.txt,.html,.htm,.csv,.docx"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-sky-600/20 file:text-sky-300 hover:file:bg-sky-600/30 cursor-pointer"
                />
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <div>• Automatic page-by-page text extraction and chunking.</div>
                <div>• SHA-256 deduplication and manifest registration.</div>
                <div>• 50 MB maximum file size limit.</div>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-lg disabled:opacity-50"
                >
                  {uploading ? 'Uploading & Ingesting...' : 'Upload & Ingest'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default KnowledgeBase;

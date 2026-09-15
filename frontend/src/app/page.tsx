'use client';

import React, { useState } from 'react';
import { UploadZone } from '../components/UploadZone';
import { ChatInterface } from '../components/ChatInterface';
import { Suggestions } from '../components/Suggestions';
import { TopicsList } from '../components/TopicsList';
import { UploadResponse, TopicItem } from '../types';
import { fetchSuggestions, fetchTopics } from '../lib/api';
import { Layers, Database, Cpu, Sparkles } from 'lucide-react';

export default function Home() {
  const [documentId, setDocumentId] = useState<string | undefined>();
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [topics, setTopics] = useState<TopicItem[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<string | undefined>();

  const handleUploadSuccess = async (res: UploadResponse) => {
    setDocumentId(res.document_id);

    try {
      const fetchedSuggestions = await fetchSuggestions(res.document_id);
      setSuggestions(fetchedSuggestions);

      const fetchedTopics = await fetchTopics(res.document_id);
      setTopics(fetchedTopics);
    } catch (err) {
      console.error('Error fetching document metadata:', err);
    }
  };

  return (
    <main className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto">
      {/* App Header */}
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 border-b border-slate-700/60 pb-6 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-8 h-8 text-indigo-400" />
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              Single-Source Retrieval
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Production-grade RAG pipeline with FAISS, HuggingFace, Cross-Encoder & RAGAS evaluation
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-300">
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-lg">
            <Database className="w-3.5 h-3.5 text-indigo-400" /> FAISS Vector Store
          </div>
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-lg">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" /> Cross-Encoder Reranker
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload & Document Metadata */}
        <div className="lg:col-span-4 space-y-4">
          <UploadZone onUploadSuccess={handleUploadSuccess} />
          <TopicsList topics={topics} onSelectTopic={(t) => setSelectedPrompt(t)} />
        </div>

        {/* Right Column: Chat & Suggestions */}
        <div className="lg:col-span-8 space-y-4">
          <ChatInterface documentId={documentId} selectedPrompt={selectedPrompt} />
          <Suggestions suggestions={suggestions} onSelectSuggestion={(s) => setSelectedPrompt(s)} />
        </div>
      </div>
    </main>
  );
}

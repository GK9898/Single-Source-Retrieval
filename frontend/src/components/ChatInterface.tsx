'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff, Volume2, Bot, User, Clock, FileCode, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { ChatMessage, SourceChunk } from '../types';
import { queryDocument, evaluateQuery, fetchTTS } from '../lib/api';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useTextToSpeech } from '../hooks/useTextToSpeech';
import { EvaluationPanel } from './EvaluationPanel';

interface ChatInterfaceProps {
  documentId?: string;
  selectedPrompt?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ documentId, selectedPrompt }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! Upload a PDF or document above to begin asking context-aware questions with source chunk citations.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { transcript, isListening, supported: speechSupported, startListening, stopListening } = useSpeechRecognition();
  const { speak, isSpeaking } = useTextToSpeech();

  useEffect(() => {
    if (transcript) setInput(transcript);
  }, [transcript]);

  useEffect(() => {
    if (selectedPrompt) {
      handleSend(selectedPrompt);
    }
  }, [selectedPrompt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const queryText = (textToSend || input).trim();
    if (!queryText || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await queryDocument(queryText, documentId);

      // Perform evaluation metrics audit asynchronously
      let evalMetrics;
      try {
        const evalRes = await evaluateQuery(
          queryText,
          response.answer,
          response.sources.map((s) => s.text)
        );
        evalMetrics = evalRes.metrics;
      } catch (e) {
        // Fallback metric evaluation
      }

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources,
        executionTime: response.execution_time_ms,
        evaluation: evalMetrics,
        queryType: response.query_type,
        subQueries: response.sub_queries
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `Error processing request: ${err.message || 'Server connection error'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="flex flex-col h-[650px] w-full bg-slate-800/80 backdrop-blur-md border border-slate-700/80 rounded-xl shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/80 bg-slate-900/40">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/50 flex items-center justify-center">
            <Bot className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Single Source RAG Assistant</h3>
            <p className="text-xs text-slate-400">FAISS Vector Retrieval • Cross-Encoder Reranking • Query Decomposition</p>
          </div>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-medium text-slate-400">{msg.timestamp}</span>
              <span className="text-xs font-semibold text-slate-300">
                {msg.sender === 'user' ? 'You' : 'Assistant'}
              </span>
            </div>

            <div
              className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-sm ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-none'
                  : 'bg-slate-900/80 text-slate-200 border border-slate-700/60 rounded-tl-none'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {msg.subQueries && msg.subQueries.length > 1 && (
                <div className="mt-2 bg-indigo-950/60 border border-indigo-500/30 p-2 rounded text-[11px] text-indigo-300">
                  <span className="font-semibold block mb-1">🔀 Decomposed Sub-queries ({msg.queryType}):</span>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                    {msg.subQueries.map((sub, idx) => (
                      <li key={idx}>"{sub}"</li>
                    ))}
                  </ul>
                </div>
              )}

              {msg.executionTime && (
                <div className="flex items-center gap-3 text-[10px] text-slate-400 mt-2 border-t border-slate-700/40 pt-2">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-indigo-400" /> {msg.executionTime}ms
                  </span>
                  <button
                    onClick={() => speak(msg.text)}
                    className="flex items-center gap-1 hover:text-indigo-300 transition-colors"
                  >
                    <Volume2 className="w-3 h-3 text-indigo-400" /> Listen
                  </button>
                </div>
              )}

              {msg.sources && msg.sources.length > 0 && (

                <div className="mt-3 border-t border-slate-700/50 pt-2">
                  <button
                    onClick={() => toggleSources(msg.id)}
                    className="flex items-center justify-between w-full text-xs font-medium text-indigo-300 hover:text-indigo-200"
                  >
                    <span className="flex items-center gap-1.5">
                      <FileCode className="w-3.5 h-3.5" /> Cited Sources ({msg.sources.length})
                    </span>
                    {expandedSources[msg.id] ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </button>

                  {expandedSources[msg.id] && (
                    <div className="mt-2 space-y-2">
                      {msg.sources.map((src, i) => (
                        <div
                          key={i}
                          className="bg-slate-950/60 p-2.5 rounded border border-slate-800 text-xs text-slate-300"
                        >
                          <div className="flex justify-between font-mono text-[10px] text-slate-400 mb-1">
                            <span>Chunk ID: {src.chunk_id} (Page {src.page_number || 1})</span>
                            <span className="text-emerald-400 font-semibold">Score: {src.score}</span>
                          </div>
                          <p className="italic text-slate-400 line-clamp-3">"{src.text}"</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {msg.evaluation && <EvaluationPanel metrics={msg.evaluation} />}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-indigo-400 text-xs bg-slate-900/60 p-3 rounded-lg border border-slate-700/40 w-fit animate-pulse">
            <Bot className="w-4 h-4 animate-bounce" />
            <span>Searching vector index & synthesizing response...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-700/80 bg-slate-900/40">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          {speechSupported && (
            <button
              type="button"
              onClick={isListening ? stopListening : startListening}
              className={`p-2.5 rounded-lg border transition-all ${
                isListening
                  ? 'bg-red-500/20 border-red-500/50 text-red-400 animate-pulse'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-indigo-400'
              }`}
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
          )}

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your uploaded document..."
            className="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80"
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2.5 rounded-lg transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

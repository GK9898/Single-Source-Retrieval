'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument } from '../lib/api';
import { UploadResponse } from '../types';

interface UploadZoneProps {
  onUploadSuccess: (response: UploadResponse) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentFile, setCurrentFile] = useState<UploadResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const result = await uploadDocument(file);
      setCurrentFile(result);
      onUploadSuccess(result);
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full bg-slate-800/80 backdrop-blur-md border border-slate-700/80 rounded-xl p-6 shadow-xl transition-all">
      <h2 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
        <FileText className="w-5 h-5 text-indigo-400" /> Document Knowledge Base
      </h2>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`cursor-pointer border-2 border-dashed rounded-lg p-6 text-center transition-all ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]'
            : 'border-slate-600 hover:border-indigo-400/80 hover:bg-slate-700/40'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          accept=".pdf,.txt"
          className="hidden"
        />

        {loading ? (
          <div className="flex flex-col items-center py-4 text-indigo-400">
            <Loader2 className="w-8 h-8 animate-spin mb-2" />
            <p className="text-sm font-medium">Extracting text & building FAISS index...</p>
          </div>
        ) : currentFile ? (
          <div className="flex flex-col items-center py-2 text-emerald-400">
            <CheckCircle className="w-8 h-8 mb-2" />
            <p className="font-semibold text-slate-200">{currentFile.filename}</p>
            <p className="text-xs text-slate-400 mt-1">
              {currentFile.num_pages} pages • {currentFile.num_chunks} vector chunks indexed
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center py-2 text-slate-300">
            <Upload className="w-8 h-8 text-indigo-400 mb-2" />
            <p className="text-sm font-medium">Drag & drop your PDF or TXT document here</p>
            <p className="text-xs text-slate-400 mt-1">or click to browse files</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-red-400 text-xs bg-red-950/40 p-2.5 rounded-lg border border-red-800/40">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

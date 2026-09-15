'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface SuggestionsProps {
  suggestions: string[];
  onSelectSuggestion: (text: string) => void;
}

export const Suggestions: React.FC<SuggestionsProps> = ({ suggestions, onSelectSuggestion }) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="w-full mt-4">
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Suggested Follow-ups
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectSuggestion(item)}
            className="text-xs bg-slate-700/60 hover:bg-indigo-600/30 text-indigo-200 hover:text-indigo-100 border border-indigo-500/20 hover:border-indigo-400/50 rounded-full px-3 py-1.5 transition-all text-left"
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
};

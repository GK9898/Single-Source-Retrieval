'use client';

import React from 'react';
import { Hash, Info } from 'lucide-react';
import { TopicItem } from '../types';

interface TopicsListProps {
  topics: TopicItem[];
  onSelectTopic?: (topicName: string) => void;
}

export const TopicsList: React.FC<TopicsListProps> = ({ topics, onSelectTopic }) => {
  if (!topics || topics.length === 0) return null;

  return (
    <div className="w-full bg-slate-800/80 backdrop-blur-md border border-slate-700/80 rounded-xl p-5 shadow-xl mt-4">
      <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
        <Hash className="w-4 h-4 text-indigo-400" /> Extracted Key Topics
      </h3>
      <div className="space-y-2">
        {topics.map((t, idx) => (
          <div
            key={idx}
            onClick={() => onSelectTopic && onSelectTopic(`Tell me about ${t.topic}`)}
            className="group cursor-pointer bg-slate-900/40 hover:bg-slate-700/50 p-3 rounded-lg border border-slate-700/60 hover:border-indigo-500/40 transition-all"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-indigo-300 group-hover:text-indigo-200">
                #{t.topic}
              </span>
              <span className="text-[10px] bg-indigo-950/80 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-800/40">
                {(t.relevance_score * 100).toFixed(0)}% relevance
              </span>
            </div>
            {t.summary && (
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{t.summary}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

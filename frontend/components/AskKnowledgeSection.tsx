"use client";

import React, { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { QueryResponse } from "@/types";
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  BookOpen,
  ExternalLink,
  ShieldCheck,
  HelpCircle,
  FileText,
  Globe,
} from "lucide-react";

export function AskKnowledgeSection() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sampleQuestions = [
    "What are the main strategic priorities saved in my notes?",
    "Summarize the engineering decisions from recent documents.",
    "What does our onboarding process require?",
  ];

  const handleAsk = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q) return;

    if (queryText) {
      setQuestion(queryText);
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.query(q);
      setResult(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to query knowledge inbox.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="p-2 rounded-xl bg-violet-50 text-violet-600 border border-violet-100">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-zinc-900">Ask Your Knowledge</h2>
          <p className="text-xs text-zinc-500">
            Ask natural-language questions grounded strictly in your saved notes and web pages
          </p>
        </div>
      </div>

      {/* Question Input Box */}
      <div className="space-y-3">
        <div className="relative flex items-center">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your saved notes or ingested URLs..."
            disabled={loading}
            className="w-full pl-4 pr-24 py-3.5 rounded-xl bg-white border border-zinc-300 text-zinc-900 placeholder-zinc-400 text-sm focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition-all shadow-xs disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="absolute right-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" />
                <span>Ask</span>
              </>
            )}
          </button>
        </div>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] text-zinc-500">Suggestions:</span>
          {sampleQuestions.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleAsk(sq)}
              disabled={loading}
              className="text-[11px] text-zinc-600 hover:text-zinc-900 bg-zinc-100 border border-zinc-200 hover:border-zinc-300 px-2.5 py-1 rounded-lg transition-all"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Error Feedback */}
      {error && (
        <div className="mt-5 flex items-start gap-2.5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
          <div>
            <span className="font-semibold block">Query Error</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Answer & Citations Display */}
      {result && (
        <div className="mt-6 space-y-6 pt-6 border-t border-zinc-200">
          {/* Answer Card */}
          <div className="rounded-xl border border-zinc-200 bg-zinc-50/80 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold text-zinc-700">
                <BookOpen className="h-4 w-4 text-indigo-600" />
                <span>Grounded Answer</span>
              </div>

              {result.has_sufficient_context ? (
                <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                  <ShieldCheck className="h-3 w-3" />
                  <span>Evidence Grounded</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                  <HelpCircle className="h-3 w-3" />
                  <span>Insufficient Context</span>
                </span>
              )}
            </div>

            <div className="text-sm text-zinc-800 leading-relaxed whitespace-pre-wrap">
              {result.answer}
            </div>
          </div>

          {/* Citations and Sources */}
          {result.citations.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Supporting Citations & Verifiable Snippets ({result.citations.length})
                </h3>
                <span className="text-[11px] text-zinc-400">
                  Retrieved via pgvector cosine similarity
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.citations.map((cite, index) => (
                  <div
                    key={cite.chunk_id || index}
                    className="p-3.5 rounded-xl border border-zinc-200 bg-white hover:border-zinc-300 shadow-xs transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {cite.source_type === "url" ? (
                          <Globe className="h-3.5 w-3.5 text-cyan-600 shrink-0" />
                        ) : (
                          <FileText className="h-3.5 w-3.5 text-indigo-600 shrink-0" />
                        )}
                        <span className="text-xs font-medium text-zinc-900 truncate" title={cite.title}>
                          {cite.title}
                        </span>
                      </div>

                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-700 border border-zinc-200 shrink-0">
                        {Math.round(cite.similarity_score * 100)}% match
                      </span>
                    </div>

                    <div className="text-xs text-zinc-600 font-mono bg-zinc-50 p-2 rounded-lg leading-relaxed line-clamp-4 border border-zinc-100">
                      "{cite.snippet}"
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-zinc-400 pt-1 border-t border-zinc-100">
                      <span className="truncate max-w-[150px]">Chunk: {cite.chunk_id.slice(0, 8)}...</span>
                      {cite.url && (
                        <a
                          href={cite.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-600 hover:text-indigo-700 flex items-center gap-0.5 shrink-0"
                        >
                          <span>Original URL</span>
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import { KnowledgeItem } from "@/types";
import { api } from "@/lib/api";
import {
  FileText,
  Globe,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Clock,
  Layers,
  Inbox,
  Trash2,
  Loader2,
} from "lucide-react";

interface SavedKnowledgeListProps {
  items: KnowledgeItem[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function SavedKnowledgeList({
  items,
  loading,
  error,
  onRefresh,
}: SavedKnowledgeListProps) {
  const [filter, setFilter] = useState<"all" | "note" | "url">("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const filteredItems = items.filter((item) => {
    if (filter === "all") return true;
    return item.source_type === filter;
  });

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (deletingId) return;
    if (!window.confirm("Are you sure you want to delete this saved knowledge item?")) return;

    setDeletingId(id);
    try {
      await api.deleteItem(id);
      onRefresh();
    } catch (err) {
      alert("Failed to delete item. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (isoStr: string) => {
    try {
      const date = new Date(isoStr);
      return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm flex flex-col h-full">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-base font-semibold text-zinc-900 flex items-center gap-2">
            <span>Saved Knowledge</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700 font-normal">
              {filteredItems.length}
            </span>
          </h2>
          <p className="text-xs text-zinc-500">Indexed notes and URLs ready for query</p>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Pills */}
          <div className="inline-flex rounded-lg bg-zinc-100 p-1 border border-zinc-200 text-xs">
            <button
              onClick={() => setFilter("all")}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filter === "all"
                  ? "bg-white text-zinc-900 shadow-sm font-semibold"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("note")}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filter === "note"
                  ? "bg-white text-zinc-900 shadow-sm font-semibold"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              Notes
            </button>
            <button
              onClick={() => setFilter("url")}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filter === "url"
                  ? "bg-white text-zinc-900 shadow-sm font-semibold"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              URLs
            </button>
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-white border border-zinc-200 text-zinc-600 hover:text-zinc-900 hover:border-zinc-300 transition-all disabled:opacity-50 cursor-pointer shadow-xs"
            title="Refresh knowledge list"
            aria-label="Refresh knowledge list"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-indigo-600" : ""}`} />
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 flex items-center gap-2 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Items Container */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[540px]">
        {loading && items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-zinc-400">
            <RefreshCw className="h-7 w-7 animate-spin text-indigo-600 mb-2" />
            <p className="text-xs">Loading knowledge inbox...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-xl border border-dashed border-zinc-200 bg-zinc-50/50">
            <div className="p-3 rounded-full bg-zinc-100 text-zinc-400 mb-3">
              <Inbox className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-medium text-zinc-800">Your Knowledge Inbox is Empty</h3>
            <p className="text-xs text-zinc-500 max-w-xs mt-1">
              Add your first plain-text note or web link to start asking questions grounded in your saved knowledge.
            </p>
          </div>
        ) : (
          filteredItems.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <div
                key={item.id}
                className="rounded-xl border border-zinc-200 bg-zinc-50/70 hover:border-zinc-300 hover:bg-zinc-50 transition-all p-3.5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5 min-w-0 flex-1">
                    <div
                      className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${
                        item.source_type === "url"
                          ? "bg-cyan-50 text-cyan-600 border border-cyan-200"
                          : "bg-indigo-50 text-indigo-600 border border-indigo-200"
                      }`}
                    >
                      {item.source_type === "url" ? (
                        <Globe className="h-3.5 w-3.5" />
                      ) : (
                        <FileText className="h-3.5 w-3.5" />
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-semibold text-zinc-900 truncate" title={item.title}>
                        {item.title}
                      </h4>

                      <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-zinc-500">
                        <span className="flex items-center gap-1" suppressHydrationWarning>
                          <Clock className="h-3 w-3 text-zinc-400" />
                          {mounted ? formatDate(item.created_at) : ""}
                        </span>

                        <span className="text-zinc-300">•</span>

                        <span className="flex items-center gap-1">
                          <Layers className="h-3 w-3 text-zinc-400" />
                          {item.chunk_count} chunk{item.chunk_count === 1 ? "" : "s"}
                        </span>

                        {item.original_url && (
                          <>
                            <span className="text-zinc-300">•</span>
                            <a
                              href={item.original_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-indigo-600 hover:text-indigo-700 flex items-center gap-0.5 truncate max-w-[140px]"
                              title={item.original_url}
                            >
                              <span>link</span>
                              <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Status Badge & Actions */}
                  <div className="shrink-0 flex items-center gap-1.5">
                    <span
                      className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full border ${
                        item.indexing_status === "indexed"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : item.indexing_status === "pending"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}
                    >
                      {item.indexing_status}
                    </span>

                    <button
                      onClick={() => toggleExpand(item.id)}
                      className="text-zinc-400 hover:text-zinc-600 p-1"
                      title={isExpanded ? "Collapse preview" : "Expand preview"}
                      aria-label="Toggle preview"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronDown className="h-3.5 w-3.5" />
                      )}
                    </button>

                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      disabled={deletingId === item.id}
                      className="text-zinc-400 hover:text-rose-600 p-1 transition-colors"
                      title="Delete item"
                      aria-label="Delete item"
                    >
                      {deletingId === item.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-rose-500" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Error Banner if Failed */}
                {item.indexing_status === "failed" && item.error_message && (
                  <div className="mt-2.5 p-2 rounded-lg bg-rose-50 border border-rose-200 text-[11px] text-rose-800">
                    <span className="font-semibold">Error:</span> {item.error_message}
                  </div>
                )}

                {/* Expanded Content Preview */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-zinc-200 text-xs text-zinc-700 font-mono bg-zinc-100/70 p-2.5 rounded-lg whitespace-pre-wrap leading-relaxed">
                    {item.preview}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

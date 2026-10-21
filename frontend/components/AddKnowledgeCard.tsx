"use client";

import React, { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { SourceType } from "@/types";
import {
  FileText,
  Globe,
  Loader2,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
} from "lucide-react";

interface AddKnowledgeCardProps {
  onItemAdded: () => void;
}

export function AddKnowledgeCard({ onItemAdded }: AddKnowledgeCardProps) {
  const [sourceType, setSourceType] = useState<SourceType>("note");

  // Form states
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [url, setUrl] = useState("");

  // Submission & feedback states
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;

    setSuccessMessage(null);
    setErrorMessage(null);
    setValidationError(null);

    // Client-side validation
    if (sourceType === "note") {
      if (!title.trim()) {
        setValidationError("Please enter a note title.");
        return;
      }
      if (!content.trim()) {
        setValidationError("Note content cannot be empty.");
        return;
      }
    } else {
      const trimmedUrl = url.trim();
      if (!trimmedUrl) {
        setValidationError("Please provide a webpage URL.");
        return;
      }
      if (!trimmedUrl.startsWith("http://") && !trimmedUrl.startsWith("https://")) {
        setValidationError("URL must start with http:// or https://");
        return;
      }
    }

    setSubmitting(true);

    try {
      if (sourceType === "note") {
        const res = await api.ingest({
          source_type: "note",
          title: title.trim(),
          content: content.trim(),
        });
        setSuccessMessage(
          `Note "${res.title}" indexed successfully (${res.chunk_count} chunk${
            res.chunk_count === 1 ? "" : "s"
          }).`
        );
        setTitle("");
        setContent("");
      } else {
        const res = await api.ingest({
          source_type: "url",
          url: url.trim(),
        });
        setSuccessMessage(
          `URL content extracted and indexed: "${res.title}" (${res.chunk_count} chunks).`
        );
        setUrl("");
      }

      onItemAdded();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred during ingestion.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
            <PlusCircle className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-zinc-900">Add Knowledge</h2>
            <p className="text-xs text-zinc-500">
              Save raw notes or extract content from web URLs
            </p>
          </div>
        </div>

        {/* Source Type Selector */}
        <div className="inline-flex rounded-lg bg-zinc-100 p-1 border border-zinc-200">
          <button
            type="button"
            onClick={() => {
              setSourceType("note");
              setValidationError(null);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              sourceType === "note"
                ? "bg-white text-indigo-600 shadow-sm font-semibold"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Text Note</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setSourceType("url");
              setValidationError(null);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              sourceType === "url"
                ? "bg-white text-indigo-600 shadow-sm font-semibold"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <Globe className="h-3.5 w-3.5" />
            <span>Web URL</span>
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {sourceType === "note" ? (
          <>
            <div>
              <label
                htmlFor="note-title"
                className="block text-xs font-medium text-zinc-700 mb-1.5"
              >
                Title <span className="text-rose-500">*</span>
              </label>
              <input
                id="note-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Q3 Strategic Priorities, Architecture Notes..."
                disabled={submitting}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-zinc-300 text-zinc-900 placeholder-zinc-400 text-sm focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition-all disabled:opacity-50"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="note-content"
                  className="block text-xs font-medium text-zinc-700"
                >
                  Content <span className="text-rose-500">*</span>
                </label>
                <span className="text-[11px] text-zinc-400">
                  {content.length} characters
                </span>
              </div>
              <textarea
                id="note-content"
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste or write your notes here. Content will be automatically split into chunks and embedded..."
                disabled={submitting}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-zinc-300 text-zinc-900 placeholder-zinc-400 text-sm focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition-all resize-y disabled:opacity-50"
              />
            </div>
          </>
        ) : (
          <div>
            <label
              htmlFor="url-target"
              className="block text-xs font-medium text-zinc-700 mb-1.5"
            >
              Webpage URL <span className="text-rose-500">*</span>
            </label>
            <input
              id="url-target"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/blog/article"
              disabled={submitting}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-zinc-300 text-zinc-900 placeholder-zinc-400 text-sm focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition-all disabled:opacity-50"
            />
            <p className="mt-1.5 text-[11px] text-zinc-500">
              The backend safely fetches the page, protects against SSRF, extracts readable HTML text, and indexes it.
            </p>
          </div>
        )}

        {/* Validation Error */}
        {validationError && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs">
            <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Server Error */}
        {errorMessage && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
            <div className="flex-1">
              <span className="font-semibold block">Ingestion Failed</span>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Success Feedback */}
        {successMessage && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>
                {sourceType === "note" ? "Chunking & Indexing..." : "Fetching & Indexing URL..."}
              </span>
            </>
          ) : (
            <>
              <PlusCircle className="h-4 w-4" />
              <span>Save & Index Knowledge</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

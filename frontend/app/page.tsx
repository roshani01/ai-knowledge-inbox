"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { AddKnowledgeCard } from "@/components/AddKnowledgeCard";
import { SavedKnowledgeList } from "@/components/SavedKnowledgeList";
import { AskKnowledgeSection } from "@/components/AskKnowledgeSection";
import { api, ApiError } from "@/lib/api";
import { KnowledgeItem } from "@/types";

export default function Home() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(true);
  const [itemsError, setItemsError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchItems = useCallback(async () => {
    setLoadingItems(true);
    setItemsError(null);
    try {
      const response = await api.getItems();
      setItems(response.items);
    } catch (err) {
      if (err instanceof ApiError) {
        setItemsError(err.message);
      } else {
        setItemsError("Failed to fetch saved knowledge items.");
      }
    } finally {
      setLoadingItems(false);
    }
  }, []);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  return (
    <div
      suppressHydrationWarning
      className="min-h-screen flex flex-col bg-white text-zinc-900 selection:bg-indigo-500 selection:text-white"
    >
      {/* Top Navigation */}
      <Navbar itemCount={items.length} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Banner / Subtitle */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-zinc-200">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900">
              AI Knowledge Inbox
            </h2>
            <p className="text-sm text-zinc-600 mt-1">
              Store notes & web pages, index with pgvector embeddings, and retrieve verifiable answers with grounded citations.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-zinc-600 bg-zinc-100 px-3 py-1.5 rounded-lg border border-zinc-200">
            <span className="h-2 w-2 rounded-full bg-indigo-600"></span>
            <span>Vector Indexing: <strong className="text-zinc-900">Active</strong></span>
          </div>
        </div>

        {/* Section C: Ask Your Knowledge (Prominent Top Area) */}
        <section aria-labelledby="ask-section-heading">
          <AskKnowledgeSection />
        </section>

        {/* Grid: Section A (Add Knowledge) & Section B (Saved Knowledge) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Add Knowledge (4 cols on lg) */}
          <section
            aria-labelledby="add-knowledge-heading"
            className="lg:col-span-5 w-full"
          >
            <AddKnowledgeCard onItemAdded={fetchItems} />
          </section>

          {/* Saved Knowledge (7 cols on lg) */}
          <section
            aria-labelledby="saved-knowledge-heading"
            className="lg:col-span-7 w-full"
          >
            <SavedKnowledgeList
              items={items}
              loading={loadingItems}
              error={itemsError}
              onRefresh={fetchItems}
            />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 bg-zinc-50/80 py-6 text-center text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4">
          <span>AI Knowledge Inbox • PostgreSQL & pgvector • OpenAI SDK • FastAPI • Next.js App Router</span>
        </div>
      </footer>
    </div>
  );
}

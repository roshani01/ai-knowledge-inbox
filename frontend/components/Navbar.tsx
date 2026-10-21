"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { HealthResponse } from "@/types";
import { Inbox, Sparkles, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";

interface NavbarProps {
  itemCount: number;
}

export function Navbar({ itemCount }: NavbarProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const res = await api.getHealth();
      setHealth(res);
    } catch {
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="border-b border-zinc-200 bg-white/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-500 p-0.5 shadow-md shadow-indigo-500/10">
            <div className="h-full w-full bg-white rounded-[10px] flex items-center justify-center">
              <Inbox className="h-5 w-5 text-indigo-600" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-zinc-900 tracking-tight">AI Knowledge Inbox</h1>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200">
                MVP
              </span>
            </div>
            <p className="text-xs text-zinc-500">Grounded Vector Knowledge System</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-50 border border-zinc-200 text-xs text-zinc-600">
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>Saved Items:</span>
            <span className="font-semibold text-zinc-900 bg-white border border-zinc-200 px-2 py-0.5 rounded text-[11px]">
              {itemCount}
            </span>
          </div>

          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
              health?.status === "healthy"
                ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                : health?.status === "degraded"
                ? "bg-amber-50 border-amber-200 text-amber-700"
                : "bg-rose-50 border-rose-200 text-rose-700"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full animate-pulse ${
                health?.status === "healthy"
                  ? "bg-emerald-500"
                  : health?.status === "degraded"
                  ? "bg-amber-500"
                  : "bg-rose-500"
              }`}
            />
            <span className="hidden md:inline">
              {health?.status === "healthy"
                ? "Backend Connected"
                : health?.status === "degraded"
                ? "Backend Degraded"
                : "Backend Offline"}
            </span>
            <button
              onClick={checkHealth}
              disabled={loading}
              title="Ping Backend Status"
              aria-label="Ping Backend Status"
              className="hover:opacity-75 focus:outline-none"
            >
              <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

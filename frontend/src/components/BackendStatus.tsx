"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2, RefreshCw, Server } from "lucide-react";

interface HealthData {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  environment: string;
}

export function BackendStatus() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const res = await fetch(`${apiUrl}/health`, {
        cache: "no-store",
      });
      const end = performance.now();
      setLatency(Math.round(end - start));

      if (!res.ok) {
        throw new Error(`HTTP ${res.status} (${res.statusText})`);
      }

      const data: HealthData = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err?.message || "Failed to reach backend");
      setHealth(null);
      setLatency(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Poll health status every 15 seconds
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const isConnected = !!health && !error;

  return (
    <div className="rounded-2xl bg-slate-800/40 border border-slate-800 p-5 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-xl bg-slate-800 text-slate-300 border border-slate-700/60">
            <Server className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-white">FastAPI Backend Status</h3>
              <span className="text-xs text-slate-500 font-mono">({apiUrl})</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {loading ? (
                "Testing connection to /health..."
              ) : isConnected ? (
                <span className="text-emerald-400 font-medium">
                  Connected • Service: {health.service} (v{health.version}) • {latency}ms
                </span>
              ) : (
                <span className="text-rose-400 font-medium">
                  Disconnected: {error} (Ensure backend is running on port 8000)
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 self-end sm:self-center">
          <div
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
              loading
                ? "bg-slate-700/40 text-slate-300 border-slate-600/40"
                : isConnected
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-rose-500/10 text-rose-400 border-rose-500/20"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Checking...</span>
              </>
            ) : isConnected ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Connected</span>
              </>
            ) : (
              <>
                <XCircle className="h-3.5 w-3.5" />
                <span>Offline</span>
              </>
            )}
          </div>

          <button
            onClick={checkHealth}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 hover:border-slate-600 transition-colors disabled:opacity-50"
            title="Check Health"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  Database,
  Cpu,
  Webhook,
  CreditCard,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Server,
  Layers,
  Activity,
  Bot,
} from "lucide-react";
import { SystemReadiness, SystemMetrics } from "@/types/api";
import { fetchSystemReadiness, fetchSystemMetrics } from "@/services/api";

export function SystemStatus() {
  const [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rdy, met] = await Promise.all([
        fetchSystemReadiness(),
        fetchSystemMetrics(),
      ]);
      setReadiness(rdy);
      setMetrics(met);
    } catch (err: any) {
      setError(err.message || "Failed to load system observability metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 20000); // 20s poll
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-5 space-y-4 shadow-xl shadow-slate-950/40">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Server className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <span>System Reliability & Observability Console</span>
              {readiness && (
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                    readiness.status === "ready"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                      : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  }`}
                >
                  {readiness.status === "ready" ? "● SYSTEM READY" : "⚠ SYSTEM DEGRADED"}
                </span>
              )}
            </h3>
            <p className="text-[11px] text-slate-400">
              Live subsystem readiness, deterministic security gate enforcement, and operational counters
            </p>
          </div>
        </div>

        <button
          onClick={loadStatus}
          disabled={loading}
          className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Subsystem Health Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Database */}
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Database className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">SQLite Database</div>
            <div className="text-xs font-bold text-emerald-400 flex items-center space-x-1 mt-0.5">
              <CheckCircle2 className="h-3 w-3" />
              <span>{readiness?.database === "healthy" ? "HEALTHY" : "UNAVAILABLE"}</span>
            </div>
          </div>
        </div>

        {/* Razorpay Test Mode */}
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <CreditCard className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">Razorpay Gateway</div>
            <div className="text-xs font-bold text-indigo-300 flex items-center space-x-1 mt-0.5">
              <ShieldCheck className="h-3 w-3 text-indigo-400" />
              <span>{readiness?.razorpay === "test_mode" ? "TEST MODE" : "UNCONFIGURED"}</span>
            </div>
          </div>
        </div>

        {/* AI Agent Engine */}
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">OpenAI Recovery Agent</div>
            <div className="text-xs font-bold text-purple-300 flex items-center space-x-1 mt-0.5">
              <CheckCircle2 className="h-3 w-3 text-purple-400" />
              <span>{readiness?.openai === "configured" ? "CONFIGURED" : "FALLBACK ACTIVE"}</span>
            </div>
          </div>
        </div>

        {/* Webhook Receiver */}
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Webhook className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">HMAC-SHA256 Webhook</div>
            <div className="text-xs font-bold text-emerald-300 flex items-center space-x-1 mt-0.5">
              <ShieldCheck className="h-3 w-3 text-emerald-400" />
              <span>{readiness?.webhook === "configured" ? "CONFIGURED" : "UNCONFIGURED"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Telemetry Counts */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
          <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Active Recovery Cases</div>
            <div className="text-base font-extrabold text-white mt-0.5">
              {metrics.detected_cases + metrics.in_progress_cases}
              <span className="text-[11px] text-slate-500 font-normal ml-1">/ {metrics.total_recovery_cases} total</span>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Recovered Cases</div>
            <div className="text-base font-extrabold text-emerald-400 mt-0.5">
              {metrics.recovered_cases}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Pending Approvals</div>
            <div className="text-base font-extrabold text-amber-400 mt-0.5">
              {metrics.pending_approvals}
              <span className="text-[11px] text-slate-500 font-normal ml-1">awaiting review</span>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Links Dispatched</div>
            <div className="text-base font-extrabold text-blue-400 mt-0.5">
              {metrics.successful_payment_links}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

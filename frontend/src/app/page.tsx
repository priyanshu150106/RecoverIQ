"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { MetricCard } from "@/components/MetricCard";
import { BackendStatus } from "@/components/BackendStatus";
import { RecoveryQueue } from "@/components/RecoveryQueue";
import { CaseDetailModal } from "@/components/CaseDetailModal";
import { IngestSimulator } from "@/components/IngestSimulator";
import {
  AlertTriangle,
  TrendingUp,
  FileWarning,
  CheckCircle,
  CreditCard,
  Sliders,
  Bot,
  Shield,
  History,
  Coins,
} from "lucide-react";
import { DashboardMetrics, RecoveryCaseItem } from "@/types/api";
import { fetchDashboardMetrics, fetchRecoveryCases, formatINR } from "@/services/api";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [cases, setCases] = useState<RecoveryCaseItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsData, casesData] = await Promise.all([
        fetchDashboardMetrics(),
        fetchRecoveryCases(statusFilter),
      ]);
      setMetrics(metricsData);
      setCases(casesData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadData();
    // Poll data every 20 seconds
    const interval = setInterval(loadData, 20000);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-blue-500 selection:text-white">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Page Title & Badges */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Revenue Recovery Command Center
            </h1>
            <p className="mt-1 text-sm sm:text-base text-slate-400">
              Deterministic revenue recovery engine for Razorpay merchants with live persistence.
            </p>
          </div>

          <div className="flex items-center space-x-2.5">
            <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Stage 2 Live DB
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
              Synthetic Mode
            </span>
          </div>
        </div>

        {/* Backend Live Status Component */}
        <BackendStatus />

        {/* Ingest Simulator / Quick Actions */}
        <IngestSimulator onEventCreated={loadData} />

        {/* Core Live Metric Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Revenue at Risk"
            value={metrics ? formatINR(metrics.revenue_at_risk) : "₹0"}
            subtext={
              metrics
                ? `${metrics.active_cases_count} active unrecovered cases`
                : "Active cases at risk"
            }
            icon={AlertTriangle}
            accentColor="rose"
            trend={
              metrics
                ? {
                    value: `Est. recover: ${formatINR(metrics.potential_recovery)}`,
                    isPositive: false,
                  }
                : undefined
            }
          />

          <MetricCard
            title="Recovery Rate"
            value={metrics ? `${metrics.recovery_rate}%` : "0%"}
            subtext="Calculated on completed recoveries"
            icon={TrendingUp}
            accentColor="emerald"
            trend={
              metrics && metrics.recovery_rate > 0
                ? {
                    value: `${metrics.recovered_cases_count} cases resolved`,
                    isPositive: true,
                  }
                : undefined
            }
          />

          <MetricCard
            title="Cases Detected"
            value={metrics ? metrics.cases_detected.toString() : "0"}
            subtext="Total revenue-at-risk cases identified"
            icon={FileWarning}
            accentColor="amber"
          />

          <MetricCard
            title="Recovered Revenue"
            value={metrics ? formatINR(metrics.recovered_revenue) : "₹0"}
            subtext="Captured revenue from successful recoveries"
            icon={CheckCircle}
            accentColor="blue"
            trend={
              metrics
                ? {
                    value: `Processed: ${formatINR(metrics.total_revenue_processed)}`,
                    isPositive: true,
                  }
                : undefined
            }
          />
        </div>

        {/* Live Recovery Cases Queue */}
        <RecoveryQueue
          cases={cases}
          loading={loading}
          error={error}
          selectedStatus={statusFilter}
          onSelectStatus={setStatusFilter}
          onRefresh={loadData}
          onSelectCase={setSelectedCaseId}
        />

        {/* Pipeline Architecture Indicator */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Safe AI Recovery Workflow</h2>
              <p className="text-xs text-slate-400">
                End-to-end payment failure lifecycle protected by deterministic safety policy gates.
              </p>
            </div>
            <span className="text-xs text-emerald-400 font-mono font-semibold">
              Stage 3A Active (Razorpay Test Mode)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
            <div className="rounded-xl bg-slate-800/80 border border-slate-700/60 p-4 flex flex-col items-start space-y-2">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <CreditCard className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-slate-200">1. Razorpay Event</span>
              <p className="text-[11px] text-slate-400">Failed payments, expiring links, partial invoices.</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-slate-700/60 p-4 flex flex-col items-start space-y-2">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Sliders className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-slate-200">2. Normalization</span>
              <p className="text-[11px] text-slate-400">Standardized internal model & SQLite storage.</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-slate-700/60 p-4 flex flex-col items-start space-y-2">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                <Bot className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-slate-200">3. Baseline / AI Agent</span>
              <p className="text-[11px] text-slate-400">Deterministic scoring (AI reasoning in Stage 4).</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-emerald-500/30 p-4 flex flex-col items-start space-y-2 bg-emerald-950/10">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Shield className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-emerald-300">4. Policy Engine</span>
              <p className="text-[11px] text-slate-400">Hard limits & auto-action validation (Stage 3A).</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-slate-700/60 p-4 flex flex-col items-start space-y-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <History className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-slate-200">5. Execution & Audit</span>
              <p className="text-[11px] text-slate-400">Razorpay Test execution & audit trail (Stage 3A).</p>
            </div>
          </div>
        </div>
      </main>

      {/* Case Diagnostic Detail Modal */}
      <CaseDetailModal
        caseId={selectedCaseId}
        onClose={() => setSelectedCaseId(null)}
        onCaseUpdated={loadData}
      />

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>RecoverIQ • AI Revenue Recovery Agent for Razorpay Merchants • Hackathon Edition (Stage 3A Active)</p>
      </footer>
    </div>
  );
}

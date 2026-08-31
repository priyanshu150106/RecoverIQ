"use client";

import React from "react";
import { Header } from "@/components/Header";
import { MetricCard } from "@/components/MetricCard";
import { BackendStatus } from "@/components/BackendStatus";
import {
  AlertTriangle,
  TrendingUp,
  FileWarning,
  CheckCircle,
  ArrowRight,
  Shield,
  Bot,
  Sliders,
  CreditCard,
  History,
} from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Page Hero Title */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Revenue Recovery Command Center
            </h1>
            <p className="mt-1 text-sm sm:text-base text-slate-400">
              Autonomous AI agent for Razorpay merchants with deterministic policy safeguards.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Mock Data Mode
            </span>
          </div>
        </div>

        {/* Backend Connection Live Status Banner */}
        <BackendStatus />

        {/* Core Metric Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Revenue at Risk"
            value="₹2,45,800"
            subtext="Failed payments & expiring links"
            icon={AlertTriangle}
            accentColor="rose"
            trend={{ value: "+12% this week", isPositive: false }}
          />

          <MetricCard
            title="Recovery Rate"
            value="74.2%"
            subtext="Calculated on completed recoveries"
            icon={TrendingUp}
            accentColor="emerald"
            trend={{ value: "+5.4% vs last week", isPositive: true }}
          />

          <MetricCard
            title="Cases Detected"
            value="128"
            subtext="Total payment risk events tracked"
            icon={FileWarning}
            accentColor="amber"
          />

          <MetricCard
            title="Recovered Revenue"
            value="₹1,82,400"
            subtext="Successfully captured funds"
            icon={CheckCircle}
            accentColor="blue"
            trend={{ value: "₹48.2k today", isPositive: true }}
          />
        </div>

        {/* Architecture & Safety Workflow Visualizer */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Safe AI Recovery Workflow</h2>
              <p className="text-xs text-slate-400">
                End-to-end event lifecycle protected by deterministic safety policy gates.
              </p>
            </div>
            <span className="text-xs text-slate-500 font-mono">Stage 1 Active</span>
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
              <p className="text-[11px] text-slate-400">Payload standardizer & risk magnitude scoring.</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-slate-700/60 p-4 flex flex-col items-start space-y-2">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                <Bot className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-slate-200">3. AI Agent</span>
              <p className="text-[11px] text-slate-400">Root-cause diagnosis & structured recommendation.</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-emerald-500/30 p-4 flex flex-col items-start space-y-2 bg-emerald-950/10">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Shield className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-emerald-300">4. Policy Engine</span>
              <p className="text-[11px] text-slate-400">Hard limit guardrails & merchant approvals.</p>
            </div>

            <div className="rounded-xl bg-slate-800/80 border border-slate-700/60 p-4 flex flex-col items-start space-y-2">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <History className="h-4 w-4" />
              </div>
              <span className="text-xs font-semibold text-slate-200">5. Execution & Audit</span>
              <p className="text-[11px] text-slate-400">Razorpay Test action dispatch + immutable logging.</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>RecoverIQ • AI Revenue Recovery Agent for Razorpay Merchants • Hackathon Edition</p>
      </footer>
    </div>
  );
}

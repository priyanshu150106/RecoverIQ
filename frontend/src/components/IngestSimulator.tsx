"use client";

import React, { useState } from "react";
import {
  Sparkles,
  RefreshCw,
  Zap,
  CheckCircle2,
  AlertCircle,
  Database,
  PlusCircle,
} from "lucide-react";
import { ingestEvent, triggerSeedData } from "@/services/api";

interface IngestSimulatorProps {
  onEventCreated: () => void;
}

export function IngestSimulator({ onEventCreated }: IngestSimulatorProps) {
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const simulate = async (
    name: string,
    email: string,
    type: string,
    amount: number,
    reason: string
  ) => {
    setLoading(true);
    setFeedback(null);
    try {
      const extId = `sim_${Date.now()}`;
      await ingestEvent({
        event_type: type,
        customer: { name, email, phone: "+919800000000" },
        amount,
        currency: "INR",
        failure_reason: reason,
        external_event_id: extId,
      });
      setFeedback(`Ingested synthetic event for ${name}!`);
      onEventCreated();
    } catch (err: any) {
      setFeedback(`Failed: ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const handleResetSeed = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      await triggerSeedData();
      setFeedback("Database reset and re-seeded with synthetic dataset!");
      onEventCreated();
    } catch (err: any) {
      setFeedback(`Seed failed: ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  return (
    <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-5 backdrop-blur-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white">Event Simulation & Seed Sandbox</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Inject synthetic Razorpay test events to watch RecoverIQ normalize, score, and queue cases.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() =>
              simulate(
                "Karan Kapoor",
                "karan.k@example.com",
                "payment.failed",
                450000,
                "bank_authorization_timeout"
              )
            }
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors flex items-center space-x-1.5 disabled:opacity-50"
          >
            <Zap className="h-3.5 w-3.5 text-blue-400" />
            <span>Simulate Bank Timeout (₹4.5k)</span>
          </button>

          <button
            onClick={() =>
              simulate(
                "Simran Kaur",
                "simran.k@example.com",
                "payment_link.expired",
                899900,
                "payment_link_ttl_expired"
              )
            }
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors flex items-center space-x-1.5 disabled:opacity-50"
          >
            <PlusCircle className="h-3.5 w-3.5 text-indigo-400" />
            <span>Simulate Expired Link (₹9k)</span>
          </button>

          <button
            onClick={handleResetSeed}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-semibold transition-colors flex items-center space-x-1.5 disabled:opacity-50"
          >
            <Database className="h-3.5 w-3.5 text-blue-400" />
            <span>Reset / Seed Synthetic DB</span>
          </button>
        </div>
      </div>

      {feedback && (
        <div className="mt-3 text-xs text-emerald-400 font-medium flex items-center space-x-1.5 animate-in fade-in">
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>{feedback}</span>
        </div>
      )}
    </div>
  );
}

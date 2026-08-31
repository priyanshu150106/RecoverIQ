"use client";

import React, { useState } from "react";
import {
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import { RecoveryCaseItem } from "@/types/api";
import { formatINR } from "@/services/api";

interface RecoveryQueueProps {
  cases: RecoveryCaseItem[];
  loading: boolean;
  error: string | null;
  selectedStatus: string;
  onSelectStatus: (status: string) => void;
  onRefresh: () => void;
  onSelectCase: (caseId: number) => void;
}

export function RecoveryQueue({
  cases,
  loading,
  error,
  selectedStatus,
  onSelectStatus,
  onRefresh,
  onSelectCase,
}: RecoveryQueueProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCases = cases.filter((c) => {
    const query = searchQuery.toLowerCase();
    return (
      c.customer_name.toLowerCase().includes(query) ||
      c.customer_email.toLowerCase().includes(query) ||
      c.event_type.toLowerCase().includes(query) ||
      c.recommended_action.toLowerCase().includes(query) ||
      c.id.toString().includes(query)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RECOVERED":
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            <span>Recovered</span>
          </span>
        );
      case "IN_PROGRESS":
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Clock className="h-3 w-3" />
            <span>In Progress</span>
          </span>
        );
      case "DETECTED":
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="h-3 w-3" />
            <span>Detected</span>
          </span>
        );
    }
  };

  const getRiskPill = (score: number) => {
    if (score >= 65) {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          {score} • High
        </span>
      );
    }
    if (score >= 35) {
      return (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          {score} • Med
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        {score} • Low
      </span>
    );
  };

  return (
    <div className="rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur-sm overflow-hidden flex flex-col">
      {/* Header & Controls */}
      <div className="p-5 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-white">Live Recovery Queue</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
              {filteredCases.length} cases
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time at-risk payment cases ingested and scored by the baseline engine.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status Tabs */}
          <div className="flex rounded-xl bg-slate-800/80 p-1 border border-slate-700/60 text-xs">
            <button
              onClick={() => onSelectStatus("")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                selectedStatus === ""
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              All
            </button>
            <button
              onClick={() => onSelectStatus("DETECTED")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                selectedStatus === "DETECTED"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Detected
            </button>
            <button
              onClick={() => onSelectStatus("IN_PROGRESS")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                selectedStatus === "IN_PROGRESS"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              In Progress
            </button>
            <button
              onClick={() => onSelectStatus("RECOVERED")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                selectedStatus === "RECOVERED"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Recovered
            </button>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search customer, event..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-48 sm:w-56"
            />
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors disabled:opacity-50"
            title="Refresh Cases"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/40 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Customer</th>
              <th className="py-3 px-4 font-semibold">Amount</th>
              <th className="py-3 px-4 font-semibold">Event Type</th>
              <th className="py-3 px-4 font-semibold">Risk Score</th>
              <th className="py-3 px-4 font-semibold">Recovery Prob</th>
              <th className="py-3 px-4 font-semibold">Recommended Action</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 text-right font-semibold">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading && cases.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                    <span>Loading recovery cases from SQLite...</span>
                  </div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-rose-400">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <ShieldAlert className="h-6 w-6" />
                    <span>Failed to load cases: {error}</span>
                    <button
                      onClick={onRefresh}
                      className="px-3 py-1 rounded-lg bg-slate-800 text-xs text-white border border-slate-700 hover:bg-slate-700"
                    >
                      Retry
                    </button>
                  </div>
                </td>
              </tr>
            ) : filteredCases.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400">
                  <p className="text-sm">No recovery cases match your criteria.</p>
                  <p className="text-xs text-slate-500 mt-1">Try resetting filters or seeding synthetic data.</p>
                </td>
              </tr>
            ) : (
              filteredCases.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => onSelectCase(c.id)}
                  className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                >
                  {/* Customer */}
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                      {c.customer_name}
                    </div>
                    <div className="text-slate-400 font-mono text-[11px] truncate max-w-[160px]">
                      {c.customer_email}
                    </div>
                  </td>

                  {/* Amount */}
                  <td className="py-3.5 px-4 font-bold text-slate-100">
                    {formatINR(c.amount)}
                  </td>

                  {/* Event Type */}
                  <td className="py-3.5 px-4">
                    <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {c.event_type}
                    </span>
                  </td>

                  {/* Risk Score */}
                  <td className="py-3.5 px-4">
                    {getRiskPill(c.risk_score)}
                  </td>

                  {/* Recovery Probability */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${Math.min(c.recovery_probability * 100, 100)}%` }}
                        />
                      </div>
                      <span className="font-semibold text-emerald-400">
                        {(c.recovery_probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>

                  {/* Recommended Action */}
                  <td className="py-3.5 px-4">
                    <span className="font-mono text-[11px] text-blue-300 bg-blue-950/40 px-2 py-1 rounded border border-blue-800/40">
                      {c.recommended_action}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="py-3.5 px-4">
                    {getStatusBadge(c.status)}
                  </td>

                  {/* Action */}
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(c.id);
                      }}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
                    >
                      <span>View</span>
                      <ExternalLink className="h-3 w-3" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

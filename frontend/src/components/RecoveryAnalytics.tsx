"use client";

import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  BarChart3,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  RefreshCw,
  Compass,
  ArrowUpRight,
  ShieldAlert,
  Percent,
  Activity,
  Layers,
} from "lucide-react";
import {
  AnalyticsOverview,
  StrategyAnalytics,
  RecoveryTrendPoint,
  AIPerformanceMetrics,
} from "@/types/api";
import {
  fetchAnalyticsOverview,
  fetchStrategyAnalytics,
  fetchRecoveryTrend,
  fetchAIPerformance,
  formatINR,
} from "@/services/api";

export function RecoveryAnalytics() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [strategies, setStrategies] = useState<StrategyAnalytics[]>([]);
  const [trend, setTrend] = useState<RecoveryTrendPoint[]>([]);
  const [aiPerf, setAiPerf] = useState<AIPerformanceMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, strat, tr, ai] = await Promise.all([
        fetchAnalyticsOverview(),
        fetchStrategyAnalytics(),
        fetchRecoveryTrend(7),
        fetchAIPerformance(),
      ]);
      setOverview(ov);
      setStrategies(strat);
      setTrend(tr);
      setAiPerf(ai);
    } catch (err: any) {
      setError(err.message || "Failed to load recovery analytics data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-6 shadow-2xl shadow-slate-950">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 text-blue-400 border border-blue-500/30">
            <BarChart3 className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-white">Recovery Intelligence & Analytics</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border bg-blue-500/10 text-blue-300 border-blue-500/20">
                Stage 7 Outcome Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Verified financial outcomes, strategy efficiency matrix, and AI predictive calibration
            </p>
          </div>
        </div>

        <button
          onClick={loadAnalytics}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center space-x-2 transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Intelligence</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 6-KPI Header Grid */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Revenue at Risk */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Revenue at Risk</div>
            <div className="text-lg font-bold text-rose-400 truncate">
              {formatINR(overview.revenue_at_risk)}
            </div>
            <div className="text-[10px] text-slate-500">Active failed volume</div>
          </div>

          {/* Revenue Recovered */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Revenue Recovered</div>
            <div className="text-lg font-bold text-emerald-400 truncate">
              {formatINR(overview.revenue_recovered)}
            </div>
            <div className="text-[10px] text-emerald-500/80 font-medium flex items-center">
              <ArrowUpRight className="h-3 w-3 mr-0.5" />
              <span>Verified in Test Mode</span>
            </div>
          </div>

          {/* Recovery Success Rate */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Recovery Rate</div>
            <div className="text-lg font-bold text-indigo-300">
              {overview.recovery_rate}%
            </div>
            <div className="text-[10px] text-slate-500">Portfolio conversion</div>
          </div>

          {/* Avg Recovery Time */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Avg Recovery Time</div>
            <div className="text-lg font-bold text-amber-300">
              {overview.average_time_to_recovery_seconds > 60
                ? `${(overview.average_time_to_recovery_seconds / 60).toFixed(1)}m`
                : `${overview.average_time_to_recovery_seconds.toFixed(0)}s`}
            </div>
            <div className="text-[10px] text-slate-500">Execution to payment</div>
          </div>

          {/* Successful Recoveries */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Recovered Cases</div>
            <div className="text-lg font-bold text-emerald-400">
              {overview.successful_recoveries}
            </div>
            <div className="text-[10px] text-slate-500">Fully settled</div>
          </div>

          {/* Pending Recoveries */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="text-[11px] text-slate-400 font-medium">Active In-Progress</div>
            <div className="text-lg font-bold text-blue-400">
              {overview.pending_recoveries}
            </div>
            <div className="text-[10px] text-slate-500">Links dispatched</div>
          </div>
        </div>
      )}

      {/* Grid: 7-Day Trend Chart & Outcome Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Trend Bar Chart */}
        <div className="lg:col-span-2 rounded-xl bg-slate-950/60 border border-slate-800 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <span>7-Day Recovery Volume & Rate Trend</span>
            </span>
            <div className="flex items-center space-x-3 text-[11px]">
              <span className="flex items-center space-x-1 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/60 inline-block" />
                <span>At Risk</span>
              </span>
              <span className="flex items-center space-x-1 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" />
                <span>Recovered</span>
              </span>
            </div>
          </div>

          {/* Clean SVG/HTML Chart Bars */}
          <div className="pt-2 grid grid-cols-7 gap-2 h-44 items-end">
            {trend.map((point, idx) => {
              const maxVal = Math.max(...trend.map((p) => Math.max(p.amount_at_risk, p.amount_recovered)), 1);
              const riskHeight = Math.max(8, (point.amount_at_risk / maxVal) * 100);
              const recHeight = Math.max(6, (point.amount_recovered / maxVal) * 100);

              const dateFormatted = new Date(point.date).toLocaleDateString("en-IN", {
                weekday: "short",
                day: "numeric",
              });

              return (
                <div key={idx} className="flex flex-col items-center h-full justify-end group">
                  <div className="text-[9px] font-mono text-emerald-400 mb-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {point.recovery_rate}%
                  </div>
                  <div className="w-full flex items-end justify-center space-x-1 h-32 px-1">
                    {/* Risk Bar */}
                    <div
                      style={{ height: `${riskHeight}%` }}
                      className="w-1/2 rounded-t bg-rose-500/30 border-t border-rose-500/50 hover:bg-rose-500/50 transition-colors"
                      title={`At Risk: ${formatINR(point.amount_at_risk)}`}
                    />
                    {/* Recovered Bar */}
                    <div
                      style={{ height: `${recHeight}%` }}
                      className="w-1/2 rounded-t bg-emerald-500 hover:bg-emerald-400 transition-colors shadow-lg shadow-emerald-500/20"
                      title={`Recovered: ${formatINR(point.amount_recovered)}`}
                    />
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 mt-1 truncate">
                    {dateFormatted}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Outcome Status Distribution & AI Performance Card */}
        <div className="rounded-xl bg-slate-950/60 border border-slate-800 p-4 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
              <Layers className="h-4 w-4 text-blue-400" />
              <span>Outcome Distribution</span>
            </span>

            {overview && (
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-300 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span>Recovered</span>
                  </span>
                  <span className="font-bold text-emerald-400">{overview.successful_recoveries}</span>
                </div>

                <div className="flex justify-between items-center p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-300 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    <span>Partially Recovered</span>
                  </span>
                  <span className="font-bold text-amber-400">{overview.partial_recoveries}</span>
                </div>

                <div className="flex justify-between items-center p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-300 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    <span>Pending Action</span>
                  </span>
                  <span className="font-bold text-blue-400">{overview.pending_recoveries}</span>
                </div>

                <div className="flex justify-between items-center p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-300 flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    <span>Failed / Expired</span>
                  </span>
                  <span className="font-bold text-rose-400">
                    {overview.failed_recoveries + overview.expired_recoveries}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* AI vs Outcome Calibration */}
          {aiPerf && (
            <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-purple-300 flex items-center space-x-1">
                  <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                  <span>AI vs Outcome Accuracy</span>
                </span>
                <span className="text-[10px] font-mono text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded">
                  {aiPerf.analyzed_cases} Evaluated
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div>
                  <span className="text-slate-400">Predicted Prob:</span>
                  <div className="font-bold text-white">{(aiPerf.average_predicted_probability * 100).toFixed(0)}%</div>
                </div>
                <div>
                  <span className="text-slate-400">Actual Rec Rate:</span>
                  <div className="font-bold text-emerald-400">{aiPerf.average_actual_recovery_percentage}%</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Strategy Performance Matrix Table */}
      <div className="rounded-xl bg-slate-950/60 border border-slate-800 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
            <Compass className="h-4 w-4 text-indigo-400" />
            <span>Deterministic Recovery Strategy Efficiency Matrix</span>
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            {strategies.length} Active Strategies
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                <th className="py-2.5 px-3">Strategy</th>
                <th className="py-2.5 px-3">Cases Routed</th>
                <th className="py-2.5 px-3">Executions</th>
                <th className="py-2.5 px-3">Recovered</th>
                <th className="py-2.5 px-3">Success Rate</th>
                <th className="py-2.5 px-3 text-right">Volume Recovered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {strategies.map((strat, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 px-3 font-mono font-semibold text-white">
                    {strat.strategy}
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">{strat.cases}</td>
                  <td className="py-2.5 px-3">{strat.executions}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-semibold">{strat.recovered_cases}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                        strat.recovery_rate >= 50
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : strat.recovery_rate > 0
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {strat.recovery_rate}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono font-bold text-white text-right">
                    {formatINR(strat.amount_recovered)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

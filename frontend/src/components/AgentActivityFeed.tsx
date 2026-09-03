"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Clock,
  Ban,
  Hourglass,
  Sparkles,
  AlertOctagon,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Radio,
} from "lucide-react";
import { ActivityItem, ActionType, ActorType } from "@/types/api";
import { fetchActivityFeed, formatINR } from "@/services/api";

interface AgentActivityFeedProps {
  onSelectCase?: (caseId: number) => void;
  limit?: number;
}

export function AgentActivityFeed({ onSelectCase, limit = 15 }: AgentActivityFeedProps) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadFeed = useCallback(async (isManual: boolean = false) => {
    if (isManual) setRefreshing(true);
    setError(null);
    try {
      const data = await fetchActivityFeed(limit);
      setActivities(data);
    } catch (err: any) {
      setError(err.message || "Unable to load recovery activity");
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  }, [limit]);

  useEffect(() => {
    loadFeed();
    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      loadFeed();
    }, 10000);
    return () => clearInterval(interval);
  }, [loadFeed]);

  const getActionConfig = (action: ActionType) => {
    switch (action) {
      case "FAILURE_DETECTED":
        return {
          icon: AlertTriangle,
          color: "text-rose-400",
          bg: "bg-rose-500/10",
          border: "border-rose-500/20",
          label: "Failure Detected",
        };
      case "AI_DIAGNOSED":
        return {
          icon: Bot,
          color: "text-purple-400",
          bg: "bg-purple-500/10",
          border: "border-purple-500/20",
          label: "AI Diagnosis",
        };
      case "POLICY_PASSED":
        return {
          icon: ShieldCheck,
          color: "text-emerald-400",
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/20",
          label: "Policy Verified",
        };
      case "LINK_GENERATED":
        return {
          icon: Zap,
          color: "text-blue-400",
          bg: "bg-blue-500/10",
          border: "border-blue-500/20",
          label: "Payment Link Created",
        };
      case "PAYMENT_CAPTURED":
        return {
          icon: CheckCircle2,
          color: "text-emerald-400",
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/20",
          label: "Payment Captured",
        };
      case "PAYMENT_PARTIALLY_CAPTURED":
        return {
          icon: Clock,
          color: "text-amber-400",
          bg: "bg-amber-500/10",
          border: "border-amber-500/20",
          label: "Partial Payment",
        };
      case "PAYMENT_CANCELLED":
        return {
          icon: Ban,
          color: "text-slate-400",
          bg: "bg-slate-700/20",
          border: "border-slate-700/40",
          label: "Payment Cancelled",
        };
      case "PAYMENT_EXPIRED":
        return {
          icon: Hourglass,
          color: "text-slate-400",
          bg: "bg-slate-700/20",
          border: "border-slate-700/40",
          label: "Payment Expired",
        };
      case "CASE_RECOVERED":
        return {
          icon: Sparkles,
          color: "text-emerald-300",
          bg: "bg-emerald-500/20",
          border: "border-emerald-500/40",
          label: "Case Recovered",
        };
      case "RECOVERY_ACTION_FAILED":
        return {
          icon: AlertOctagon,
          color: "text-rose-400",
          bg: "bg-rose-500/10",
          border: "border-rose-500/20",
          label: "Action Failed",
        };
      default:
        return {
          icon: Activity,
          color: "text-blue-400",
          bg: "bg-blue-500/10",
          border: "border-blue-500/20",
          label: action,
        };
    }
  };

  const getActorBadge = (actor: ActorType) => {
    switch (actor) {
      case "AI_AGENT":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      case "POLICY_ENGINE":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "RAZORPAY_EXECUTION":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "WEBHOOK_RECEIVER":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      default:
        return "bg-slate-700/40 text-slate-300 border-slate-700";
    }
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm overflow-hidden shadow-xl">
      {/* Feed Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Radio className="h-5 w-5 animate-pulse text-purple-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white tracking-tight">
                Recovery Agent Activity
              </h2>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>
            <p className="text-xs text-slate-400">Live actions across the recovery pipeline</p>
          </div>
        </div>

        <button
          onClick={() => loadFeed(true)}
          disabled={refreshing || loading}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors disabled:opacity-50"
          title="Refresh activity stream"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin text-purple-400" : ""}`} />
        </button>
      </div>

      {/* Feed Body */}
      <div className="p-4 divide-y divide-slate-800/60 max-h-[380px] overflow-y-auto">
        {loading ? (
          <div className="space-y-3 py-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center space-x-3 p-3 rounded-xl bg-slate-950/40 animate-pulse">
                <div className="h-8 w-8 rounded-lg bg-slate-800 shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 w-1/4 bg-slate-800 rounded" />
                  <div className="h-2.5 w-3/4 bg-slate-800/60 rounded" />
                </div>
                <div className="h-3 w-12 bg-slate-800 rounded" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-6 text-center space-y-2">
            <div className="inline-flex p-2.5 rounded-full bg-rose-500/10 text-rose-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <p className="text-sm font-semibold text-rose-400">Unable to load recovery activity</p>
            <p className="text-xs text-slate-500">{error}</p>
          </div>
        ) : activities.length === 0 ? (
          <div className="p-8 text-center space-y-2">
            <div className="inline-flex p-3 rounded-full bg-slate-800 text-slate-400">
              <Activity className="h-6 w-6" />
            </div>
            <p className="text-sm font-semibold text-slate-300">No recovery activity yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Simulate payment failure events using the quick actions above or execute payment links to see real-time pipeline events.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {activities.map((act) => {
              const cfg = getActionConfig(act.action);
              const IconComp = cfg.icon;

              return (
                <div
                  key={act.id}
                  className={`group flex items-start justify-between gap-3 p-3 rounded-xl transition-all duration-150 border ${cfg.bg} ${cfg.border} hover:border-slate-700/80 hover:bg-slate-800/40`}
                >
                  {/* Left Icon & Text */}
                  <div className="flex items-start space-x-3 min-w-0">
                    <div className={`p-2 rounded-lg shrink-0 ${cfg.bg} ${cfg.color} border ${cfg.border}`}>
                      <IconComp className="h-4 w-4" />
                    </div>

                    <div className="min-w-0 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold text-white">{cfg.label}</span>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${getActorBadge(act.actor)}`}>
                          {act.actor}
                        </span>
                        {act.case_id && onSelectCase && (
                          <button
                            onClick={() => onSelectCase(act.case_id!)}
                            className="text-[10px] font-mono font-semibold text-blue-400 hover:text-blue-300 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20 flex items-center space-x-0.5 transition-colors"
                          >
                            <span>Case #{act.case_id}</span>
                            <ChevronRight className="h-3 w-3" />
                          </button>
                        )}
                      </div>

                      <p className="text-xs text-slate-300 leading-snug break-words">
                        {act.summary}
                      </p>
                    </div>
                  </div>

                  {/* Right: Amount & Timestamp */}
                  <div className="text-right shrink-0 space-y-1">
                    {act.amount !== undefined && act.amount !== null && (
                      <div className="text-xs font-bold text-white font-mono">
                        {formatINR(act.amount)}
                      </div>
                    )}
                    <div className="text-[11px] text-slate-500 font-mono">
                      {formatTime(act.timestamp)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

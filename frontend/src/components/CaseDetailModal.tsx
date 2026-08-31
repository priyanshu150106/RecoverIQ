"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  User,
  CreditCard,
  Gauge,
  Sparkles,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  Info,
  Loader2,
  ExternalLink,
  Copy,
  Check,
  Zap,
} from "lucide-react";
import { RecoveryCaseDetail } from "@/types/api";
import {
  fetchRecoveryCaseDetail,
  executePaymentLink,
  formatINR,
} from "@/services/api";

interface CaseDetailModalProps {
  caseId: number | null;
  onClose: () => void;
  onCaseUpdated?: () => void;
}

export function CaseDetailModal({
  caseId,
  onClose,
  onCaseUpdated,
}: CaseDetailModalProps) {
  const [detail, setDetail] = useState<RecoveryCaseDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);
  const [execError, setExecError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const loadCase = (id: number) => {
    setLoading(true);
    setError(null);
    setExecError(null);

    fetchRecoveryCaseDetail(id)
      .then((data) => {
        setDetail(data);
      })
      .catch((err) => {
        setError(err.message || "Failed to load case details.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    if (!caseId) return;
    loadCase(caseId);
  }, [caseId]);

  const handleGenerateLink = async () => {
    if (!caseId) return;
    setExecuting(true);
    setExecError(null);

    try {
      await executePaymentLink(caseId);
      loadCase(caseId);
      if (onCaseUpdated) {
        onCaseUpdated();
      }
    } catch (err: any) {
      setExecError(err.message || "Failed to generate Razorpay payment link.");
    } finally {
      setExecuting(false);
    }
  };

  const handleCopyLink = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (!caseId) return null;

  // Check if a payment link has already been executed for this case
  const activeLinkAction = detail?.recovery_actions?.find(
    (a) => a.action_type === "CREATE_PAYMENT_LINK" && a.status === "EXECUTED" && a.payment_link_url
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-3xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl shadow-slate-950 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white">Recovery Case #{caseId}</h3>
                {detail && (
                  <span
                    className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                      detail.status === "RECOVERED"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : detail.status === "IN_PROGRESS"
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    }`}
                  >
                    {detail.status}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">Diagnostic Breakdown & Recovery Actions</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              <p className="text-sm">Loading diagnostic case data...</p>
            </div>
          ) : error || !detail ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
              <p className="font-semibold">Unable to load case details</p>
              <p className="text-xs mt-1">{error}</p>
            </div>
          ) : (
            <>
              {/* Active Razorpay Payment Link Card (if generated) */}
              {activeLinkAction?.payment_link_url && (
                <div className="rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Zap className="h-4 w-4 text-emerald-400" />
                      <h4 className="text-sm font-bold text-white">
                        Razorpay Test Payment Link Active
                      </h4>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      {activeLinkAction.payment_link_id}
                    </span>
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span className="font-mono text-xs text-slate-300 truncate max-w-[340px]">
                      {activeLinkAction.payment_link_url}
                    </span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleCopyLink(activeLinkAction.payment_link_url!)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs flex items-center space-x-1"
                        title="Copy Link"
                      >
                        {copied ? (
                          <>
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                            <span className="text-emerald-400 text-[11px]">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3.5 w-3.5" />
                            <span className="text-[11px]">Copy</span>
                          </>
                        )}
                      </button>

                      <a
                        href={activeLinkAction.payment_link_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1.5 transition-colors shadow-lg shadow-emerald-600/20"
                      >
                        <span>Open Test Checkout</span>
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {/* Execution Error Banner */}
              {execError && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">Action Blocked / Failed</p>
                    <p className="mt-0.5 text-slate-300">{execError}</p>
                  </div>
                </div>
              )}

              {/* Grid: Customer Profile & Payment Event */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Customer Profile */}
                <div className="rounded-xl bg-slate-800/60 border border-slate-700/60 p-4 space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    <User className="h-4 w-4 text-blue-400" />
                    <span>Customer Profile</span>
                  </div>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Name:</span>
                      <span className="font-semibold text-white">{detail.customer.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Email:</span>
                      <span className="font-mono text-xs text-slate-200">{detail.customer.email}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Phone:</span>
                      <span className="font-mono text-xs text-slate-200">{detail.customer.phone || "N/A"}</span>
                    </div>
                    <div className="pt-2 border-t border-slate-700/60 grid grid-cols-3 gap-2 text-center">
                      <div className="rounded-lg bg-slate-900/60 p-2">
                        <div className="text-xs text-slate-400">Successes</div>
                        <div className="text-sm font-bold text-emerald-400">{detail.customer.successful_transactions}</div>
                      </div>
                      <div className="rounded-lg bg-slate-900/60 p-2">
                        <div className="text-xs text-slate-400">Failures</div>
                        <div className="text-sm font-bold text-rose-400">{detail.customer.failed_transactions}</div>
                      </div>
                      <div className="rounded-lg bg-slate-900/60 p-2">
                        <div className="text-xs text-slate-400">Total Spent</div>
                        <div className="text-xs font-bold text-white mt-0.5">{formatINR(detail.customer.total_paid)}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Payment Event */}
                <div className="rounded-xl bg-slate-800/60 border border-slate-700/60 p-4 space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    <CreditCard className="h-4 w-4 text-indigo-400" />
                    <span>Payment Event</span>
                  </div>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Event Type:</span>
                      <span className="font-mono text-xs text-indigo-300 font-semibold">{detail.payment_event.event_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Amount at Risk:</span>
                      <span className="text-base font-extrabold text-white">{formatINR(detail.payment_event.amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">External ID:</span>
                      <span className="font-mono text-xs text-slate-300">{detail.payment_event.external_event_id || "None"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Failure Reason:</span>
                      <span className="text-xs text-amber-300 font-medium text-right max-w-[180px] truncate">
                        {detail.payment_event.failure_reason || "Unspecified"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Event Time:</span>
                      <span className="text-xs text-slate-400">
                        {new Date(detail.payment_event.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Scoring & Recovery Metrics */}
              <div className="rounded-xl bg-slate-800/60 border border-slate-700/60 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    <Gauge className="h-4 w-4 text-emerald-400" />
                    <span>Scoring & Diagnostic Assessment</span>
                  </div>
                  <span className="text-xs text-slate-400">Confidence: {(detail.confidence * 100).toFixed(0)}%</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Risk Score */}
                  <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-400">Risk Magnitude:</span>
                      <span className={`font-bold ${detail.risk_score > 60 ? "text-rose-400" : detail.risk_score > 35 ? "text-amber-400" : "text-emerald-400"}`}>
                        {detail.risk_score} / 100
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${detail.risk_score > 60 ? "bg-rose-500" : detail.risk_score > 35 ? "bg-amber-500" : "bg-emerald-500"}`}
                        style={{ width: `${Math.min(detail.risk_score, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Recovery Probability */}
                  <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-400">Recovery Probability:</span>
                      <span className="font-bold text-emerald-400">
                        {(detail.recovery_probability * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${Math.min(detail.recovery_probability * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Scoring Breakdown Details */}
                {detail.scoring_breakdown && (
                  <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/80 text-xs space-y-1 text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Reason Category:</span>
                      <span className="font-medium text-white">{detail.scoring_breakdown.category}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Customer Factor:</span>
                      <span className="font-medium text-slate-200">{detail.scoring_breakdown.customer_history}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Amount Context:</span>
                      <span className="font-medium text-slate-200">{detail.scoring_breakdown.amount_context}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Recommended Action & Stage 3A Execution Trigger */}
              <div className="rounded-xl bg-gradient-to-r from-blue-950/40 via-indigo-950/40 to-slate-900 border border-blue-800/40 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                    Recommended Recovery Action
                  </span>
                  <p className="text-base font-bold text-white mt-0.5 font-mono">
                    {detail.recommended_action}
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  {detail.status !== "RECOVERED" && (
                    <button
                      onClick={handleGenerateLink}
                      disabled={executing}
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors flex items-center space-x-2 shadow-lg shadow-blue-600/20 disabled:opacity-50"
                    >
                      {executing ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Calling Razorpay Test API...</span>
                        </>
                      ) : (
                        <>
                          <Zap className="h-4 w-4 text-amber-300" />
                          <span>Generate Razorpay Test Link</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end px-6 py-4 border-t border-slate-800 bg-slate-900/90 space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

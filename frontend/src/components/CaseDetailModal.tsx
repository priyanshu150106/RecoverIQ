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
  Bot,
  ShieldAlert,
  HelpCircle,
  TrendingUp,
} from "lucide-react";
import { RecoveryCaseDetail, AIRecoveryRecommendationResponse } from "@/types/api";
import {
  fetchRecoveryCaseDetail,
  executePaymentLink,
  fetchAIRecommendation,
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

  // Stage 4 AI Agent state
  const [aiRec, setAiRec] = useState<AIRecoveryRecommendationResponse | null>(null);
  const [analyzingAI, setAnalyzingAI] = useState<boolean>(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const loadCase = (id: number) => {
    setLoading(true);
    setError(null);
    setExecError(null);
    setAiRec(null);
    setAiError(null);

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

  const handleRunAIAnalysis = async () => {
    if (!caseId) return;
    setAnalyzingAI(true);
    setAiError(null);

    try {
      const rec = await fetchAIRecommendation(caseId);
      setAiRec(rec);
    } catch (err: any) {
      setAiError(err.message || "AI Agent recommendation failed.");
    } finally {
      setAnalyzingAI(false);
    }
  };

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
                        : detail.status === "CANCELLED"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    }`}
                  >
                    {detail.status}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">Diagnostic Breakdown & Autonomous Recovery Engine</p>
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

              {/* STAGE 4: AI Recovery Agent Analysis Console */}
              <div className="rounded-2xl bg-gradient-to-br from-indigo-950/40 via-purple-950/20 to-slate-900 border border-purple-500/30 p-5 space-y-4 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-purple-500/20 pb-3">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      <Bot className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                        <span>AI Recovery Agent Analysis</span>
                        {aiRec && (
                          <span
                            className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                              aiRec.source === "ai"
                                ? "bg-purple-500/10 text-purple-300 border-purple-500/30"
                                : "bg-slate-700/60 text-slate-300 border-slate-600"
                            }`}
                          >
                            {aiRec.source === "ai"
                              ? `Model: ${aiRec.model_used || "OpenAI"}`
                              : "Deterministic Fallback Engine"}
                          </span>
                        )}
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        High-precision failure diagnostics and automated policy recommendations
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleRunAIAnalysis}
                    disabled={analyzingAI}
                    className="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition-all flex items-center space-x-2 shadow-lg shadow-purple-600/20 disabled:opacity-50 shrink-0"
                  >
                    {analyzingAI ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        <span>AI analyzing recovery signals...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                        <span>{aiRec ? "Re-Analyze with AI" : "Analyze with AI"}</span>
                      </>
                    )}
                  </button>
                </div>

                {/* AI Error Warning */}
                {aiError && (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>{aiError}</span>
                  </div>
                )}

                {/* AI Analysis Result Display */}
                {aiRec ? (
                  <div className="space-y-4">
                    {/* Metrics 4-Col Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                        <div className="text-[11px] text-slate-400 font-medium">Recovery Prob.</div>
                        <div className="text-lg font-bold text-emerald-400 mt-0.5">
                          {(aiRec.recommendation.recovery_probability * 100).toFixed(0)}%
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                        <div className="text-[11px] text-slate-400 font-medium">Urgency</div>
                        <div className="mt-1">
                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded ${
                              aiRec.recommendation.urgency === "HIGH"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                : aiRec.recommendation.urgency === "MEDIUM"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                            }`}
                          >
                            {aiRec.recommendation.urgency}
                          </span>
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                        <div className="text-[11px] text-slate-400 font-medium">Confidence</div>
                        <div className="text-lg font-bold text-indigo-300 mt-0.5">
                          {(aiRec.recommendation.confidence * 100).toFixed(0)}%
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                        <div className="text-[11px] text-slate-400 font-medium">Policy Decision</div>
                        <div className="mt-1">
                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded flex items-center space-x-1 w-fit ${
                              aiRec.recommendation.policy_recommendation === "ALLOW"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : aiRec.recommendation.policy_recommendation === "REVIEW"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            <span>
                              {aiRec.recommendation.policy_recommendation === "ALLOW"
                                ? "✓ ALLOWED"
                                : aiRec.recommendation.policy_recommendation === "REVIEW"
                                ? "⚠ REVIEW"
                                : "✕ BLOCKED"}
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Recommended Action */}
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
                      <span className="text-xs text-slate-400 font-medium">Recommended Action:</span>
                      <span className="text-xs font-mono font-bold text-purple-300 bg-purple-500/10 px-2.5 py-1 rounded border border-purple-500/20">
                        {aiRec.recommendation.recommended_action}
                      </span>
                    </div>

                    {/* Reasoning Section (Why?) */}
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                      <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                        <HelpCircle className="h-3.5 w-3.5 text-purple-400" />
                        <span>Diagnostic Reasoning</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-sans">
                        "{aiRec.recommendation.reasoning}"
                      </p>
                    </div>

                    {/* Key Signals Bullet Points */}
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                        <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                        <span>Key Signals Detected</span>
                      </div>
                      <ul className="space-y-1 text-xs text-slate-300">
                        {aiRec.recommendation.signals.map((sig, idx) => (
                          <li key={idx} className="flex items-start space-x-2">
                            <span className="text-purple-400 text-sm leading-none">•</span>
                            <span>{sig}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center space-y-1 text-xs text-slate-400">
                    <p>Click <strong className="text-purple-300">"Analyze with AI"</strong> to generate deep failure diagnostics, behavioral probability scoring, and automated policy verification.</p>
                  </div>
                )}
              </div>

              {/* Recommended Action & Stage 3A Execution Trigger */}
              <div className="rounded-xl bg-gradient-to-r from-blue-950/40 via-indigo-950/40 to-slate-900 border border-blue-800/40 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                    Execution Trigger
                  </span>
                  <p className="text-base font-bold text-white mt-0.5 font-mono">
                    {detail.recommended_action}
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  {detail.status !== "RECOVERED" && detail.status !== "CANCELLED" && (
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

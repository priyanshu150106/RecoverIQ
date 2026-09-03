export interface DashboardMetrics {
  total_revenue_processed: number; // in paise
  revenue_at_risk: number; // in paise
  recovery_rate: number; // percentage (0 - 100)
  cases_detected: number;
  recovered_revenue: number; // in paise
  potential_recovery: number; // in paise
  active_cases_count: number;
  recovered_cases_count: number;
}

export interface CustomerInfo {
  id: number;
  name: string;
  email: string;
  phone?: string | null;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_paid: number; // in paise
  created_at: string;
}

export interface PaymentEventInfo {
  id: number;
  customer_id: number;
  event_type: string;
  amount: number; // in paise
  currency: string;
  status: string;
  failure_reason?: string | null;
  external_event_id?: string | null;
  created_at: string;
  customer?: CustomerInfo;
}

export interface RecoveryActionItem {
  id: number;
  recovery_case_id: number;
  action_type: string;
  status: string;
  external_reference?: string | null;
  payment_link_id?: string | null;
  payment_link_url?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface RecoveryCaseItem {
  id: number;
  customer_id: number;
  customer_name: string;
  customer_email: string;
  customer_phone?: string | null;
  amount: number; // in paise
  currency: string;
  event_type: string;
  failure_reason?: string | null;
  risk_score: number; // 0 to 100
  recovery_probability: number; // 0.0 to 1.0
  recommended_action: string;
  confidence: number; // 0.0 to 1.0
  status: string;
  created_at: string;
}

export interface RecoveryCaseDetail {
  id: number;
  customer_id: number;
  payment_event_id: number;
  risk_score: number;
  recovery_probability: number;
  recommended_action: string;
  confidence: number;
  status: string;
  created_at: string;
  customer: CustomerInfo;
  payment_event: PaymentEventInfo;
  recovery_actions: RecoveryActionItem[];
  scoring_breakdown?: {
    category?: string;
    customer_history?: string;
    amount_context?: string;
    model?: string;
  } | null;
}

export interface ExecuteLinkResponse {
  status: string;
  message: string;
  recovery_case_id: number;
  action_id: number;
  payment_link_id: string;
  payment_link_url: string;
  amount: number;
  currency: string;
}

export interface AIRecoveryRecommendation {
  recovery_probability: number; // 0.0 to 1.0
  recommended_action: string;
  urgency: "LOW" | "MEDIUM" | "HIGH";
  confidence: number; // 0.0 to 1.0
  reasoning: string;
  signals: string[];
  policy_recommendation: "ALLOW" | "BLOCK" | "REVIEW";
}

export interface AIRecoveryRecommendationResponse {
  status: string;
  recovery_case_id: number;
  source: "ai" | "fallback";
  model_used?: string | null;
  recommendation: AIRecoveryRecommendation;
}

export type ActorType =
  | "AI_AGENT"
  | "POLICY_ENGINE"
  | "RAZORPAY_EXECUTION"
  | "WEBHOOK_RECEIVER"
  | "SYSTEM";

export type ActionType =
  | "FAILURE_DETECTED"
  | "AI_DIAGNOSED"
  | "POLICY_PASSED"
  | "LINK_GENERATED"
  | "PAYMENT_CAPTURED"
  | "PAYMENT_PARTIALLY_CAPTURED"
  | "PAYMENT_CANCELLED"
  | "PAYMENT_EXPIRED"
  | "CASE_RECOVERED"
  | "RECOVERY_ACTION_FAILED";

export interface ActivityItem {
  id: string;
  timestamp: string;
  actor: ActorType;
  action: ActionType;
  summary: string;
  status: string;
  case_id?: number | null;
  amount?: number | null; // in paise
  metadata?: Record<string, any>;
}

export type StrategyType =
  | "SEND_SMART_RETRY_LINK"
  | "SEND_PAYMENT_LINK"
  | "SEND_REMINDER"
  | "NO_ACTION"
  | "HUMAN_REVIEW";

export interface RecoveryStrategyResponse {
  recovery_case_id: number;
  strategy: StrategyType;
  reason: string;
  risk_score: number;
  recovery_probability: number;
  confidence: number;
  requires_human_approval: boolean;
  allowed_to_execute: boolean;
}

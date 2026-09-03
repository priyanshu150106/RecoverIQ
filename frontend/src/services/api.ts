import {
  DashboardMetrics,
  RecoveryCaseItem,
  RecoveryCaseDetail,
  ExecuteLinkResponse,
  AIRecoveryRecommendationResponse,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard/metrics`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch metrics: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchRecoveryCases(
  status?: string
): Promise<RecoveryCaseItem[]> {
  const url = status
    ? `${API_BASE_URL}/api/recovery-cases?status=${encodeURIComponent(status)}`
    : `${API_BASE_URL}/api/recovery-cases`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch cases: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchRecoveryCaseDetail(
  caseId: number
): Promise<RecoveryCaseDetail> {
  const res = await fetch(`${API_BASE_URL}/api/recovery-cases/${caseId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `Failed to fetch case detail #${caseId}: ${res.status} ${res.statusText}`
    );
  }
  return res.json();
}

export async function fetchAIRecommendation(
  caseId: number
): Promise<AIRecoveryRecommendationResponse> {
  const res = await fetch(
    `${API_BASE_URL}/api/recovery-cases/${caseId}/ai-recommendation`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }
  );

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || `AI analysis failed with HTTP ${res.status}`);
  }
  return data;
}

export async function executePaymentLink(
  caseId: number,
  expireHours: number = 24
): Promise<ExecuteLinkResponse> {
  const res = await fetch(
    `${API_BASE_URL}/api/recovery-cases/${caseId}/execute-link`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expire_hours: expireHours }),
    }
  );

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || `Execution failed with HTTP ${res.status}`);
  }
  return data;
}

export async function ingestEvent(payload: Record<string, any>): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to ingest event: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function triggerSeedData(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/events/seed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to reset seed data: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function formatINR(paise: number): string {
  const rupees = (paise / 100).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  });
  return `₹${rupees}`;
}

// frontend/src/services/api.ts
const API_BASE = import.meta.env.VITE_API_URL || const API_URL = "https://hospital-timeline-ai-production.up.railway.app";

export interface SourceTrace {
  table: string;
  column: string;
  row_id: number;
  charttime: string | null;
}

export interface TimelineEvent {
  event_id: string;
  category: string;
  timestamp: string;
  end_timestamp: string | null;
  label: string;
  detail: Record<string, unknown>;
  source: SourceTrace;
  is_abnormal: boolean;
  uncertainty: string | null;
}

export interface EventGroup {
  group_id: string;
  category: string;
  start_time: string;
  end_time: string;
  event_count: number;
  summary_stats: Record<string, number>;
  representative_events: TimelineEvent[];
  is_collapsed: boolean;
  member_source_traces: SourceTrace[];
}

export interface PatientTimeline {
  subject_id: number;
  hadm_id: number;
  admission_time: string;
  discharge_time: string | null;
  events: TimelineEvent[];
  groups: EventGroup[];
  quality_report: Record<string, unknown>;
}

export interface QueryResponse {
  answer: string | null;
  sql: string;
  supporting_rows: number;
  evidence: Array<{ data: Record<string, unknown>; source_trace: SourceTrace }>;
  refused: boolean;
  error?: string;
}

export async function fetchTimeline(
  hadmId: number,
  categories?: string[]
): Promise<PatientTimeline> {
  const params = new URLSearchParams();
  if (categories?.length) params.set("categories", categories.join(","));
  const res = await fetch(`${API_BASE}/timeline/${hadmId}?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch timeline: ${res.statusText}`);
  return res.json();
}

export async function askQuestion(
  question: string,
  hadmId?: number
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, hadm_id: hadmId }),
  });
  if (!res.ok) throw new Error(`Query failed: ${res.statusText}`);
  return res.json();
}

export async function checkQuality(hadmId: number) {
  const res = await fetch(`${API_BASE}/validation/quality/${hadmId}`);
  return res.json();
}

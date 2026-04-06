import type { Chore } from "./chore";

export type SpinStatus = "PENDING" | "COMPLETED" | "SKIPPED" | "DEACTIVATED";

export interface SpinSession {
  id: string;
  chore: Chore;
  spun_at: string;
  completed_at: string | null;
  status: SpinStatus;
}

export interface SpinHistoryItem {
  id: string;
  chore_name: string;
  spun_at: string;
  completed_at: string | null;
  status: SpinStatus;
}

export interface SpinHistoryResponse {
  items: SpinHistoryItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface DailyProgressItem {
  chore_id: string;
  completed: number;
  skipped: number;
  deactivated: number;
  multiplicity: number;
}

export interface WheelSegment {
  chore_id: string;
  name: string;
  color: string;
  effective_weight: number;
}

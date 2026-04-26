import type { BucketKind } from "./bucket";

export type DashboardPeriod = "7d" | "30d" | "90d" | "year";

export const DASHBOARD_PERIODS: DashboardPeriod[] = ["7d", "30d", "90d", "year"];

export interface TodaySection {
  wheel: {
    pending: number;
    completed: number;
    skipped: number;
    deactivated: number;
  };
  earnings_today: string;
  in_progress: Record<BucketKind, number>;
  next_notification_minutes: number | null;
}

export interface DailyPoint {
  date: string;
  completed: number;
  skipped: number;
  deactivated: number;
  pending: number;
}

export interface HeatmapCell {
  weekday: number;
  hour: number;
  count: number;
}

export interface ProductivitySection {
  spins_per_day: DailyPoint[];
  completion_rate: number;
  current_streak_days: number;
  longest_streak_days: number;
  heatmap: HeatmapCell[];
}

export interface KanbanColumnCounts {
  to_do: number;
  in_progress: number;
  blocked: number;
  done: number;
}

export interface BlockedItem {
  id: string;
  name: string;
  kind: BucketKind;
  blocked_days: number;
}

export interface ThroughputPoint {
  week_start: string;
  adult: number;
  happy: number;
}

export interface KanbanSection {
  distribution: Record<BucketKind, KanbanColumnCounts>;
  avg_lead_time_hours: Record<BucketKind, number | null>;
  blocked_aging: BlockedItem[];
  throughput_per_week: ThroughputPoint[];
}

export interface EarningsPoint {
  date: string;
  amount: string;
}

export interface TopChore {
  chore_name: string;
  completions: number;
  amount: string;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface KindCounts {
  created: number;
  completed: number;
}

export interface WalletSection {
  earnings_per_day: EarningsPoint[];
  total: string;
  top_chores: TopChore[];
  top_chore_categories: CategoryCount[];
  top_bucket_categories: CategoryCount[];
  adult_vs_happy: Record<BucketKind, KindCounts>;
}

export interface WeeklyOverviewPoint {
  week_start: string;
  chores_completed: number;
  earnings: string;
}

export interface DashboardData {
  period: DashboardPeriod;
  today: TodaySection;
  productivity: ProductivitySection;
  weekly_overview: WeeklyOverviewPoint[];
  kanban: KanbanSection;
  wallet: WalletSection;
}

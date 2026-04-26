export type KanbanStatus = "to_do" | "in_progress" | "blocked" | "done";

export type BucketKind = "adult" | "happy";

export const KANBAN_COLUMNS: KanbanStatus[] = ["to_do", "in_progress", "blocked", "done"];

export interface BucketItem {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  status: KanbanStatus;
  kind: BucketKind;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DrawSuggestion {
  item: BucketItem;
}

export interface BucketSettings {
  max_in_progress: number;
}

export interface CreateBucketItemRequest {
  name: string;
  description?: string;
  category?: string;
}

export interface UpdateBucketItemRequest {
  name?: string;
  description?: string;
  category?: string;
}

export interface MoveBucketItemRequest {
  status: KanbanStatus;
}

export interface UpdateBucketSettingsRequest {
  max_in_progress: number;
}

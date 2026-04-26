import { apiClient } from "./client";
import type {
  BucketItem,
  BucketKind,
  BucketSettings,
  CreateBucketItemRequest,
  DrawSuggestion,
  KanbanStatus,
  UpdateBucketItemRequest,
  UpdateBucketSettingsRequest,
} from "@/types/bucket";

/** Fetch all bucket items for the given board. */
export async function listItems(kind: BucketKind): Promise<BucketItem[]> {
  const response = await apiClient.get<BucketItem[]>(`/bucket/${kind}/items`);
  return response.data;
}

/** Create a new bucket item on the given board (lands in TO_DO). */
export async function createItem(
  kind: BucketKind,
  data: CreateBucketItemRequest,
): Promise<BucketItem> {
  const response = await apiClient.post<BucketItem>(`/bucket/${kind}/items`, data);
  return response.data;
}

/** Update an existing bucket item's editable fields. */
export async function updateItem(
  kind: BucketKind,
  id: string,
  data: UpdateBucketItemRequest,
): Promise<BucketItem> {
  const response = await apiClient.put<BucketItem>(`/bucket/${kind}/items/${id}`, data);
  return response.data;
}

/** Delete a bucket item. */
export async function deleteItem(kind: BucketKind, id: string): Promise<void> {
  await apiClient.delete(`/bucket/${kind}/items/${id}`);
}

/** Move a bucket item to a different Kanban column. */
export async function moveItem(
  kind: BucketKind,
  id: string,
  status: KanbanStatus,
): Promise<BucketItem> {
  const response = await apiClient.put<BucketItem>(`/bucket/${kind}/items/${id}/move`, {
    status,
  });
  return response.data;
}

/** Transfer a bucket item to the other board (adult <-> happy). */
export async function transferItem(
  kind: BucketKind,
  id: string,
  target_kind: BucketKind,
): Promise<BucketItem> {
  const response = await apiClient.put<BucketItem>(
    `/bucket/${kind}/items/${id}/transfer`,
    { target_kind },
  );
  return response.data;
}

/** Get a random TO_DO item suggestion (does not change state). */
export async function drawSuggestion(kind: BucketKind): Promise<DrawSuggestion> {
  const response = await apiClient.post<DrawSuggestion>(`/bucket/${kind}/draw`);
  return response.data;
}

/** Get the user's Kanban settings for the given board. */
export async function getSettings(kind: BucketKind): Promise<BucketSettings> {
  const response = await apiClient.get<BucketSettings>(`/bucket/${kind}/settings`);
  return response.data;
}

/** Update the user's Kanban settings for the given board. */
export async function updateSettings(
  kind: BucketKind,
  data: UpdateBucketSettingsRequest,
): Promise<BucketSettings> {
  const response = await apiClient.put<BucketSettings>(`/bucket/${kind}/settings`, data);
  return response.data;
}

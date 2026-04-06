import { apiClient } from "./client";
import type { DailyProgressItem, SpinHistoryItem, SpinSession, WheelSegment } from "@/types/wheel";

/** Spin the wheel and get a chore assignment. */
export async function spin(): Promise<SpinSession> {
  const response = await apiClient.post<SpinSession>("/wheel/spin");
  return response.data;
}

/** Mark a spin session as completed. */
export async function completeSession(sessionId: string): Promise<void> {
  await apiClient.put(`/wheel/sessions/${sessionId}/complete`);
}

/** Skip a spin session. */
export async function skipSession(sessionId: string): Promise<void> {
  await apiClient.put(`/wheel/sessions/${sessionId}/skip`);
}

/** Get spin history for the current user. */
export async function getHistory(page = 1, perPage = 20): Promise<{ items: SpinHistoryItem[]; total: number }> {
  const response = await apiClient.get("/wheel/history", {
    params: { page, per_page: perPage },
  });
  return response.data;
}

/** Mark one instance of a chore as completed for today. */
export async function quickCompleteChore(choreId: string): Promise<void> {
  await apiClient.post(`/wheel/chores/${choreId}/complete`);
}

/** Mark one instance of a chore as skipped for today. */
export async function quickSkipChore(choreId: string): Promise<void> {
  await apiClient.post(`/wheel/chores/${choreId}/skip`);
}

/** Get daily completion/skip progress for all chores. */
export async function getDailyProgress(): Promise<DailyProgressItem[]> {
  const response = await apiClient.get<DailyProgressItem[]>("/wheel/daily-progress");
  return response.data;
}

/** Reset a specific chore for today by clearing its spin sessions. */
export async function resetChore(choreId: string): Promise<void> {
  await apiClient.delete(`/wheel/chores/${choreId}/reset`);
}

/** Deactivate one instance of a chore for today (not needed today). */
export async function quickDeactivateChore(choreId: string): Promise<void> {
  await apiClient.post(`/wheel/chores/${choreId}/deactivate`);
}

/** Reset today's wheel by clearing all spin sessions for the day. */
export async function resetDaily(): Promise<void> {
  await apiClient.delete("/wheel/reset-daily");
}

/** Get the current wheel segments with computed weights. */
export async function getSegments(): Promise<WheelSegment[]> {
  const response = await apiClient.get<WheelSegment[]>("/wheel/segments");
  return response.data;
}

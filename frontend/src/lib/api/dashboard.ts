import { apiClient } from "./client";
import type { DashboardData, DashboardPeriod } from "@/types/dashboard";

/** Fetch the dashboard payload for the given period. */
export async function getDashboard(period: DashboardPeriod): Promise<DashboardData> {
  const response = await apiClient.get<DashboardData>("/dashboard", {
    params: { period },
  });
  return response.data;
}

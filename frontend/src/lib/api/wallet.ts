import { apiClient } from "./client";

export interface WalletData {
  total_today: string;
  total_this_month: string;
  total_this_year: string;
  currency: string;
}

/** Fetch the authenticated user's wallet earnings summary. */
export async function getWallet(): Promise<WalletData> {
  const response = await apiClient.get<WalletData>("/wheel/wallet");
  return response.data;
}

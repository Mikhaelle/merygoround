"use client";

import { useCallback, useEffect, useState } from "react";
import { getWallet, type WalletData } from "@/lib/api/wallet";

/** Hook for fetching the user's wallet earnings summary. */
export function useWallet() {
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWallet = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getWallet();
      setWallet(data);
    } catch {
      setError("Failed to load wallet");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWallet();
  }, [fetchWallet]);

  return { wallet, isLoading, error, refetch: fetchWallet };
}

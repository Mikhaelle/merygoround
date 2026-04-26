"use client";

import { useCallback, useEffect, useState } from "react";
import { getDashboard } from "@/lib/api/dashboard";
import type { DashboardData, DashboardPeriod } from "@/types/dashboard";

/**
 * Fetch and re-fetch dashboard data when the selected period changes.
 * @returns Dashboard data, loading state, error and a setter for the period.
 */
export function useDashboard(initial: DashboardPeriod = "7d") {
  const [period, setPeriod] = useState<DashboardPeriod>(initial);
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const fetchData = useCallback(
    async (p: DashboardPeriod, signal: { cancelled: boolean }) => {
      try {
        const fresh = await getDashboard(p);
        if (!signal.cancelled) {
          setData(fresh);
          setError(null);
        }
      } catch (err) {
        if (!signal.cancelled) setError(err);
      } finally {
        if (!signal.cancelled) setIsLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    const signal = { cancelled: false };
    fetchData(period, signal);
    return () => {
      signal.cancelled = true;
    };
  }, [period, fetchData]);

  return { data, period, setPeriod, isLoading, error };
}

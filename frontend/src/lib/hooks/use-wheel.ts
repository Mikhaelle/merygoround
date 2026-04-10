"use client";

import { useCallback, useEffect, useState } from "react";
import type { SpinHistoryItem, SpinSession, WheelSegment } from "@/types/wheel";
import * as wheelApi from "@/lib/api/wheel";

/**
 * Manage wheel state including segments, spinning, and history.
 * @returns Segments, history, and wheel interaction functions.
 */
export function useWheel() {
  const [segments, setSegments] = useState<WheelSegment[]>([]);
  const [history, setHistory] = useState<SpinHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSpinning, setIsSpinning] = useState(false);

  const fetchSegments = useCallback(async () => {
    try {
      const data = await wheelApi.getSegments();
      setSegments(data);
    } catch {
      /* segments may not be available if no chores exist */
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await wheelApi.getHistory();
      setHistory(data.items);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchSegments(), fetchHistory()]).finally(() => setIsLoading(false));
  }, [fetchSegments, fetchHistory]);

  const spin = useCallback(async (): Promise<SpinSession> => {
    setIsSpinning(true);
    try {
      const session = await wheelApi.spin();
      await fetchSegments();
      return session;
    } finally {
      setIsSpinning(false);
    }
  }, [fetchSegments]);

  const completeSession = useCallback(
    async (sessionId: string) => {
      await wheelApi.completeSession(sessionId);
      await Promise.all([fetchHistory(), fetchSegments()]);
    },
    [fetchHistory, fetchSegments],
  );

  const skipSession = useCallback(
    async (sessionId: string) => {
      await wheelApi.skipSession(sessionId);
      await Promise.all([fetchHistory(), fetchSegments()]);
    },
    [fetchHistory, fetchSegments],
  );

  const resetDaily = useCallback(async () => {
    await wheelApi.resetDaily();
    await Promise.all([fetchHistory(), fetchSegments()]);
  }, [fetchHistory, fetchSegments]);

  return {
    segments,
    history,
    isLoading,
    isSpinning,
    fetchSegments,
    fetchHistory,
    spin,
    completeSession,
    skipSession,
    resetDaily,
  };
}

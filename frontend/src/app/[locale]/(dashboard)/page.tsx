"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { useWheel } from "@/lib/hooks/use-wheel";
import { SpinningWheel } from "@/components/wheel/spinning-wheel";
import { SpinButton } from "@/components/wheel/spin-button";
import { SpinResultModal } from "@/components/wheel/spin-result-modal";
import { SpinHistory } from "@/components/wheel/spin-history";
import { ResetDailyButton } from "@/components/wheel/reset-daily-button";
import type { SpinSession } from "@/types/wheel";
import { toast } from "sonner";

/** Main wheel page - the hero dashboard view. */
export default function WheelPage() {
  const t = useTranslations("wheel");
  const {
    segments,
    history,
    isLoading,
    isSpinning,
    spin,
    completeSession,
    skipSession,
    resetDaily,
  } = useWheel();

  const [animatingSpinning, setAnimatingSpinning] = useState(false);
  const [targetIndex, setTargetIndex] = useState<number | null>(null);
  const [currentSession, setCurrentSession] = useState<SpinSession | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);

  const handleSpinStart = useCallback(async () => {
    if (animatingSpinning || segments.length === 0) return;

    try {
      const session = await spin();
      setCurrentSession(session);

      const segIndex = segments.findIndex((s) => s.chore_id === session.chore.id);
      const targetIdx = segIndex >= 0 ? segIndex : 0;

      setTargetIndex(targetIdx);
      setAnimatingSpinning(true);
    } catch {
      toast.error(t("noChores"));
    }
  }, [animatingSpinning, segments, spin, t]);

  const handleSpinEnd = useCallback(() => {
    setAnimatingSpinning(false);
    setTargetIndex(null);
    setShowResult(true);
  }, []);

  const handleComplete = useCallback(async () => {
    if (!currentSession) return;
    setIsActionLoading(true);
    try {
      await completeSession(currentSession.id);
      toast.success(t("spinSuccess"));
      setShowResult(false);
      setCurrentSession(null);
    } catch {
      toast.error(t("actionError"));
    } finally {
      setIsActionLoading(false);
    }
  }, [currentSession, completeSession, t]);

  const handleSkip = useCallback(async () => {
    if (!currentSession) return;
    setIsActionLoading(true);
    try {
      await skipSession(currentSession.id);
      toast.info(t("spinSkipped"));
      setShowResult(false);
      setCurrentSession(null);
    } catch {
      toast.error(t("actionError"));
    } finally {
      setIsActionLoading(false);
    }
  }, [currentSession, skipSession, t]);

  const handleHistoryComplete = useCallback(
    async (sessionId: string) => {
      try {
        await completeSession(sessionId);
        toast.success(t("spinSuccess"));
      } catch {
        toast.error(t("actionError"));
      }
    },
    [completeSession, t],
  );

  const handleHistorySkip = useCallback(
    async (sessionId: string) => {
      try {
        await skipSession(sessionId);
        toast.info(t("spinSkipped"));
      } catch {
        toast.error(t("actionError"));
      }
    },
    [skipSession, t],
  );

  const handleResetDaily = useCallback(async () => {
    try {
      await resetDaily();
      toast.success(t("resetDailySuccess"));
      setCurrentSession(null);
      setShowResult(false);
    } catch {
      toast.error(t("actionError"));
    }
  }, [resetDaily, t]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="size-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col items-center gap-6">
          <SpinningWheel
            segments={segments}
            onSpinStart={handleSpinStart}
            onSpinEnd={handleSpinEnd}
            isSpinning={animatingSpinning}
            targetSegmentIndex={targetIndex}
          />
          <SpinButton
            onSpin={handleSpinStart}
            isSpinning={animatingSpinning || isSpinning}
            disabled={segments.length === 0}
          />
          <ResetDailyButton
            onReset={handleResetDaily}
            disabled={animatingSpinning || isSpinning || history.length === 0}
          />
        </div>

        <div className="hidden lg:block">
          <SpinHistory history={history} onComplete={handleHistoryComplete} onSkip={handleHistorySkip} />
        </div>
      </div>

      <div className="lg:hidden">
        <SpinHistory history={history} onComplete={handleHistoryComplete} onSkip={handleHistorySkip} />
      </div>

      <SpinResultModal
        session={currentSession}
        open={showResult}
        onOpenChange={setShowResult}
        onComplete={handleComplete}
        onSkip={handleSkip}
        isLoading={isActionLoading}
      />
    </div>
  );
}

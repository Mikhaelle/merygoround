"use client";

import { useTranslations } from "next-intl";
import { useDashboard } from "@/lib/hooks/use-dashboard";
import { PeriodSelector } from "@/components/dashboard/period-selector";
import { TodayCards } from "@/components/dashboard/today-cards";
import { ProductivitySection } from "@/components/dashboard/productivity-section";
import { WeeklyOverviewSection } from "@/components/dashboard/weekly-overview-section";
import { KanbanSection } from "@/components/dashboard/kanban-section";
import { WalletSection } from "@/components/dashboard/wallet-section";

/** Aggregated user dashboard with period filter (7d / 30d / 90d / year). */
export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const { data, period, setPeriod, isLoading, error } = useDashboard("7d");

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="size-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="py-20 text-center text-muted-foreground">
        <p>{t("loadError")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
          <p className="text-xs text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      <TodayCards today={data.today} />
      <ProductivitySection data={data.productivity} />
      <WeeklyOverviewSection data={data.weekly_overview} />
      <WalletSection data={data.wallet} />
      <KanbanSection data={data.kanban} />
    </div>
  );
}

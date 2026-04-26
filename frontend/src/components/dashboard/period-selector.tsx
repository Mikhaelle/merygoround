"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { DASHBOARD_PERIODS, type DashboardPeriod } from "@/types/dashboard";

interface PeriodSelectorProps {
  value: DashboardPeriod;
  onChange: (next: DashboardPeriod) => void;
}

/** Pill toggle to switch between dashboard time windows. */
export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  const t = useTranslations("dashboard.period");

  return (
    <div className="inline-flex items-center rounded-lg border border-border bg-muted/40 p-1 gap-1">
      {DASHBOARD_PERIODS.map((p) => (
        <Button
          key={p}
          size="sm"
          variant={p === value ? "default" : "ghost"}
          onClick={() => onChange(p)}
          className={
            p === value
              ? "bg-indigo-600 hover:bg-indigo-700 text-white h-7 px-3"
              : "h-7 px-3 text-muted-foreground"
          }
        >
          {t(p)}
        </Button>
      ))}
    </div>
  );
}

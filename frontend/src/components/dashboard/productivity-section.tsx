"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Flame, Target } from "lucide-react";
import type { ProductivitySection as ProductivityData } from "@/types/dashboard";

interface ProductivitySectionProps {
  data: ProductivityData;
}

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const WEEKDAYS = [0, 1, 2, 3, 4, 5, 6];

function formatShortDate(d: string): string {
  const date = new Date(d + "T00:00:00");
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

/** Productivity charts: spins per day stacked bar, streak cards, heatmap. */
export function ProductivitySection({ data }: ProductivitySectionProps) {
  const t = useTranslations("dashboard.productivity");

  const barData = useMemo(
    () =>
      data.spins_per_day.map((p) => ({
        date: formatShortDate(p.date),
        completed: p.completed,
        skipped: p.skipped,
        deactivated: p.deactivated,
        pending: p.pending,
      })),
    [data.spins_per_day],
  );

  const heatmapMax = useMemo(
    () => data.heatmap.reduce((max, c) => Math.max(max, c.count), 0),
    [data.heatmap],
  );
  const heatmapLookup = useMemo(() => {
    const map = new Map<string, number>();
    for (const c of data.heatmap) map.set(`${c.weekday}-${c.hour}`, c.count);
    return map;
  }, [data.heatmap]);

  const completionPct = Math.round(data.completion_rate * 100);

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">{t("title")}</h2>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Target className="size-4 text-indigo-500" />
              <CardTitle className="text-sm font-medium">
                {t("completionRate")}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{completionPct}%</p>
            <CardDescription>{t("completionRateHint")}</CardDescription>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Flame className="size-4 text-orange-500" />
              <CardTitle className="text-sm font-medium">
                {t("currentStreak")}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {data.current_streak_days}
              <span className="text-sm font-normal text-muted-foreground ml-1">
                {t("days")}
              </span>
            </p>
            <CardDescription>{t("currentStreakHint")}</CardDescription>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Flame className="size-4 text-amber-600" />
              <CardTitle className="text-sm font-medium">
                {t("longestStreak")}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {data.longest_streak_days}
              <span className="text-sm font-normal text-muted-foreground ml-1">
                {t("days")}
              </span>
            </p>
            <CardDescription>{t("longestStreakHint")}</CardDescription>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{t("spinsPerDay")}</CardTitle>
          <CardDescription>{t("spinsPerDayHint")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 -ml-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar
                  dataKey="completed"
                  stackId="s"
                  name={t("legendCompleted")}
                  fill="#10b981"
                />
                <Bar
                  dataKey="skipped"
                  stackId="s"
                  name={t("legendSkipped")}
                  fill="#f59e0b"
                />
                <Bar
                  dataKey="deactivated"
                  stackId="s"
                  name={t("legendDeactivated")}
                  fill="#9ca3af"
                />
                <Bar
                  dataKey="pending"
                  stackId="s"
                  name={t("legendPending")}
                  fill="#6366f1"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{t("heatmap")}</CardTitle>
          <CardDescription>{t("heatmapHint")}</CardDescription>
        </CardHeader>
        <CardContent>
          {heatmapMax === 0 ? (
            <p className="text-xs text-muted-foreground italic py-6 text-center">
              {t("heatmapEmpty")}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <div
                className="grid"
                style={{ gridTemplateColumns: "auto repeat(24, minmax(14px, 1fr))" }}
              >
                <div />
                {HOURS.map((h) => (
                  <div
                    key={`h-${h}`}
                    className="text-[9px] text-muted-foreground text-center"
                  >
                    {h % 3 === 0 ? h : ""}
                  </div>
                ))}
                {WEEKDAYS.map((wd) => (
                  <div key={`row-${wd}`} className="contents">
                    <div className="text-[10px] text-muted-foreground pr-2 leading-4">
                      {t(`weekday.${wd}`)}
                    </div>
                    {HOURS.map((h) => {
                      const count = heatmapLookup.get(`${wd}-${h}`) ?? 0;
                      const intensity = heatmapMax === 0 ? 0 : count / heatmapMax;
                      const bg = `rgba(99, 102, 241, ${
                        count === 0 ? 0.06 : 0.18 + 0.65 * intensity
                      })`;
                      return (
                        <div
                          key={`c-${wd}-${h}`}
                          title={t("heatmapTooltip", { count, weekday: t(`weekday.${wd}`), hour: h })}
                          style={{ backgroundColor: bg }}
                          className="h-4 rounded-sm m-[1px]"
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

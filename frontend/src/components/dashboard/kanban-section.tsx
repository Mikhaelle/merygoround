"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type {
  KanbanColumnCounts,
  KanbanSection as KanbanData,
} from "@/types/dashboard";
import type { BucketKind } from "@/types/bucket";

interface KanbanSectionProps {
  data: KanbanData;
}

const COLUMN_COLORS = ["#94a3b8", "#6366f1", "#f59e0b", "#10b981"];

function buildPie(counts: KanbanColumnCounts) {
  return [
    { name: "to_do", value: counts.to_do },
    { name: "in_progress", value: counts.in_progress },
    { name: "blocked", value: counts.blocked },
    { name: "done", value: counts.done },
  ];
}

function formatWeek(d: string): string {
  const date = new Date(d + "T00:00:00");
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

/** Kanban health: distribution donut, lead time, blocked aging, throughput. */
export function KanbanSection({ data }: KanbanSectionProps) {
  const t = useTranslations("dashboard.kanban");
  const tCols = useTranslations("bucket.column");

  const adultPie = useMemo(() => buildPie(data.distribution.adult), [data.distribution.adult]);
  const happyPie = useMemo(() => buildPie(data.distribution.happy), [data.distribution.happy]);

  const throughputData = useMemo(
    () =>
      data.throughput_per_week.map((p) => ({
        week: formatWeek(p.week_start),
        adult: p.adult,
        happy: p.happy,
      })),
    [data.throughput_per_week],
  );

  const leadAdult = data.avg_lead_time_hours.adult;
  const leadHappy = data.avg_lead_time_hours.happy;

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-foreground">{t("title")}</h2>

      <div className="grid gap-3 md:grid-cols-2">
        {(["adult", "happy"] as BucketKind[]).map((kind) => (
          <Card key={kind}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {t(`distributionTitle.${kind}`)}
              </CardTitle>
              <CardDescription>
                {t("avgLeadTime", {
                  hours:
                    (kind === "adult" ? leadAdult : leadHappy)?.toFixed(1) ?? "-",
                })}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={kind === "adult" ? adultPie : happyPie}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      stroke="none"
                    >
                      {(kind === "adult" ? adultPie : happyPie).map((_, i) => (
                        <Cell key={i} fill={COLUMN_COLORS[i]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value, name) => [
                        Number(value),
                        tCols(String(name)),
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                {(["to_do", "in_progress", "blocked", "done"] as const).map(
                  (col, i) => (
                    <div key={col} className="flex items-center gap-1.5">
                      <span
                        className="size-2.5 rounded-sm"
                        style={{ backgroundColor: COLUMN_COLORS[i] }}
                      />
                      <span className="text-muted-foreground">{tCols(col)}:</span>
                      <span className="font-medium">
                        {data.distribution[kind][col]}
                      </span>
                    </div>
                  ),
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{t("throughput")}</CardTitle>
          <CardDescription>{t("throughputHint")}</CardDescription>
        </CardHeader>
        <CardContent>
          {throughputData.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-6 text-center">
              {t("throughputEmpty")}
            </p>
          ) : (
            <div className="h-56 -ml-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={throughputData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line
                    type="monotone"
                    dataKey="adult"
                    name={t("legendAdult")}
                    stroke="#a855f7"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="happy"
                    name={t("legendHappy")}
                    stroke="#f59e0b"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{t("blockedAging")}</CardTitle>
          <CardDescription>{t("blockedAgingHint")}</CardDescription>
        </CardHeader>
        <CardContent>
          {data.blocked_aging.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-4 text-center">
              {t("blockedAgingEmpty")}
            </p>
          ) : (
            <ul className="space-y-1.5">
              {data.blocked_aging.map((b) => (
                <li
                  key={b.id}
                  className="flex items-center justify-between gap-2 rounded-md bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-sm"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Badge
                      variant="outline"
                      className="text-[10px] border-amber-300 text-amber-700 dark:border-amber-700 dark:text-amber-400 shrink-0"
                    >
                      {b.kind}
                    </Badge>
                    <span className="truncate text-foreground">{b.name}</span>
                  </div>
                  <span className="text-xs text-amber-700 dark:text-amber-400 font-mono shrink-0">
                    {t("daysBlocked", { days: b.blocked_days })}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

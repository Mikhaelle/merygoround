"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeeklyOverviewPoint } from "@/types/dashboard";

interface WeeklyOverviewSectionProps {
  data: WeeklyOverviewPoint[];
}

function formatWeekLabel(d: string): string {
  const date = new Date(d + "T00:00:00");
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

function brl(value: number): string {
  return Number(value).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  });
}

/** Combined weekly view: chores completed (bars) + earnings (line, R$). */
export function WeeklyOverviewSection({ data }: WeeklyOverviewSectionProps) {
  const t = useTranslations("dashboard.weekly");

  const chartData = useMemo(
    () =>
      data.map((p) => ({
        week: formatWeekLabel(p.week_start),
        chores: p.chores_completed,
        earnings: Number(p.earnings),
      })),
    [data],
  );

  const totals = useMemo(() => {
    const chores = data.reduce((acc, p) => acc + p.chores_completed, 0);
    const earnings = data.reduce((acc, p) => acc + Number(p.earnings), 0);
    return { chores, earnings };
  }, [data]);

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-foreground">{t("title")}</h2>
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <CardTitle className="text-sm font-medium">{t("cardTitle")}</CardTitle>
              <CardDescription>{t("cardHint")}</CardDescription>
            </div>
            <div className="flex gap-4 text-right">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase">
                  {t("totalChores")}
                </p>
                <p className="text-base font-bold text-indigo-600 dark:text-indigo-400">
                  {totals.chores}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase">
                  {t("totalEarnings")}
                </p>
                <p className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                  {brl(totals.earnings)}
                </p>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {chartData.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-6 text-center">
              {t("empty")}
            </p>
          ) : (
            <div className="h-64 -ml-4">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 11 }}
                    allowDecimals={false}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v) => `R$${v}`}
                  />
                  <Tooltip
                    formatter={(value, name) => {
                      if (name === t("legendEarnings")) {
                        return [brl(Number(value)), name];
                      }
                      return [Number(value), name];
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar
                    yAxisId="left"
                    dataKey="chores"
                    name={t("legendChores")}
                    fill="#6366f1"
                    radius={[4, 4, 0, 0]}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="earnings"
                    name={t("legendEarnings")}
                    stroke="#10b981"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: "#10b981" }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

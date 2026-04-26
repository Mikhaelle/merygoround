"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { WalletSection as WalletData } from "@/types/dashboard";

interface WalletSectionProps {
  data: WalletData;
}

function brl(value: number | string): string {
  return Number(value).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function formatShortDate(d: string): string {
  const date = new Date(d + "T00:00:00");
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

/** Wallet earnings curve, top chores, top categories, adult vs happy breakdown. */
export function WalletSection({ data }: WalletSectionProps) {
  const t = useTranslations("dashboard.wallet");

  const earningsChart = useMemo(
    () =>
      data.earnings_per_day.map((p) => ({
        date: formatShortDate(p.date),
        amount: Number(p.amount),
      })),
    [data.earnings_per_day],
  );

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-foreground">{t("title")}</h2>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm font-medium">{t("earnings")}</CardTitle>
              <CardDescription>{t("earningsHint")}</CardDescription>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-muted-foreground uppercase">
                {t("totalLabel")}
              </p>
              <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                {brl(data.total)}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {earningsChart.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-6 text-center">
              {t("earningsEmpty")}
            </p>
          ) : (
            <div className="h-56 -ml-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={earningsChart}>
                  <defs>
                    <linearGradient id="earnFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(value) => brl(Number(value))} />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    stroke="#10b981"
                    strokeWidth={2}
                    fill="url(#earnFill)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t("topChores")}</CardTitle>
            <CardDescription>{t("topChoresHint")}</CardDescription>
          </CardHeader>
          <CardContent>
            {data.top_chores.length === 0 ? (
              <p className="text-xs text-muted-foreground italic py-4 text-center">
                {t("topChoresEmpty")}
              </p>
            ) : (
              <ul className="space-y-1.5">
                {data.top_chores.map((c, i) => (
                  <li
                    key={c.chore_name + i}
                    className="flex items-center justify-between gap-2 text-sm"
                  >
                    <span className="truncate text-foreground">
                      <span className="text-muted-foreground mr-1.5">
                        {i + 1}.
                      </span>
                      {c.chore_name}
                    </span>
                    <span className="shrink-0 flex gap-2 items-center">
                      <Badge variant="secondary" className="text-[10px]">
                        x{c.completions}
                      </Badge>
                      <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400">
                        {brl(c.amount)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t("adultVsHappy")}</CardTitle>
            <CardDescription>{t("adultVsHappyHint")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(["adult", "happy"] as const).map((k) => {
              const v = data.adult_vs_happy[k];
              const completionPct =
                v.created > 0 ? Math.round((v.completed / v.created) * 100) : 0;
              const tone = k === "adult" ? "bg-fuchsia-500" : "bg-amber-500";
              return (
                <div key={k}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium text-foreground">
                      {t(`kind.${k}`)}
                    </span>
                    <span className="text-muted-foreground">
                      {t("createdCompleted", {
                        created: v.created,
                        completed: v.completed,
                      })}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={"h-full " + tone}
                      style={{ width: `${completionPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              {t("topChoreCategories")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_chore_categories.length === 0 ? (
              <p className="text-xs text-muted-foreground italic py-4 text-center">
                {t("categoriesEmpty")}
              </p>
            ) : (
              <ul className="space-y-1">
                {data.top_chore_categories.map((c, i) => (
                  <li
                    key={c.category + i}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-foreground truncate">{c.category}</span>
                    <Badge variant="secondary" className="text-[10px]">
                      {c.count}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              {t("topBucketCategories")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_bucket_categories.length === 0 ? (
              <p className="text-xs text-muted-foreground italic py-4 text-center">
                {t("categoriesEmpty")}
              </p>
            ) : (
              <ul className="space-y-1">
                {data.top_bucket_categories.map((c, i) => (
                  <li
                    key={c.category + i}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-foreground truncate">{c.category}</span>
                    <Badge variant="secondary" className="text-[10px]">
                      {c.count}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

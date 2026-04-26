"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Disc3, Wallet, Palette, Smile, Bell } from "lucide-react";
import type { TodaySection } from "@/types/dashboard";

interface TodayCardsProps {
  today: TodaySection;
}

/** Top-row stat cards summarising the user's current local day. */
export function TodayCards({ today }: TodayCardsProps) {
  const t = useTranslations("dashboard.today");
  const totalSpins =
    today.wheel.completed +
    today.wheel.skipped +
    today.wheel.deactivated +
    today.wheel.pending;

  const earnings = Number(today.earnings_today).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });

  const cards = [
    {
      icon: Disc3,
      tone: "from-indigo-500 to-purple-500",
      label: t("wheelToday"),
      value: `${today.wheel.completed}/${totalSpins}`,
      hint: t("wheelHint"),
    },
    {
      icon: Wallet,
      tone: "from-emerald-500 to-teal-500",
      label: t("earningsToday"),
      value: earnings,
      hint: t("earningsHint"),
    },
    {
      icon: Palette,
      tone: "from-fuchsia-500 to-pink-500",
      label: t("inProgressAdult"),
      value: today.in_progress.adult.toString(),
      hint: t("inProgressHint"),
    },
    {
      icon: Smile,
      tone: "from-amber-500 to-orange-500",
      label: t("inProgressHappy"),
      value: today.in_progress.happy.toString(),
      hint: t("inProgressHint"),
    },
    {
      icon: Bell,
      tone: "from-sky-500 to-blue-500",
      label: t("nextNotification"),
      value:
        today.next_notification_minutes === null
          ? t("disabled")
          : t("inMinutes", { minutes: today.next_notification_minutes }),
      hint: t("nextNotificationHint"),
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      {cards.map((c) => (
        <Card key={c.label} className="overflow-hidden">
          <CardContent className="p-4 flex items-center gap-3">
            <div
              className={
                "shrink-0 size-10 rounded-lg flex items-center justify-center text-white bg-gradient-to-br " +
                c.tone
              }
            >
              <c.icon className="size-5" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] text-muted-foreground uppercase tracking-wide truncate">
                {c.label}
              </p>
              <p className="text-lg font-bold text-foreground truncate">{c.value}</p>
              <p className="text-[10px] text-muted-foreground truncate">{c.hint}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

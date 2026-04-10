"use client";

import { useTranslations } from "next-intl";
import { useWallet } from "@/lib/hooks/use-wallet";
import { formatBRL } from "@/lib/utils/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Coins } from "lucide-react";

/** Wallet page showing BRL earnings from completed chores (today, month, year). */
export default function WalletPage() {
  const t = useTranslations("wallet");
  const { wallet, isLoading } = useWallet();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="size-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
        <p className="text-muted-foreground mt-1">{t("subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-emerald-200 dark:border-emerald-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Coins className="size-4 text-emerald-600" />
              {t("totalToday")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-emerald-600">
              {formatBRL(wallet?.total_today ?? "0")}
            </p>
          </CardContent>
        </Card>

        <Card className="border-indigo-200 dark:border-indigo-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Coins className="size-4 text-indigo-600" />
              {t("totalMonth")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-indigo-600">
              {formatBRL(wallet?.total_this_month ?? "0")}
            </p>
          </CardContent>
        </Card>

        <Card className="border-purple-200 dark:border-purple-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Coins className="size-4 text-purple-600" />
              {t("totalYear")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">
              {formatBRL(wallet?.total_this_year ?? "0")}
            </p>
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">{t("completedChoresOnly")}</p>
    </div>
  );
}

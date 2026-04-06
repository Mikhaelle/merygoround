"use client";

import { useTranslations } from "next-intl";
import { useLocale } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock, Check, SkipForward, Hourglass, EyeOff } from "lucide-react";
import type { SpinHistoryItem } from "@/types/wheel";
import { formatDateTime } from "@/lib/utils/format";

interface SpinHistoryProps {
  history: SpinHistoryItem[];
  onComplete?: (sessionId: string) => void;
  onSkip?: (sessionId: string) => void;
}

/** Displays recent spin sessions with their status and actions for pending items. */
export function SpinHistory({ history, onComplete, onSkip }: SpinHistoryProps) {
  const t = useTranslations("wheel");
  const locale = useLocale();

  if (history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("recentSpins")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">{t("noHistory")}</p>
        </CardContent>
      </Card>
    );
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case "COMPLETED":
        return <Check className="size-3.5" />;
      case "SKIPPED":
        return <SkipForward className="size-3.5" />;
      case "DEACTIVATED":
        return <EyeOff className="size-3.5" />;
      default:
        return <Hourglass className="size-3.5" />;
    }
  }

  function getStatusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
    switch (status) {
      case "COMPLETED":
        return "default";
      case "SKIPPED":
      case "DEACTIVATED":
        return "secondary";
      default:
        return "outline";
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case "COMPLETED":
        return t("completed");
      case "SKIPPED":
        return t("skipped");
      case "DEACTIVATED":
        return t("deactivated");
      default:
        return t("pending");
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t("recentSpins")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {history.slice(0, 10).map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between gap-3 p-3 rounded-lg bg-muted/50"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{item.chore_name}</p>
              <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                <Clock className="size-3" />
                {formatDateTime(item.spun_at, locale)}
              </div>
            </div>
            {item.status === "PENDING" && onComplete && onSkip ? (
              <div className="flex gap-1.5 shrink-0">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-2 text-xs"
                  onClick={() => onSkip(item.id)}
                >
                  <SkipForward className="size-3" />
                </Button>
                <Button
                  size="sm"
                  className="h-7 px-2 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                  onClick={() => onComplete(item.id)}
                >
                  <Check className="size-3" />
                </Button>
              </div>
            ) : (
              <Badge variant={getStatusVariant(item.status)} className="gap-1 shrink-0">
                {getStatusIcon(item.status)}
                {getStatusLabel(item.status)}
              </Badge>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

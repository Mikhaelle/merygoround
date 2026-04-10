"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Clock, Coins, Layers, Check, EyeOff, RotateCcw } from "lucide-react";
import type { Chore } from "@/types/chore";
import type { DailyProgressItem } from "@/types/wheel";
import { formatBRL, formatDuration } from "@/lib/utils/format";

interface ChoreCardProps {
  chore: Chore;
  progress?: DailyProgressItem;
  onEdit: (chore: Chore) => void;
  onDelete: (chore: Chore) => void;
  onComplete?: (choreId: string) => void;
  onDeactivate?: (choreId: string) => void;
  onReset?: (choreId: string) => void;
}

/** Card displaying a single chore with complete/deactivate/reset actions. */
export function ChoreCard({ chore, progress, onEdit, onDelete, onComplete, onDeactivate, onReset }: ChoreCardProps) {
  const t = useTranslations("chores");

  const completed = progress?.completed ?? 0;
  const deactivated = progress?.deactivated ?? 0;
  const multiplicity = chore.wheel_config.multiplicity;
  const done = completed + deactivated;
  const allDone = done >= multiplicity;
  const hasDayProgress = done > 0 || (progress?.skipped ?? 0) > 0;

  return (
    <Card className={`group hover:shadow-md transition-all duration-200 hover:border-indigo-200 dark:hover:border-indigo-800 ${allDone ? "opacity-60" : ""}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-foreground truncate">{chore.name}</h3>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <Badge variant="outline" className="gap-1">
                <Clock className="size-3" />
                {formatDuration(chore.estimated_duration_minutes)}
              </Badge>
              {chore.category && <Badge variant="secondary">{chore.category}</Badge>}
              <Badge
                variant="outline"
                className="gap-1 border-emerald-300 text-emerald-700 dark:border-emerald-600 dark:text-emerald-400"
              >
                <Coins className="size-3" />
                {formatBRL(chore.reward_value)}
              </Badge>
              {multiplicity > 1 && (
                <Badge
                  variant="outline"
                  className="gap-1 border-amber-300 text-amber-700 dark:border-amber-600 dark:text-amber-400"
                >
                  <Layers className="size-3" />
                  {completed}/{multiplicity}
                </Badge>
              )}
              {multiplicity === 1 && allDone && (
                <Badge variant="default" className="gap-1 bg-emerald-600">
                  <Check className="size-3" />
                  {t("done")}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon-sm" onClick={() => onEdit(chore)}>
              <Pencil className="size-3.5" />
              <span className="sr-only">{t("editChore")}</span>
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              className="hover:text-destructive"
              onClick={() => onDelete(chore)}
            >
              <Trash2 className="size-3.5" />
              <span className="sr-only">{t("deleteChore")}</span>
            </Button>
          </div>
        </div>

        {onComplete && onDeactivate && (
          <div className="flex gap-2 mt-3 pt-3 border-t">
            <Button
              size="sm"
              variant="outline"
              className="flex-1 h-8 text-xs"
              disabled={allDone}
              onClick={() => onDeactivate(chore.id)}
            >
              <EyeOff className="size-3.5" />
              {t("deactivate")}
            </Button>
            <Button
              size="sm"
              className="flex-1 h-8 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
              disabled={allDone}
              onClick={() => onComplete(chore.id)}
            >
              <Check className="size-3.5" />
              {t("complete")}
            </Button>
            {hasDayProgress && onReset && (
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground"
                onClick={() => onReset(chore.id)}
              >
                <RotateCcw className="size-3.5" />
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

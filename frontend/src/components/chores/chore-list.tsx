"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ChoreCard } from "./chore-card";
import { Plus, Search, RotateCcw } from "lucide-react";
import type { Chore } from "@/types/chore";
import type { DailyProgressItem } from "@/types/wheel";

interface ChoreListProps {
  chores: Chore[];
  progress: DailyProgressItem[];
  onAdd: () => void;
  onEdit: (chore: Chore) => void;
  onDelete: (chore: Chore) => void;
  onComplete: (choreId: string) => void;
  onDeactivate: (choreId: string) => void;
  onResetChore: (choreId: string) => void;
  onResetDaily: () => void;
  hasDailyProgress: boolean;
}

/** Searchable grid of chore cards with add and reset buttons. */
export function ChoreList({
  chores,
  progress,
  onAdd,
  onEdit,
  onDelete,
  onComplete,
  onDeactivate,
  onResetChore,
  onResetDaily,
  hasDailyProgress,
}: ChoreListProps) {
  const t = useTranslations("chores");
  const tCommon = useTranslations("common");
  const [search, setSearch] = useState("");
  const [confirmingReset, setConfirmingReset] = useState(false);

  const progressMap = new Map(progress.map((p) => [p.chore_id, p]));

  const filteredChores = chores.filter(
    (chore) =>
      chore.name.toLowerCase().includes(search.toLowerCase()) ||
      chore.category?.toLowerCase().includes(search.toLowerCase()),
  );

  const handleResetClick = () => {
    if (!confirmingReset) {
      setConfirmingReset(true);
      return;
    }
    onResetDaily();
    setConfirmingReset(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder={tCommon("search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        {hasDailyProgress && (
          <Button
            variant={confirmingReset ? "destructive" : "outline"}
            size="sm"
            className="gap-1.5 shrink-0"
            onClick={handleResetClick}
            onBlur={() => setConfirmingReset(false)}
          >
            <RotateCcw className="size-3.5" />
            {confirmingReset ? t("resetDailyConfirm") : t("resetDaily")}
          </Button>
        )}
        <Button
          onClick={onAdd}
          className="bg-indigo-600 hover:bg-indigo-700 text-white gap-1.5 shrink-0"
        >
          <Plus className="size-4" />
          {t("addChore")}
        </Button>
      </div>

      {filteredChores.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>{chores.length === 0 ? t("noChores") : tCommon("noResults")}</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredChores.map((chore) => (
            <ChoreCard
              key={chore.id}
              chore={chore}
              progress={progressMap.get(chore.id)}
              onEdit={onEdit}
              onDelete={onDelete}
              onComplete={onComplete}
              onDeactivate={onDeactivate}
              onReset={onResetChore}
            />
          ))}
        </div>
      )}
    </div>
  );
}

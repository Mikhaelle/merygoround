"use client";

import { useTranslations } from "next-intl";
import { AnimatePresence } from "framer-motion";
import { useDroppable } from "@dnd-kit/core";
import { KanbanCard } from "./kanban-card";
import type { BucketItem, BucketKind, KanbanStatus } from "@/types/bucket";

interface KanbanColumnProps {
  status: KanbanStatus;
  items: BucketItem[];
  highlightedItemId: string | null;
  inProgressLimit: { current: number; max: number };
  otherKind: BucketKind;
  onMove: (item: BucketItem, target: KanbanStatus) => void;
  onTransfer: (item: BucketItem) => void;
  onEdit: (item: BucketItem) => void;
  onDelete: (item: BucketItem) => void;
}

const COLUMN_ACCENTS: Record<KanbanStatus, string> = {
  to_do: "border-t-slate-400",
  in_progress: "border-t-indigo-500",
  blocked: "border-t-amber-500",
  done: "border-t-emerald-500",
};

/** A droppable Kanban column rendering its title, badge counter, and cards. */
export function KanbanColumn({
  status,
  items,
  highlightedItemId,
  inProgressLimit,
  otherKind,
  onMove,
  onTransfer,
  onEdit,
  onDelete,
}: KanbanColumnProps) {
  const t = useTranslations("bucket");
  const { setNodeRef, isOver } = useDroppable({ id: status });

  const isOverLimit =
    status === "in_progress" && inProgressLimit.current > inProgressLimit.max;

  function isMoveDisabled(target: KanbanStatus): boolean {
    if (target !== "in_progress") return false;
    return inProgressLimit.current >= inProgressLimit.max;
  }

  return (
    <section
      ref={setNodeRef}
      className={
        "flex min-h-[300px] flex-col rounded-xl border bg-muted/30 p-3 border-t-4 transition-colors " +
        COLUMN_ACCENTS[status] +
        (isOver
          ? " bg-indigo-50/60 border-indigo-300 dark:bg-indigo-950/30 dark:border-indigo-700"
          : " border-border")
      }
      aria-label={t(`column.${status}`)}
    >
      <header className="flex items-center justify-between gap-2 px-1 pb-3">
        <h2 className="font-semibold text-sm text-foreground">{t(`column.${status}`)}</h2>
        <div className="flex items-center gap-1.5">
          {status === "in_progress" && (
            <span
              className={
                "text-[10px] font-mono px-1.5 py-0.5 rounded-md " +
                (isOverLimit
                  ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400"
                  : "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-400")
              }
            >
              {inProgressLimit.current}/{inProgressLimit.max}
            </span>
          )}
          <span className="text-xs text-muted-foreground bg-background px-1.5 py-0.5 rounded-md">
            {items.length}
          </span>
        </div>
      </header>

      <div className="flex flex-col gap-2 flex-1">
        <AnimatePresence>
          {items.length === 0 ? (
            <p className="text-xs text-muted-foreground italic px-1 py-4">
              {t(`emptyColumn.${status}`)}
            </p>
          ) : (
            items.map((item) => (
              <KanbanCard
                key={item.id}
                item={item}
                isHighlighted={item.id === highlightedItemId}
                isMoveDisabled={isMoveDisabled}
                otherKind={otherKind}
                onMove={onMove}
                onTransfer={onTransfer}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

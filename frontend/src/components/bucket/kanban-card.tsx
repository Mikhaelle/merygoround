"use client";

import { useTranslations } from "next-intl";
import { useDraggable } from "@dnd-kit/core";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ArrowLeftRight,
  GripVertical,
  MoreHorizontal,
  Pencil,
  Trash2,
  Sparkles,
} from "lucide-react";
import { motion } from "framer-motion";
import type { BucketItem, BucketKind, KanbanStatus } from "@/types/bucket";
import { KANBAN_COLUMNS } from "@/types/bucket";

interface KanbanCardProps {
  item: BucketItem;
  isHighlighted: boolean;
  isMoveDisabled: (target: KanbanStatus) => boolean;
  otherKind: BucketKind;
  onMove: (item: BucketItem, target: KanbanStatus) => void;
  onTransfer: (item: BucketItem) => void;
  onEdit: (item: BucketItem) => void;
  onDelete: (item: BucketItem) => void;
  /** When true the card is rendered without DnD bindings (for the drag overlay). */
  isOverlay?: boolean;
}

/** A draggable Kanban card with move/edit/delete actions. */
export function KanbanCard({
  item,
  isHighlighted,
  isMoveDisabled,
  otherKind,
  onMove,
  onTransfer,
  onEdit,
  onDelete,
  isOverlay = false,
}: KanbanCardProps) {
  const t = useTranslations("bucket");
  const { setNodeRef, attributes, listeners, isDragging } = useDraggable({
    id: item.id,
    disabled: isOverlay,
  });

  return (
    <motion.div
      ref={isOverlay ? undefined : setNodeRef}
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: isDragging ? 0.4 : 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
    >
      <Card
        className={
          "group transition-all " +
          (isHighlighted
            ? "border-2 border-fuchsia-400 shadow-lg shadow-fuchsia-200/40 dark:border-fuchsia-500 dark:shadow-fuchsia-900/30"
            : "hover:shadow-md hover:border-purple-200 dark:hover:border-purple-800")
        }
      >
        <CardContent className="p-3 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <button
              type="button"
              className="text-muted-foreground hover:text-foreground cursor-grab active:cursor-grabbing touch-none mt-0.5"
              aria-label={t("dragHandle")}
              {...attributes}
              {...listeners}
            >
              <GripVertical className="size-3.5" />
            </button>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                {isHighlighted && (
                  <Sparkles className="size-3.5 text-fuchsia-500 shrink-0" />
                )}
                <h3 className="font-semibold text-foreground text-sm truncate">{item.name}</h3>
              </div>
              {item.description && (
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {item.description}
                </p>
              )}
              {item.category && (
                <Badge variant="secondary" className="mt-2 text-[10px]">
                  {item.category}
                </Badge>
              )}
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger
                render={<Button variant="ghost" size="icon-sm" aria-label={t("actions")} />}
              >
                <MoreHorizontal className="size-3.5" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {KANBAN_COLUMNS.filter((c) => c !== item.status).map((target) => (
                  <DropdownMenuItem
                    key={target}
                    disabled={isMoveDisabled(target)}
                    onClick={() => onMove(item, target)}
                  >
                    {t(`moveTo.${target}`)}
                  </DropdownMenuItem>
                ))}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onTransfer(item)}>
                  <ArrowLeftRight className="size-3.5" />
                  {t(`transferTo.${otherKind}`)}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onEdit(item)}>
                  <Pencil className="size-3.5" />
                  {t("editItem")}
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => onDelete(item)}
                >
                  <Trash2 className="size-3.5" />
                  {t("deleteItem")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

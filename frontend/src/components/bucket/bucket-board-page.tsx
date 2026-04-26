"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useBucket } from "@/lib/hooks/use-bucket";
import { KanbanBoard } from "@/components/bucket/kanban-board";
import { BucketItemForm } from "@/components/bucket/bucket-item-form";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Plus, Sparkles } from "lucide-react";
import type {
  BucketItem,
  BucketKind,
  CreateBucketItemRequest,
  KanbanStatus,
} from "@/types/bucket";

const HIGHLIGHT_TIMEOUT_MS = 6000;

interface BucketBoardPageProps {
  /** Board kind: "adult" or "happy". */
  kind: BucketKind;
  /** i18n namespace key for the page title (e.g. "bucket" or "happyBucket"). */
  titleNamespace: "bucket" | "happyBucket";
}

/** Generic Kanban page rendered for a specific bucket kind. */
export function BucketBoardPage({ kind, titleNamespace }: BucketBoardPageProps) {
  const t = useTranslations("bucket");
  const tTitle = useTranslations(titleNamespace);
  const tCommon = useTranslations("common");
  const {
    items,
    settings,
    isLoading,
    createItem,
    updateItem,
    deleteItem,
    moveItem,
    drawSuggestion,
  } = useBucket(kind);

  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<BucketItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<BucketItem | null>(null);
  const [highlightedItemId, setHighlightedItemId] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  const inProgressCount = useMemo(
    () => items.filter((item) => item.status === "in_progress").length,
    [items],
  );
  const drawDisabled =
    isDrawing ||
    inProgressCount >= settings.max_in_progress ||
    items.filter((item) => item.status === "to_do").length === 0;

  useEffect(() => {
    if (!highlightedItemId) return;
    const handle = setTimeout(() => setHighlightedItemId(null), HIGHLIGHT_TIMEOUT_MS);
    return () => clearTimeout(handle);
  }, [highlightedItemId]);

  const handleAdd = useCallback(() => {
    setEditingItem(null);
    setFormOpen(true);
  }, []);

  const handleEdit = useCallback((item: BucketItem) => {
    setEditingItem(item);
    setFormOpen(true);
  }, []);

  const handleSubmit = useCallback(
    async (data: CreateBucketItemRequest) => {
      try {
        if (editingItem) {
          await updateItem(editingItem.id, data);
          toast.success(t("itemUpdated"));
        } else {
          await createItem(data);
          toast.success(t("itemCreated"));
        }
        setFormOpen(false);
        setEditingItem(null);
      } catch {
        toast.error(tCommon("error"));
      }
    },
    [editingItem, createItem, updateItem, t, tCommon],
  );

  const handleDelete = useCallback(
    async (item: BucketItem) => {
      try {
        await deleteItem(item.id);
        toast.success(t("itemDeleted"));
        setDeleteTarget(null);
      } catch {
        toast.error(tCommon("error"));
      }
    },
    [deleteItem, t, tCommon],
  );

  const handleMove = useCallback(
    async (item: BucketItem, target: KanbanStatus) => {
      try {
        await moveItem(item.id, target);
        toast.success(t(`movedTo.${target}`));
      } catch (err) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 409) {
          toast.error(t("maxInProgressReached", { max: settings.max_in_progress }));
        } else {
          toast.error(tCommon("error"));
        }
      }
    },
    [moveItem, t, tCommon, settings.max_in_progress],
  );

  const handleDraw = useCallback(async () => {
    setIsDrawing(true);
    try {
      const suggestion = await drawSuggestion();
      setHighlightedItemId(suggestion.id);
      toast.success(t("drawHighlighted", { name: suggestion.name }));
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        toast.error(t("maxInProgressReached", { max: settings.max_in_progress }));
      } else if (status === 400) {
        toast.error(t("drawNoItems"));
      } else {
        toast.error(tCommon("error"));
      }
    } finally {
      setIsDrawing(false);
    }
  }, [drawSuggestion, t, tCommon, settings.max_in_progress]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="size-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{tTitle("title")}</h1>
          <p className="text-xs text-muted-foreground mt-1">
            {t("inProgressLabel", {
              current: inProgressCount,
              max: settings.max_in_progress,
            })}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleDraw}
            disabled={drawDisabled}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white gap-1.5"
          >
            <Sparkles className="size-4" />
            {t("draw")}
          </Button>
          <Button
            onClick={handleAdd}
            className="bg-indigo-600 hover:bg-indigo-700 text-white gap-1.5"
          >
            <Plus className="size-4" />
            {t("addItem")}
          </Button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>{t("noItems")}</p>
        </div>
      ) : (
        <KanbanBoard
          items={items}
          highlightedItemId={highlightedItemId}
          maxInProgress={settings.max_in_progress}
          onMove={handleMove}
          onEdit={handleEdit}
          onDelete={(i) => setDeleteTarget(i)}
        />
      )}

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingItem ? t("editItem") : t("addItem")}</DialogTitle>
            <DialogDescription className="sr-only">
              {editingItem ? t("editItem") : t("addItem")}
            </DialogDescription>
          </DialogHeader>
          <BucketItemForm
            item={editingItem}
            onSubmit={handleSubmit}
            onCancel={() => setFormOpen(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>{t("deleteItem")}</DialogTitle>
            <DialogDescription>{t("deleteConfirm")}</DialogDescription>
          </DialogHeader>
          <div className="flex gap-3 pt-4">
            <Button variant="outline" className="flex-1" onClick={() => setDeleteTarget(null)}>
              {tCommon("cancel")}
            </Button>
            <Button
              variant="destructive"
              className="flex-1"
              onClick={() => deleteTarget && handleDelete(deleteTarget)}
            >
              {tCommon("delete")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

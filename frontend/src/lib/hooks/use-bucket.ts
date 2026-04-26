"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  BucketItem,
  BucketKind,
  BucketSettings,
  CreateBucketItemRequest,
  KanbanStatus,
  UpdateBucketItemRequest,
} from "@/types/bucket";
import * as bucketApi from "@/lib/api/bucket";

/**
 * Manage bucket items, Kanban settings, and draw suggestions for a given board.
 * @param kind Which board to manage ("adult" or "happy").
 * @returns Items, settings, and mutation/state helpers scoped to that board.
 */
export function useBucket(kind: BucketKind) {
  const [items, setItems] = useState<BucketItem[]>([]);
  const [settings, setSettings] = useState<BucketSettings>({ max_in_progress: 2 });
  const [isLoading, setIsLoading] = useState(true);

  const fetchItems = useCallback(async () => {
    try {
      const data = await bucketApi.listItems(kind);
      setItems(data);
    } catch {
      /* ignore */
    }
  }, [kind]);

  const fetchSettings = useCallback(async () => {
    try {
      const data = await bucketApi.getSettings(kind);
      setSettings(data);
    } catch {
      /* ignore */
    }
  }, [kind]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchItems(), fetchSettings()]).finally(() => {
      if (!cancelled) setIsLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [fetchItems, fetchSettings]);

  const createItem = useCallback(
    async (data: CreateBucketItemRequest) => {
      const newItem = await bucketApi.createItem(kind, data);
      setItems((prev) => [newItem, ...prev]);
      return newItem;
    },
    [kind],
  );

  const updateItem = useCallback(
    async (id: string, data: UpdateBucketItemRequest) => {
      const updated = await bucketApi.updateItem(kind, id, data);
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
      return updated;
    },
    [kind],
  );

  const deleteItem = useCallback(
    async (id: string) => {
      await bucketApi.deleteItem(kind, id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    },
    [kind],
  );

  const moveItem = useCallback(
    async (id: string, status: KanbanStatus) => {
      const updated = await bucketApi.moveItem(kind, id, status);
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
      return updated;
    },
    [kind],
  );

  const transferItem = useCallback(
    async (id: string, target_kind: BucketKind) => {
      const updated = await bucketApi.transferItem(kind, id, target_kind);
      setItems((prev) => prev.filter((item) => item.id !== id));
      return updated;
    },
    [kind],
  );

  const drawSuggestion = useCallback(async () => {
    const result = await bucketApi.drawSuggestion(kind);
    return result.item;
  }, [kind]);

  const updateSettings = useCallback(
    async (max_in_progress: number) => {
      const updated = await bucketApi.updateSettings(kind, { max_in_progress });
      setSettings(updated);
      return updated;
    },
    [kind],
  );

  return {
    items,
    settings,
    isLoading,
    fetchItems,
    fetchSettings,
    createItem,
    updateItem,
    deleteItem,
    moveItem,
    transferItem,
    drawSuggestion,
    updateSettings,
  };
}

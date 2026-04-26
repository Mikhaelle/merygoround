"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  DragOverlay,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "./kanban-column";
import { KanbanCard } from "./kanban-card";
import type { BucketItem, BucketKind, KanbanStatus } from "@/types/bucket";
import { KANBAN_COLUMNS } from "@/types/bucket";

interface KanbanBoardProps {
  items: BucketItem[];
  highlightedItemId: string | null;
  maxInProgress: number;
  otherKind: BucketKind;
  onMove: (item: BucketItem, target: KanbanStatus) => void;
  onTransfer: (item: BucketItem) => void;
  onEdit: (item: BucketItem) => void;
  onDelete: (item: BucketItem) => void;
}

/** Kanban board with four columns and drag-and-drop support. */
export function KanbanBoard({
  items,
  highlightedItemId,
  maxInProgress,
  otherKind,
  onMove,
  onTransfer,
  onEdit,
  onDelete,
}: KanbanBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor),
  );
  const [activeItemId, setActiveItemId] = useState<string | null>(null);

  const grouped = useMemo(() => {
    const map = new Map<KanbanStatus, BucketItem[]>(
      KANBAN_COLUMNS.map((c) => [c, [] as BucketItem[]]),
    );
    for (const item of items) {
      map.get(item.status)?.push(item);
    }
    return map;
  }, [items]);

  const inProgressCount = grouped.get("in_progress")?.length ?? 0;
  const activeItem = activeItemId ? items.find((i) => i.id === activeItemId) ?? null : null;

  function handleDragStart(event: DragStartEvent) {
    setActiveItemId(String(event.active.id));
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveItemId(null);
    const { active, over } = event;
    if (!over) return;
    const target = String(over.id) as KanbanStatus;
    if (!KANBAN_COLUMNS.includes(target)) return;
    const item = items.find((i) => i.id === String(active.id));
    if (!item || item.status === target) return;
    onMove(item, target);
  }

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {KANBAN_COLUMNS.map((status) => (
          <KanbanColumn
            key={status}
            status={status}
            items={grouped.get(status) ?? []}
            highlightedItemId={highlightedItemId}
            inProgressLimit={{ current: inProgressCount, max: maxInProgress }}
            otherKind={otherKind}
            onMove={onMove}
            onTransfer={onTransfer}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>
      <DragOverlay dropAnimation={null}>
        {activeItem ? (
          <div className="rotate-2 scale-105 cursor-grabbing">
            <KanbanCard
              item={activeItem}
              isHighlighted={false}
              isMoveDisabled={() => true}
              otherKind={otherKind}
              onMove={() => {}}
              onTransfer={() => {}}
              onEdit={() => {}}
              onDelete={() => {}}
              isOverlay
            />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

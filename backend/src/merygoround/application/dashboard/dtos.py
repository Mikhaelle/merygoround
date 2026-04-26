"""Data transfer objects for the Dashboard."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

PeriodLiteral = Literal["7d", "30d", "90d", "year"]
KanbanKindLiteral = Literal["adult", "happy"]


class TodaySection(BaseModel):
    """Real-time snapshot for the current local day.

    Attributes:
        wheel: Spin counters by status, scoped to today.
        earnings_today: Sum of reward values from chores completed today (BRL).
        in_progress: Count of IN_PROGRESS items per kanban board.
        next_notification_minutes: Minutes until the next push, or None if push
            is disabled / cannot be predicted.
    """

    wheel: dict[str, int]
    earnings_today: Decimal
    in_progress: dict[KanbanKindLiteral, int]
    next_notification_minutes: int | None


class DailyPoint(BaseModel):
    """One bucket on a daily time-series chart."""

    date: date
    completed: int
    skipped: int
    deactivated: int
    pending: int


class HeatmapCell(BaseModel):
    """One cell of the weekday x hour completion heatmap."""

    weekday: int
    hour: int
    count: int


class ProductivitySection(BaseModel):
    """Spin behaviour aggregated over the requested period."""

    spins_per_day: list[DailyPoint]
    completion_rate: float
    current_streak_days: int
    longest_streak_days: int
    heatmap: list[HeatmapCell]


class KanbanColumnCounts(BaseModel):
    """Item counts per Kanban column for a single board."""

    to_do: int
    in_progress: int
    blocked: int
    done: int


class BlockedItem(BaseModel):
    """A bucket item parked in BLOCKED for too long."""

    id: str
    name: str
    kind: KanbanKindLiteral
    blocked_days: int


class ThroughputPoint(BaseModel):
    """Items moved to DONE within a single ISO week."""

    week_start: date
    adult: int
    happy: int


class KanbanSection(BaseModel):
    """Kanban-board health metrics."""

    distribution: dict[KanbanKindLiteral, KanbanColumnCounts]
    avg_lead_time_hours: dict[KanbanKindLiteral, float | None]
    blocked_aging: list[BlockedItem]
    throughput_per_week: list[ThroughputPoint]


class EarningsPoint(BaseModel):
    """Daily earnings amount."""

    date: date
    amount: Decimal


class TopChore(BaseModel):
    """A chore ranked by earnings or completions."""

    chore_name: str
    completions: int
    amount: Decimal


class CategoryCount(BaseModel):
    """Aggregation of items/spins by category label."""

    category: str
    count: int


class KindCounts(BaseModel):
    """Created / completed counters for one board kind."""

    created: int
    completed: int


class WalletSection(BaseModel):
    """Earnings + categories + adult-vs-happy breakdown for the period."""

    earnings_per_day: list[EarningsPoint]
    total: Decimal
    top_chores: list[TopChore]
    top_chore_categories: list[CategoryCount]
    top_bucket_categories: list[CategoryCount]
    adult_vs_happy: dict[KanbanKindLiteral, KindCounts]


class WeeklyOverviewPoint(BaseModel):
    """Combined chores + earnings totals for one ISO week."""

    week_start: date
    chores_completed: int
    earnings: Decimal


class DashboardResponse(BaseModel):
    """Full dashboard payload returned by GET /api/v1/dashboard."""

    period: PeriodLiteral
    today: TodaySection
    productivity: ProductivitySection
    weekly_overview: list[WeeklyOverviewPoint]
    kanban: KanbanSection
    wallet: WalletSection

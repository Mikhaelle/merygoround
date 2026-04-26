"""Dashboard read-side aggregations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import text

from merygoround.application.dashboard.dtos import (
    BlockedItem,
    CategoryCount,
    DailyPoint,
    DashboardResponse,
    EarningsPoint,
    HeatmapCell,
    KanbanColumnCounts,
    KanbanSection,
    KindCounts,
    PeriodLiteral,
    ProductivitySection,
    ThroughputPoint,
    TodaySection,
    TopChore,
    WalletSection,
    WeeklyOverviewPoint,
)
from merygoround.application.shared.use_case import BaseQuery

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


_PERIOD_DAYS: dict[PeriodLiteral, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "year": 365,
}

_BLOCKED_AGING_THRESHOLD_DAYS = 3

# spin_sessions persists uppercase values from SpinStatus.value; the dashboard
# response normalises them to lowercase keys to match the rest of the API.
_SPIN_STATUS_DB_TO_API: dict[str, str] = {
    "PENDING": "pending",
    "COMPLETED": "completed",
    "SKIPPED": "skipped",
    "DEACTIVATED": "deactivated",
}


@dataclass
class GetDashboardInput:
    """Input for GetDashboardQuery.

    Attributes:
        user_id: Authenticated user.
        period: One of 7d / 30d / 90d / year.
        tz_name: IANA timezone used to bucket "today" and per-day aggregates.
    """

    user_id: uuid.UUID
    period: PeriodLiteral
    tz_name: str


class GetDashboardQuery(BaseQuery[GetDashboardInput, DashboardResponse]):
    """Builds the full dashboard payload in one query batch.

    Args:
        session: Async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, input_data: GetDashboardInput) -> DashboardResponse:
        """Run all aggregations and return the structured response."""
        tz = ZoneInfo(input_data.tz_name)
        now_local = datetime.now(tz)
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        period_days = _PERIOD_DAYS[input_data.period]
        period_start_local = today_start_local - timedelta(days=period_days - 1)

        today = await self._build_today(input_data.user_id, today_start_local, now_local)
        productivity = await self._build_productivity(
            input_data.user_id, period_days, period_start_local, today_start_local, tz
        )
        weekly_overview = await self._build_weekly_overview(
            input_data.user_id, period_start_local
        )
        kanban = await self._build_kanban(input_data.user_id, period_start_local)
        wallet = await self._build_wallet(input_data.user_id, period_start_local, tz)

        return DashboardResponse(
            period=input_data.period,
            today=today,
            productivity=productivity,
            weekly_overview=weekly_overview,
            kanban=kanban,
            wallet=wallet,
        )

    async def _build_today(
        self,
        user_id: uuid.UUID,
        today_start_local: datetime,
        now_local: datetime,
    ) -> TodaySection:
        """Fetch the today snapshot."""
        today_start_utc = today_start_local.astimezone(UTC)

        wheel_rows = await self._session.execute(
            text(
                """
                SELECT status, COUNT(*) AS c
                FROM spin_sessions
                WHERE user_id = :uid AND spun_at >= :start
                GROUP BY status
                """
            ),
            {"uid": user_id, "start": today_start_utc},
        )
        wheel_counts: dict[str, int] = {
            "pending": 0,
            "completed": 0,
            "skipped": 0,
            "deactivated": 0,
        }
        for row in wheel_rows:
            api_key = _SPIN_STATUS_DB_TO_API.get(row.status)
            if api_key is not None:
                wheel_counts[api_key] = int(row.c)

        earnings_row = await self._session.execute(
            text(
                """
                SELECT COALESCE(SUM(c.reward_value), 0) AS total
                FROM spin_sessions s
                JOIN chores c ON c.id = s.selected_chore_id
                WHERE s.user_id = :uid
                  AND s.status = 'COMPLETED'
                  AND s.completed_at >= :start
                """
            ),
            {"uid": user_id, "start": today_start_utc},
        )
        earnings_today = Decimal(str(earnings_row.scalar_one() or 0))

        kanban_rows = await self._session.execute(
            text(
                """
                SELECT kind, COUNT(*) AS c
                FROM bucket_items
                WHERE user_id = :uid AND status = 'in_progress'
                GROUP BY kind
                """
            ),
            {"uid": user_id},
        )
        in_progress: dict[str, int] = {"adult": 0, "happy": 0}
        for row in kanban_rows:
            if row.kind in in_progress:
                in_progress[row.kind] = int(row.c)

        next_minutes = await self._compute_next_notification_minutes(user_id, now_local)

        return TodaySection(
            wheel=wheel_counts,
            earnings_today=earnings_today,
            in_progress=in_progress,  # type: ignore[arg-type]
            next_notification_minutes=next_minutes,
        )

    async def _compute_next_notification_minutes(
        self, user_id: uuid.UUID, now_local: datetime
    ) -> int | None:
        """Estimate minutes until the next push across all enabled devices.

        Returns the soonest ETA among the user's enabled push subscriptions, or
        None when no device is enabled.
        """
        row = await self._session.execute(
            text(
                """
                SELECT interval_minutes, last_notified_at
                FROM push_subscriptions
                WHERE user_id = :uid AND enabled = true
                """
            ),
            {"uid": user_id},
        )
        records = row.fetchall()
        if not records:
            return None

        soonest: int | None = None
        for record in records:
            if record.last_notified_at is None:
                eta = 0
            else:
                last_local = record.last_notified_at.astimezone(now_local.tzinfo)
                next_at = last_local + timedelta(minutes=record.interval_minutes)
                delta = next_at - now_local
                eta = max(0, int(delta.total_seconds() // 60))
            if soonest is None or eta < soonest:
                soonest = eta
        return soonest

    async def _build_productivity(
        self,
        user_id: uuid.UUID,
        period_days: int,
        period_start_local: datetime,
        today_start_local: datetime,
        tz: ZoneInfo,
    ) -> ProductivitySection:
        """Build productivity time-series, completion rate, streak and heatmap."""
        period_start_utc = period_start_local.astimezone(UTC)

        rows = await self._session.execute(
            text(
                """
                SELECT (spun_at AT TIME ZONE :tz)::date AS d, status, COUNT(*) AS c
                FROM spin_sessions
                WHERE user_id = :uid AND spun_at >= :start
                GROUP BY d, status
                ORDER BY d
                """
            ),
            {"uid": user_id, "start": period_start_utc, "tz": tz.key},
        )
        per_day: dict[date, dict[str, int]] = {}
        for row in rows:
            bucket = per_day.setdefault(
                row.d, {"completed": 0, "skipped": 0, "deactivated": 0, "pending": 0}
            )
            api_key = _SPIN_STATUS_DB_TO_API.get(row.status)
            if api_key is not None:
                bucket[api_key] = int(row.c)

        spins_per_day: list[DailyPoint] = []
        for offset in range(period_days):
            d = (period_start_local + timedelta(days=offset)).date()
            counts = per_day.get(d, {"completed": 0, "skipped": 0, "deactivated": 0, "pending": 0})
            spins_per_day.append(
                DailyPoint(
                    date=d,
                    completed=counts["completed"],
                    skipped=counts["skipped"],
                    deactivated=counts["deactivated"],
                    pending=counts["pending"],
                )
            )

        total = sum(p.completed + p.skipped + p.deactivated + p.pending for p in spins_per_day)
        completed_total = sum(p.completed for p in spins_per_day)
        completion_rate = (completed_total / total) if total > 0 else 0.0

        current_streak, longest_streak = await self._compute_streaks(
            user_id, today_start_local, tz
        )

        heat_rows = await self._session.execute(
            text(
                """
                SELECT EXTRACT(ISODOW FROM (spun_at AT TIME ZONE :tz))::int AS dow,
                       EXTRACT(HOUR  FROM (spun_at AT TIME ZONE :tz))::int AS hr,
                       COUNT(*) AS c
                FROM spin_sessions
                WHERE user_id = :uid
                  AND status = 'COMPLETED'
                  AND spun_at >= :start
                GROUP BY dow, hr
                """
            ),
            {"uid": user_id, "start": period_start_utc, "tz": tz.key},
        )
        heatmap = [
            HeatmapCell(weekday=int(r.dow) - 1, hour=int(r.hr), count=int(r.c))
            for r in heat_rows
        ]

        return ProductivitySection(
            spins_per_day=spins_per_day,
            completion_rate=round(completion_rate, 4),
            current_streak_days=current_streak,
            longest_streak_days=longest_streak,
            heatmap=heatmap,
        )

    async def _compute_streaks(
        self,
        user_id: uuid.UUID,
        today_start_local: datetime,
        tz: ZoneInfo,
    ) -> tuple[int, int]:
        """Compute current and longest streaks of days with at least one completion."""
        rows = await self._session.execute(
            text(
                """
                SELECT DISTINCT (spun_at AT TIME ZONE :tz)::date AS d
                FROM spin_sessions
                WHERE user_id = :uid AND status = 'COMPLETED'
                ORDER BY d DESC
                """
            ),
            {"uid": user_id, "tz": tz.key},
        )
        days = [r.d for r in rows]
        if not days:
            return 0, 0

        today_d = today_start_local.date()
        yesterday_d = today_d - timedelta(days=1)

        current = 0
        if days[0] in (today_d, yesterday_d):
            cursor = days[0]
            for d in days:
                if d == cursor:
                    current += 1
                    cursor = cursor - timedelta(days=1)
                elif d < cursor:
                    break

        longest = 0
        run = 1
        for i in range(1, len(days)):
            if days[i - 1] - days[i] == timedelta(days=1):
                run += 1
            else:
                longest = max(longest, run)
                run = 1
        longest = max(longest, run)

        return current, longest

    async def _build_weekly_overview(
        self, user_id: uuid.UUID, period_start_local: datetime
    ) -> list[WeeklyOverviewPoint]:
        """Per-ISO-week totals of completed chores and earnings."""
        period_start_utc = period_start_local.astimezone(UTC)

        rows = await self._session.execute(
            text(
                """
                SELECT date_trunc('week', s.completed_at)::date AS week_start,
                       COUNT(*) AS chores_completed,
                       COALESCE(SUM(c.reward_value), 0) AS earnings
                FROM spin_sessions s
                LEFT JOIN chores c ON c.id = s.selected_chore_id
                WHERE s.user_id = :uid
                  AND s.status = 'COMPLETED'
                  AND s.completed_at >= :start
                GROUP BY week_start
                ORDER BY week_start
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        return [
            WeeklyOverviewPoint(
                week_start=row.week_start,
                chores_completed=int(row.chores_completed),
                earnings=Decimal(str(row.earnings or 0)),
            )
            for row in rows
        ]

    async def _build_kanban(
        self, user_id: uuid.UUID, period_start_local: datetime
    ) -> KanbanSection:
        """Distribution snapshot, lead time, blocked aging, weekly throughput."""
        period_start_utc = period_start_local.astimezone(UTC)

        dist_rows = await self._session.execute(
            text(
                """
                SELECT kind, status, COUNT(*) AS c
                FROM bucket_items
                WHERE user_id = :uid
                GROUP BY kind, status
                """
            ),
            {"uid": user_id},
        )
        distribution: dict[str, dict[str, int]] = {
            "adult": {"to_do": 0, "in_progress": 0, "blocked": 0, "done": 0},
            "happy": {"to_do": 0, "in_progress": 0, "blocked": 0, "done": 0},
        }
        for row in dist_rows:
            if row.kind in distribution and row.status in distribution[row.kind]:
                distribution[row.kind][row.status] = int(row.c)

        lead_rows = await self._session.execute(
            text(
                """
                SELECT kind,
                       AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600.0) AS h
                FROM bucket_items
                WHERE user_id = :uid
                  AND status = 'done'
                  AND completed_at IS NOT NULL
                  AND completed_at >= :start
                GROUP BY kind
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        avg_lead: dict[str, float | None] = {"adult": None, "happy": None}
        for row in lead_rows:
            if row.kind in avg_lead:
                avg_lead[row.kind] = round(float(row.h), 2)

        threshold = datetime.now(UTC) - timedelta(days=_BLOCKED_AGING_THRESHOLD_DAYS)
        blocked_rows = await self._session.execute(
            text(
                """
                SELECT id, name, kind,
                       FLOOR(EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400.0)::int AS days
                FROM bucket_items
                WHERE user_id = :uid
                  AND status = 'blocked'
                  AND updated_at <= :threshold
                ORDER BY updated_at ASC
                LIMIT 10
                """
            ),
            {"uid": user_id, "threshold": threshold},
        )
        blocked_aging = [
            BlockedItem(
                id=str(r.id), name=r.name, kind=r.kind, blocked_days=int(r.days)
            )
            for r in blocked_rows
        ]

        thr_rows = await self._session.execute(
            text(
                """
                SELECT date_trunc('week', completed_at)::date AS week_start, kind, COUNT(*) AS c
                FROM bucket_items
                WHERE user_id = :uid
                  AND status = 'done'
                  AND completed_at IS NOT NULL
                  AND completed_at >= :start
                GROUP BY week_start, kind
                ORDER BY week_start
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        per_week: dict[date, dict[str, int]] = {}
        for row in thr_rows:
            bucket = per_week.setdefault(row.week_start, {"adult": 0, "happy": 0})
            if row.kind in bucket:
                bucket[row.kind] = int(row.c)
        throughput = [
            ThroughputPoint(week_start=ws, adult=v["adult"], happy=v["happy"])
            for ws, v in sorted(per_week.items())
        ]

        return KanbanSection(
            distribution={
                "adult": KanbanColumnCounts(**distribution["adult"]),  # type: ignore[arg-type]
                "happy": KanbanColumnCounts(**distribution["happy"]),  # type: ignore[arg-type]
            },
            avg_lead_time_hours=avg_lead,  # type: ignore[arg-type]
            blocked_aging=blocked_aging,
            throughput_per_week=throughput,
        )

    async def _build_wallet(
        self,
        user_id: uuid.UUID,
        period_start_local: datetime,
        tz: ZoneInfo,
    ) -> WalletSection:
        """Earnings curve, top chores, top categories, adult vs happy."""
        period_start_utc = period_start_local.astimezone(UTC)

        earn_rows = await self._session.execute(
            text(
                """
                SELECT (s.completed_at AT TIME ZONE :tz)::date AS d,
                       COALESCE(SUM(c.reward_value), 0) AS amount
                FROM spin_sessions s
                JOIN chores c ON c.id = s.selected_chore_id
                WHERE s.user_id = :uid
                  AND s.status = 'COMPLETED'
                  AND s.completed_at >= :start
                GROUP BY d
                ORDER BY d
                """
            ),
            {"uid": user_id, "start": period_start_utc, "tz": tz.key},
        )
        earnings_per_day = [
            EarningsPoint(date=row.d, amount=Decimal(str(row.amount or 0)))
            for row in earn_rows
        ]
        total = sum((p.amount for p in earnings_per_day), Decimal("0"))

        top_rows = await self._session.execute(
            text(
                """
                SELECT s.chore_name AS name,
                       COUNT(*) AS completions,
                       COALESCE(SUM(c.reward_value), 0) AS amount
                FROM spin_sessions s
                LEFT JOIN chores c ON c.id = s.selected_chore_id
                WHERE s.user_id = :uid
                  AND s.status = 'COMPLETED'
                  AND s.completed_at >= :start
                GROUP BY s.chore_name
                ORDER BY amount DESC, completions DESC
                LIMIT 5
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        top_chores = [
            TopChore(
                chore_name=row.name,
                completions=int(row.completions),
                amount=Decimal(str(row.amount or 0)),
            )
            for row in top_rows
        ]

        chore_cat_rows = await self._session.execute(
            text(
                """
                SELECT COALESCE(c.category, '-') AS category, COUNT(*) AS c
                FROM spin_sessions s
                JOIN chores c ON c.id = s.selected_chore_id
                WHERE s.user_id = :uid
                  AND s.status = 'COMPLETED'
                  AND s.completed_at >= :start
                GROUP BY category
                ORDER BY c DESC
                LIMIT 5
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        chore_categories = [
            CategoryCount(category=row.category, count=int(row.c))
            for row in chore_cat_rows
        ]

        bucket_cat_rows = await self._session.execute(
            text(
                """
                SELECT COALESCE(category, '-') AS category, COUNT(*) AS c
                FROM bucket_items
                WHERE user_id = :uid
                  AND created_at >= :start
                GROUP BY category
                ORDER BY c DESC
                LIMIT 5
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        bucket_categories = [
            CategoryCount(category=row.category, count=int(row.c))
            for row in bucket_cat_rows
        ]

        kind_rows = await self._session.execute(
            text(
                """
                SELECT kind,
                       SUM(CASE WHEN created_at >= :start THEN 1 ELSE 0 END) AS created,
                       SUM(CASE WHEN status = 'done' AND completed_at IS NOT NULL
                                AND completed_at >= :start THEN 1 ELSE 0 END) AS completed
                FROM bucket_items
                WHERE user_id = :uid
                GROUP BY kind
                """
            ),
            {"uid": user_id, "start": period_start_utc},
        )
        adult_vs_happy: dict[str, KindCounts] = {
            "adult": KindCounts(created=0, completed=0),
            "happy": KindCounts(created=0, completed=0),
        }
        for row in kind_rows:
            if row.kind in adult_vs_happy:
                adult_vs_happy[row.kind] = KindCounts(
                    created=int(row.created or 0),
                    completed=int(row.completed or 0),
                )

        return WalletSection(
            earnings_per_day=earnings_per_day,
            total=total,
            top_chores=top_chores,
            top_chore_categories=chore_categories,
            top_bucket_categories=bucket_categories,
            adult_vs_happy=adult_vs_happy,  # type: ignore[arg-type]
        )

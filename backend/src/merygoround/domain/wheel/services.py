"""Domain services for the Wheel bounded context."""

from __future__ import annotations

import random

from merygoround.domain.chores.entities import Chore
from merygoround.domain.chores.value_objects import TimeWeightRule
from merygoround.domain.wheel.exceptions import NoChoresAvailableError


class WheelSpinService:
    """Pure domain service that performs weighted random chore selection.

    Uses multiplicity and time-based weight rules to calculate effective
    weights for each chore, then performs weighted random selection.
    """

    def spin(self, chores: list[Chore], current_hour: int) -> Chore:
        """Select a chore from the list using weighted random selection.

        The effective weight for each chore is calculated as:
            multiplicity * time_weight(current_hour)

        If no time weight rule matches the current hour, a default
        weight of 1.0 is used.

        Args:
            chores: Available chores to select from.
            current_hour: Current hour of the day (0-23).

        Returns:
            The randomly selected Chore.

        Raises:
            NoChoresAvailableError: If the chores list is empty.
        """
        if not chores:
            raise NoChoresAvailableError()

        weights = [
            self._calculate_effective_weight(chore, current_hour) for chore in chores
        ]

        available = [(c, w) for c, w in zip(chores, weights) if w > 0]
        if not available:
            raise NoChoresAvailableError()

        filtered_chores, filtered_weights = zip(*available)
        selected = random.choices(list(filtered_chores), weights=list(filtered_weights), k=1)
        return selected[0]

    def get_effective_weight(self, chore: Chore, current_hour: int) -> float:
        """Calculate the effective weight for a chore at the given hour.

        Args:
            chore: The chore to calculate weight for.
            current_hour: Current hour of the day (0-23).

        Returns:
            The effective weight as a float.
        """
        return self._calculate_effective_weight(chore, current_hour)

    def _calculate_effective_weight(self, chore: Chore, current_hour: int) -> float:
        multiplicity = chore.wheel_config.multiplicity.value
        time_weight = self._get_time_weight(
            chore.wheel_config.time_weight_rules, current_hour
        )
        return multiplicity * time_weight

    def _get_time_weight(self, rules: list[TimeWeightRule], current_hour: int) -> float:
        for rule in rules:
            if rule.hour == current_hour:
                return rule.weight
        return 1.0

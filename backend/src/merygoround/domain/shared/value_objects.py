"""Shared value objects used across bounded contexts."""

from __future__ import annotations

import uuid
from typing import NewType

UserId = NewType("UserId", uuid.UUID)
ChoreId = NewType("ChoreId", uuid.UUID)
BucketItemId = NewType("BucketItemId", uuid.UUID)
SpinSessionId = NewType("SpinSessionId", uuid.UUID)
PushSubscriptionId = NewType("PushSubscriptionId", uuid.UUID)

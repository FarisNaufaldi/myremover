"""Login brute-force protection: N failures → hard lockout window."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LockoutStatus:
    locked: bool
    remaining_seconds: int = 0
    failures: int = 0


class LoginLockout:
    """
    Tracks failed login attempts per key (typically ip:username).

    After `max_failures` consecutive failures within/without window,
    the key is locked for `lockout_seconds` (default 3 hours).
    Successful login clears the counter.
    """

    def __init__(self, max_failures: int = 3, lockout_seconds: int = 3 * 60 * 60) -> None:
        self.max_failures = max(1, max_failures)
        self.lockout_seconds = max(1, lockout_seconds)
        self._failures: Dict[str, int] = {}
        self._locked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def status(self, key: str) -> LockoutStatus:
        now = time.monotonic()
        with self._lock:
            until = self._locked_until.get(key)
            if until is not None:
                if now < until:
                    return LockoutStatus(
                        locked=True,
                        remaining_seconds=int(until - now) + 1,
                        failures=self._failures.get(key, 0),
                    )
                # Lock expired
                self._locked_until.pop(key, None)
                self._failures.pop(key, None)
            return LockoutStatus(
                locked=False,
                remaining_seconds=0,
                failures=self._failures.get(key, 0),
            )

    def register_failure(self, key: str) -> LockoutStatus:
        now = time.monotonic()
        with self._lock:
            until = self._locked_until.get(key)
            if until is not None and now < until:
                return LockoutStatus(
                    locked=True,
                    remaining_seconds=int(until - now) + 1,
                    failures=self._failures.get(key, self.max_failures),
                )

            count = self._failures.get(key, 0) + 1
            self._failures[key] = count

            if count >= self.max_failures:
                self._locked_until[key] = now + self.lockout_seconds
                return LockoutStatus(
                    locked=True,
                    remaining_seconds=self.lockout_seconds,
                    failures=count,
                )

            return LockoutStatus(locked=False, remaining_seconds=0, failures=count)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)

    def remaining_attempts(self, key: str) -> Optional[int]:
        st = self.status(key)
        if st.locked:
            return 0
        return max(0, self.max_failures - st.failures)

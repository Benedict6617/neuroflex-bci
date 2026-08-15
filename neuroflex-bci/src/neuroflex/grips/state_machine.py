"""Debounced state machine for grip-pattern switching.

Prevents "flicker" between grips when decoder confidence oscillates near
threshold, by requiring a sustained majority vote over a short window
before committing to a transition. This is a usability and safety feature:
uncommanded rapid grip switching is disorienting and can be hazardous
when the hand is holding an object.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from neuroflex.grips.patterns import GripPattern


@dataclass
class GripStateMachine:
    window_size: int = 5
    min_agreement: float = 0.6
    current: GripPattern = GripPattern.REST
    _history: deque = field(default_factory=lambda: deque(maxlen=5))

    def __post_init__(self):
        self._history = deque(maxlen=self.window_size)

    def observe(self, candidate: GripPattern) -> GripPattern:
        """Feed the latest decoded grip candidate; returns the committed grip."""
        self._history.append(candidate)
        if len(self._history) < self._history.maxlen:
            return self.current

        counts: dict[GripPattern, int] = {}
        for g in self._history:
            counts[g] = counts.get(g, 0) + 1
        winner, votes = max(counts.items(), key=lambda kv: kv[1])

        if votes / len(self._history) >= self.min_agreement and winner != self.current:
            self.current = winner
        return self.current

    def force_reset(self, grip: GripPattern = GripPattern.REST) -> None:
        """Used by the safety layer to hard-reset state on interlock trip."""
        self.current = grip
        self._history.clear()

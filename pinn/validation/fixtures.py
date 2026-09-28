"""Closed-form diagnostic controls from the candidate manifest; no training."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class AnalyticFixture:
    fixture_id: str
    fundamental_amplitude: float = 1.0
    offset: float = 0.0
    mode: int = 1
    mode_amplitude: float = 0.0

    def solution(self, x: float) -> float:
        return (self.fundamental_amplitude * math.sin(math.pi * x) + self.offset
                + self.mode_amplitude * math.sin(self.mode * math.pi * x))

    def first_derivative(self, x: float) -> float:
        return (self.fundamental_amplitude * math.pi * math.cos(math.pi * x)
                + self.mode_amplitude * self.mode * math.pi * math.cos(self.mode * math.pi * x))

    def second_derivative(self, x: float) -> float:
        return (-self.fundamental_amplitude * math.pi**2 * math.sin(math.pi * x)
                - self.mode_amplitude * (self.mode * math.pi)**2 * math.sin(self.mode * math.pi * x))


FIXTURES = (
    AnalyticFixture("ANALYTIC_CONTROL"),
    AnalyticFixture("B1b", fundamental_amplitude=-1.0),
    AnalyticFixture("B3", offset=0.3),
    AnalyticFixture("B4", mode=4, mode_amplitude=0.002),
    AnalyticFixture("B6", mode=5, mode_amplitude=0.2),
    AnalyticFixture("ZERO_FIELD_CONTROL", fundamental_amplitude=0.0),
)

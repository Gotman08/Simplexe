from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Iterator

@dataclass
class Chronometre:
    debut: float = field(default_factory=perf_counter)

    def demarrer(self) -> None:
        self.debut = perf_counter()

    def ecoule(self) -> float:
        return perf_counter() - self.debut

@contextmanager
def chrono() -> Iterator[Chronometre]:
    c = Chronometre()
    yield c

import random
from typing import MutableSequence


class Rng:
    def __init__(self, *, seed: int | None = None) -> None:
        self._r = random.Random(seed)
        self.seed = seed

    def randint(self, a: int, b: int) -> int:
        return self._r.randint(a, b)

    def choice[T](self, seq: list[T]) -> T:
        return self._r.choice(seq)

    def shuffle[T](self, seq: MutableSequence[T]) -> None:
        self._r.shuffle(seq)

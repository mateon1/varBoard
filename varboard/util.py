from __future__ import annotations

from varboard.state import Square


class Vec2:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Vec2({self.x!r}, {self.y!r})"

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int) -> Vec2:
        assert isinstance(other, int)
        return Vec2(self.x * other, self.y * other)

    @staticmethod
    def from_square(sq: Square) -> Vec2:
        return Vec2(sq.file, sq.rank)

    def to_square(self) -> Square:
        return Square(rank=self.y, file=self.x)

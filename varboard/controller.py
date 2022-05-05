from __future__ import annotations

from typing import Optional, Iterable

from varboard.state import Position, GameTree, Move
from varboard.variant import Variant


class GameController:
    def __init__(self, variant: Variant, pos: Optional[Position]):
        self.variant = variant
        self.tree = GameTree(variant.startpos() if pos is None else pos)
        self.current = self.tree
        self.curmoves: list[Move] = []

    def root(self) -> None:
        self.current = self.tree
        self.curmoves.clear()

    def moves(self, moves: Iterable[Move]) -> None:
        for m in moves:
            self.move(m)

    def move(self, move: Move) -> None:
        if move not in self.current.next_moves:
            newpos, _ = self.variant.execute_move(self.current.pos, move)
            # TODO: Shove actions to GUI
            self.current.add_move(move, newpos)
        self.current = self.current.next_moves[move]
        self.curmoves.append(move)

    def move_back(self) -> None:
        self.curmoves.pop()
        moves = self.curmoves.copy()
        self.root()
        self.moves(moves)

    def legal_moves(self) -> Iterator[Move]:
        return self.variant.legal_moves(self.current.pos)

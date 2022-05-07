from __future__ import annotations

from typing import Optional, Iterable, Iterator, Dict, Any

from .state import Position, Move, BoardAction, GameEndValue
from .variant import Variant


class GameTree:
    def __init__(self, current: Position):
        self.pos = current
        self.next_moves: Dict[Move, GameTree] = {}
        self.extra: Dict[str, Any] = {}
        self.pv_move: Optional[Move] = None

    def add_move(self, move: Move, to: Position) -> None:
        self.next_moves[move] = GameTree(to)
        if self.pv_move is None:
            self.pv_move = move

    def set_pv_move(self, move: Move) -> None:
        self.pv_move = move

    def set_extra(self, prop: str, data: Any) -> None:
        self.extra[prop] = data

    def get_extra(self, prop: str) -> Any:
        return self.extra.get(prop)


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

    def move(self, move: Move) -> tuple[list[BoardAction], Optional[GameEndValue]]:
        newpos, actions = self.variant.execute_move(self.current.pos, move)
        if move not in self.current.next_moves:
            self.current.add_move(move, newpos)
        self.current = self.current.next_moves[move]
        self.curmoves.append(move)
        return actions, self.variant.game_value(self.tree.pos, self.curmoves)

    def move_back(self) -> None:
        self.curmoves.pop()
        moves = self.curmoves.copy()
        self.root()
        self.moves(moves)

    def legal_moves(self) -> Iterator[Move]:
        return self.variant.legal_moves(self.current.pos)

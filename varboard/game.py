from __future__ import annotations
from typing import Optional


class Square:
    FILES = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self, rank: int, file: int):
        self.rank = rank
        self.file = file

    @staticmethod
    def from_algebraic(s: str) -> Square:
        file = Square.FILES.index(s[0].lower())
        rank = int(s[1:]) - 1
        return Square(rank, file)

    @staticmethod
    def from_tuple(s: (int, int)) -> Square:
        return Square(rank=s[1], file=s[0])

    def __repr__(self):
        return "Square(rank=%d, file=%d)" % (self.rank, self.file)

    def __str__(self):
        return Square.FILES[self.file] + str(self.rank + 1)

    def to_tuple(self) -> (int, int):
        return (self.file, self.rank)


class PositionBuilder:
    def __init__(self, size: (int, int) = (8, 8), ply: int = 0):
        w, h = size
        self.board = [[None for x in range(w)] for y in range(h)]
        self.ply = ply
        self.extra = {}

    def ply(self, ply: int) -> PositionBuilder:
        assert ply >= 0
        self.ply = ply
        return self

    def piece(self, pos: Square, piece: Optional[str]) -> PositionBuilder:
        """
        Sets a piece at a given coordinate in this position
        """
        self.board[pos.rank][pos.file] = piece
        return self

    def extra(self, prop: str, data) -> PositionBuilder:
        """
        Sets a piece of arbitrary data for this position, used for things like the 50-move timer, pieces in hand, en passant, etc.
        The data must be of an immutable and hashable type.
        """
        assert hash(data)
        self.extra[prop] = data
        return self

    def build(self) -> Position:
        return Position(self)


class Position:
    """
    This class is an immutable representation of a chess (variant) position.
    The "extra" attribute is intentionally extremely generic to support many possible use-cases.
    """

    def __init__(self, builder: PositionBuilder):
        self.board = tuple(tuple(row) for row in builder.board)
        self.ply = builder.ply
        # Python does NOT have a frozendict(), and the PEP (416) got rejected
        self.extra = frozenset(builder.extra.items())
        self._hash = None

    def __hash__(self):
        if self._hash is not None:
            return self._hash
        h = (976153908764132 | 1) * hash(self.extra)
        h += (1072346802467642 | 1) * hash(self.board)
        h += (7428098251633488 | 1) * hash(self.ply)
        self._hash = hash(h)
        return self._hash

    def get_piece(self, pos: Square) -> Optional[str]:
        return self.board[pos.rank][pos.file]

    def get_extra(self, prop: str):
        for k, v in self.extra:
            if k == prop: return v
        else:
            return None

    def extra_iter(self):
        return iter(self.extra)


class Move:
    """
    This class represents any chess move in any variant.
    If all parameters are None, it represents the Null move
    If fromsq == None, tosq != None and intopiece != None, it represents a piece drop
    If fromsq != None, tosq == None, it represents removing a piece from the board
    If fromsq != None, tosq != None and intopiece != None, represents a piece promotion
    Otherwise, if fromsq != None, tosq != None, represents a normal move
    """

    def __init__(self, fromsq: Optional[Square] = None, tosq: Optional[Square] = None, intopiece: Optional[str] = None):
        assert tosq is not None, "Removing pieces not yet supported"
        self.fromsq = fromsq
        self.tosq = tosq
        self.intopiece = intopiece

    @staticmethod
    def move(fromsq: Square, tosq: Square):
        return Move(fromsq, tosq)

    @staticmethod
    def move_promote(fromsq: Square, tosq: Square, intopiece: str):
        return Move(fromsq, tosq, intopiece)

    @staticmethod
    def drop_at(tosq: Square, piece: str):
        return Move(None, tosq, piece)

    def __str__(self):
        if self.fromsq is None:
            return "@@@@" if self.tosq is None else "{}@{}".format(self.intopiece, self.tosq)
        elif self.tosq is not None:
            return "{}{}{}".format(self.fromsq, self.tosq, self.intopiece or "")
        else:
            assert False, "unimplemented"


class GameTree:
    def __init__(self, current: Position):
        self.current = current
        # dict[Move] -> Position
        self.next_moves = {}
        self.extra = {}

    def add_move(self, move: Move, to: Position):
        self.next_moves[move].append(GameTree(to))
        if self.pv_move is None:
            self.pv_move = move

    def set_pv_move(self, move: Move):
        self.pv_move = move

    def set_extra(self, prop: str, data):
        self.extra[prop] = data

    def get_extra(self, prop: str):
        return self.extra.get(prop)

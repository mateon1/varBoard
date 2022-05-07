from __future__ import annotations

import enum
from typing import Optional, Union, Tuple, List, Dict, Iterator, Any


class Square:
    FILES = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self, rank: int, file: int):
        self.rank = rank
        self.file = file

    def offset(self, x: int, y: int) -> Square:
        return Square(self.rank + y, self.file + x)

    @staticmethod
    def from_algebraic(s: str) -> Square:
        file = Square.FILES.index(s[0].lower())
        rank = int(s[1:]) - 1
        return Square(rank, file)

    @staticmethod
    def from_tuple(s: Tuple[int, int]) -> Square:
        return Square(rank=s[1], file=s[0])

    def __repr__(self) -> str:
        return "Square(rank=%d, file=%d)" % (self.rank, self.file)

    def __str__(self) -> str:
        return Square.FILES[self.file] + str(self.rank + 1)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Square) and self.rank == other.rank and self.file == other.file

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def to_tuple(self) -> Tuple[int, int]:
        return (self.file, self.rank)


class Color(enum.Enum):
    BLACK = "b"
    WHITE = "w"

    @staticmethod
    def from_ply(ply: int) -> Color:
        return Color.WHITE if ply % 2 == 0 else Color.BLACK

    def __invert__(self) -> Color:
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class GameEndValue(enum.Enum):
    WHITE_WIN = 1
    BLACK_WIN = -1
    DRAW = 0

    @staticmethod
    def win_for(color: Color) -> GameEndValue:
        return GameEndValue(1 if color == Color.WHITE else -1)


class Piece:
    def __init__(self, piecetype: str, color: Color):
        self.ty = piecetype.upper()
        self.color = color
        assert self.ty != self.ty.lower()

    def __hash__(self) -> int:
        return hash(self.ty) * 1000000007 + hash(self.color) * 9876543211

    def __str__(self) -> str:
        return self.ty.upper() if self.color == Color.WHITE else self.ty.lower()

    def __repr__(self) -> str:
        return f"Piece({self.ty!r}, {self.color})"


# Types for position extras
HandType = tuple[tuple[Piece, ...], tuple[Piece, ...]]
TimerType = Union[int, tuple[int, int]]
TimeIncType = Union[int, tuple[int, int]]


class PositionBuilder:
    def __init__(self, size: Tuple[int, int] = (8, 8), ply: int = 0):
        w, h = size
        self.board: List[List[Optional[Piece]]] = [[None for x in range(w)] for y in range(h)]
        self._ply = ply
        self._extra: Dict[str, Any] = {}

    @staticmethod
    def from_position(pos: Position) -> PositionBuilder:
        bld = PositionBuilder((0, 0), pos.ply)
        bld.board = [list(row) for row in pos.board]
        for k, v in pos.extra:
            bld.extra(k, v)
        return bld

    def ply(self, ply: int) -> PositionBuilder:
        assert ply >= 0
        self._ply = ply
        return self

    def piece(self, pos: Square, piece: Optional[Piece]) -> PositionBuilder:
        """
        Sets a piece at a given coordinate in this position
        """
        self.board[pos.rank][pos.file] = piece
        return self

    def extra(self, prop: str, data: Any) -> PositionBuilder:
        """
        Sets a piece of arbitrary data for this position, used for things like the 50-move timer, pieces in hand, en passant, etc.
        The data must be of an immutable and hashable type.
        """
        _ = hash(data)
        self._extra[prop] = data
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
        self.ply = builder._ply
        # Python does NOT have a frozendict(), and the PEP (416) got rejected
        self.extra = frozenset(builder._extra.items())
        self._hash: Optional[int] = None

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash
        h = (976153908764132 | 1) * hash(self.extra)
        h += (1072346802467642 | 1) * hash(self.board)
        h += (7428098251633488 | 1) * hash(self.ply)
        self._hash = hash(h)
        return self._hash

    def __str__(self) -> str:
        return "\n".join("".join(str(p) if p is not None else " " for p in r) for r in self.board[::-1])

    def __repr__(self) -> str:
        return str(self)

    def bounds(self) -> Tuple[int, int]:
        return (len(self.board[0]), len(self.board))

    def inbounds(self, sq: Square) -> bool:
        return 0 <= sq.rank < len(self.board) and 0 <= sq.file < len(self.board[0])

    def get_piece(self, sq: Square) -> Optional[Piece]:
        return self.board[sq.rank][sq.file]

    def get_extra(self, prop: str) -> Optional[Any]:
        for k, v in self.extra:
            if k == prop: return v
        else:
            return None

    def extra_iter(self) -> Iterator[Any]:
        return iter(self.extra)

    def squares_iter(self) -> Iterator[Tuple[Square, Optional[Piece]]]:
        for rank in range(len(self.board)):
            for file in range(len(self.board[rank])):
                yield (Square(rank, file), self.board[rank][file])

    def pieces_iter(self, color: Optional[Color] = None) -> Iterator[Tuple[Square, Piece]]:
        for rank, row in enumerate(self.board):
            for file, p in enumerate(row):
                if p is not None and (color is None or p.color == color):
                    yield (Square(rank, file), p)


class BoardAction:
    """
    Helper class, distinct from Move, that represents how board state is changed, irrespective of variant.
    """

    def __init__(self, tosq: Square, fromsq_or_piece: Union[Square, Piece, None]):
        self.fromsq: Optional[Square] = None
        self.piece: Optional[Piece] = None
        self.tosq = tosq
        if isinstance(fromsq_or_piece, Square):
            self.fromsq = fromsq_or_piece
        else:
            self.piece = fromsq_or_piece

    def __repr__(self) -> str:
        return f"{self.fromsq or self.piece}->{self.tosq}"


class Move:
    """
    This class represents any chess move in any variant.
    If all parameters are None, it represents the Null move
    If fromsq == None, tosq != None and intopiece != None, it represents a piece drop
    If fromsq != None, tosq == None, it represents removing a piece from the board
    If fromsq != None, tosq != None and intopiece != None, represents a piece promotion
    Otherwise, if fromsq != None, tosq != None, represents a normal move

    Variants may interpret this differently.
    """

    def __init__(self, fromsq: Optional[Square] = None, tosq: Optional[Square] = None,
                 intopiece: Optional[Piece] = None):
        assert tosq is not None, "Removing pieces not yet supported"
        if fromsq is None and tosq is not None:
            assert intopiece is not None, "Piece drop must have a piece type"
        self.fromsq = fromsq
        self.tosq = tosq
        self.intopiece = intopiece

    @staticmethod
    def move(fromsq_raw: Union[Square, str], tosq_raw: Union[Square, str]) -> Move:
        fromsq = fromsq_raw if isinstance(fromsq_raw, Square) else Square.from_algebraic(fromsq_raw)
        tosq = tosq_raw if isinstance(tosq_raw, Square) else Square.from_algebraic(tosq_raw)
        return Move(fromsq, tosq)

    @staticmethod
    def move_promote(fromsq_raw: Union[Square, str], tosq_raw: Union[Square, str], intopiece: Piece) -> Move:
        fromsq = fromsq_raw if isinstance(fromsq_raw, Square) else Square.from_algebraic(fromsq_raw)
        tosq = tosq_raw if isinstance(tosq_raw, Square) else Square.from_algebraic(tosq_raw)
        return Move(fromsq, tosq, intopiece)

    @staticmethod
    def drop_at(tosq_raw: Union[Square, str], piece: Piece) -> Move:
        tosq = tosq_raw if isinstance(tosq_raw, Square) else Square.from_algebraic(tosq_raw)
        return Move(None, tosq, piece)

    def __str__(self) -> str:
        if self.fromsq is None:
            if self.tosq is None:
                return "@@@@"
            if self.intopiece is not None:
                return "{}@{}".format(self.intopiece.ty, self.tosq)
            assert False, "Impossible case: piece drop without piece"
        elif self.tosq is not None:
            return "{}{}{}".format(self.fromsq, self.tosq, self.intopiece or "")
        else:
            assert False, "unimplemented"

    def __repr__(self) -> str:
        if self.fromsq is None and self.tosq is not None and self.intopiece is not None:
            return f"Move.drop_at({str(self.tosq)!r}, {self.intopiece!r})"
        if self.fromsq is not None and self.tosq is not None:
            if self.intopiece is not None:
                return f"Move.move_promote({str(self.fromsq)!r}, {str(self.tosq)!r}, {self.intopiece!r})"
            else:
                return f"Move.move({str(self.fromsq)!r}, {str(self.tosq)!r})"
        fromsq = str(self.fromsq) if self.fromsq is not None else None
        tosq = str(self.tosq) if self.tosq is not None else None
        intopiece = self.intopiece
        return f"Move({fromsq = !r}, {tosq = !r}, {intopiece = !r})"

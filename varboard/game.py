# from __future__ import annotations
from typing import Optional


class Position:
    pass


class Square:
    FILES = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self, rank: int, file: int):
        self.rank = rank
        self.file = file

    @staticmethod
    def from_algebraic(s: str) -> "Square":
        file = Square.FILES.index(s[0].lower())
        rank = int(s[1:])
        return Square(rank, file)

    def __repr__(self):
        return "Square(rank=%d, file=%d)" % (self.rank, self.file)

    def __str__(self):
        return Square.FILES[self.file] + str(self.rank)


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
        self.fromsq = fromsq
        self.tosq = tosq
        self.intopiece = intopiece

    def __str__(self):
        if self.fromsq is None:
            return "@@@@" if self.tosq is None else "{}@{}".format(self.intopiece, self.tosq)
        elif self.tosq is not None:
            return "{}{}{}".format(self.fromsq, self.tosq, self.intopiece or "")
        else:
            assert False, "unimplemented"


class BoardState:
    def __init__(self, initial: Position):
        self.initial = initial
        self.current = initial
        self.current_moves = []
        self.move_tree = {}

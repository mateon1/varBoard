from __future__ import annotations
from typing import Iterator, Optional
import enum
from .state import PositionBuilder, Position, Square, Move, Piece, Color, HandType
from .util import Vec2


class GameEndValue(enum.Enum):
    WHITE_WIN = 1
    BLACK_WIN = -1
    DRAW = 0

    @staticmethod
    def win_for(color: Color) -> GameEndValue:
        return GameEndValue(1 if color == Color.WHITE else -1)


class Variant:
    """
    This class is the base class for each game variant.
    A variant needs to implement a few methods necessary to implement the game, such as providing legal moves and deciding whether a game position is won or not.
    """

    def startpos(self) -> Position:
        raise TypeError("Called startpos on Variant base type")

    def is_pos_ended(self, pos: Position) -> bool:
        raise TypeError("Called is_pos_ended on Variant base type")

    def game_value(self, startpos: Position, moves: Iterator[Move]) -> Optional[GameEndValue]:
        pos = startpos
        for m in moves:
            pos = self.execute_move(pos, m)
        if not self.is_pos_ended(pos):
            return None
        return self.pos_value(pos)

    def pos_value(self, pos: Position) -> GameEndValue:
        raise TypeError("Called pos_value on Variant base type")

    def legal_moves(self, pos: Position) -> Iterator[Move]:
        raise TypeError("Called legal_moves on Variant base type")

    def is_legal(self, pos: Position, move: Move) -> bool:
        for m in self.legal_moves(pos):
            if m == move: return True
        return False

    def execute_move(self, pos: Position, move: Move) -> Position:
        """
        Generic move implementation, this is okay for a lot of moves, but may be wrong if moves have extra effects, like castling, setting en-passant state, etc.
        """
        assert self.is_legal(pos, move)
        nextpos = PositionBuilder.from_position(pos)
        nextpos.ply(pos.ply + 1)
        color = Color.from_ply(pos.ply)

        if move.fromsq is None and move.intopiece is not None:
            hand: Optional[HandType] = pos.get_extra("hand")
            # If we're tracking pieces held in hand, remove the one we just dropped
            if hand is not None:
                whand, bhand = hand
                if color == Color.WHITE:
                    idx = whand.index(move.intopiece)
                    whand = whand[:idx] + whand[idx + 1:]
                else:
                    idx = bhand.index(move.intopiece)
                    bhand = bhand[:idx] + bhand[idx + 1:]
                hand = whand, bhand
                nextpos.extra("hand", hand)

        if move.fromsq is not None:
            nextpos.piece(move.fromsq, None)

        if move.tosq is not None:
            if move.fromsq is None:
                nextpos.piece(move.tosq, move.intopiece)
            else:
                nextpos.piece(move.tosq, move.intopiece or pos.get_piece(move.fromsq))

        return nextpos.build()

    def piece_legal_moves(self, pos: Position, fromsq: Square) -> Iterator[Move]:
        for move in self.legal_moves(pos):
            if move.fromsq == fromsq:
                yield move

    def legal_drops(self, pos: Position, piecetype: Optional[Piece] = None) -> Iterator[Move]:
        for move in self.legal_moves(pos):
            if move.fromsq == None and (piecetype is None or piecetype == move.intopiece):
                yield move


class TicTacToe(Variant):
    @staticmethod
    def lines(pos: Position) -> Iterator[list[Optional[Piece]]]:
        size = len(pos.board)
        assert len(pos.board[0]) == size, "Square boards only"
        for row in pos.board:
            yield list(row)
        for col in range(size):
            yield [row[col] for row in pos.board]
        yield [pos.board[i][i] for i in range(size)]
        yield [pos.board[i][~i] for i in range(size)]

    def startpos(self) -> Position:
        return PositionBuilder((3, 3), 0).build()

    def is_pos_ended(self, pos: Position) -> bool:
        if all(p is not None for sq, p in pos.squares_iter()):
            return True
        for line in self.lines(pos):
            if any(p is None for p in line):
                continue
            colors = [p.color for p in line if p is not None]
            if len(set(colors)) == 1:
                return True
        return False

    def pos_value(self, pos: Position) -> GameEndValue:
        for line in self.lines(pos):
            if any(p is None for p in line):
                continue
            colors = [p.color for p in line if p is not None]
            if len(set(colors)) == 1:
                return GameEndValue.win_for(colors[0])
        return GameEndValue.DRAW

    def legal_moves(self, pos: Position) -> Iterator[Move]:
        color = Color.from_ply(pos.ply)
        piece = Piece("P", color)
        for sq, p in pos.squares_iter():
            if p is None:
                yield Move.drop_at(sq, piece)


class Chess(Variant):
    CASTLE_SHORT = 1
    CASTLE_LONG = 2

    def startpos(self) -> Position:
        b = PositionBuilder((8, 8), 0)
        for x, p in enumerate("RNBQKBNR"):
            b.piece(Square(file=x, rank=0), Piece(p, Color.WHITE))
            b.piece(Square(file=x, rank=7), Piece(p, Color.BLACK))
            b.piece(Square(file=x, rank=1), Piece("P", Color.WHITE))
            b.piece(Square(file=x, rank=6), Piece("P", Color.BLACK))
        b.extra("castle", (3, 3))
        b.extra("ep", None)
        return b.build()

    def can_move(self, piece: Piece, like: str):
        assert like.upper() == like
        if like in "PNKQ":
            return piece.ty == like
        if like == "B":
            return piece.ty in "QB"
        if like == "R":
            return piece.ty in "QR"
        raise ValueError(f"Don't know whether {piece.ty} moves like {like}")

    def target_squares(self, pos: Position, square: Square) -> Iterator[Square]:
        piece = pos.get_piece(square)
        if piece is None: return
        my = piece.color
        relrank = pos.bounds()[1] - 1 - square.rank if my == Color.BLACK else square.rank
        forward = Vec2(0, 1 if my == Color.WHITE else -1)
        left = Vec2(-1, 0)
        right = Vec2(1, 0)

        sqvec = Vec2.from_square(square)

        if self.can_move(piece, "P"):
            up = sqvec + forward
            assert pos.inbounds(up.to_square())
            if pos.get_piece(up.to_square()) is None:
                yield up.to_square()
                _, height = pos.bounds()
                if relrank == 1 and pos.get_piece((up + forward).to_square()) is None:
                    yield (up + forward).to_square()
            for v in {up + left, up + right}:  # TODO: en passant
                sq = v.to_square()
                if pos.inbounds(sq):
                    p = pos.get_piece(sq)
                    if p is not None and p.color == ~my:
                        yield sq
                    elif pos.get_extra("ep") == sq:
                        yield sq
        if self.can_move(piece, "N"):
            for m in range(8):
                x, y = 1, 2
                if m & 1: x, y = y, x
                if m & 2: x = -x
                if m & 4: y = -y
                sq = (sqvec + Vec2(x, y)).to_square()
                if pos.inbounds(sq):
                    p = pos.get_piece(sq)
                    if p is None or p.color == ~my:
                        yield sq
        if self.can_move(piece, "K"):
            for x in {-1, 0, 1}:
                for y in {-1, 0, 1}:
                    sq = (sqvec + Vec2(x, y)).to_square()
                    if not pos.inbounds(sq): continue
                    p = pos.get_piece(sq)
                    if p is None or p.color == ~my:
                        yield sq
            # NOTE: Castling cannot capture pieces, handle separately when generating legal moves
        rays = []
        if self.can_move(piece, "B"):
            for y in {-1, 1}:
                for x in {-1, 1}:
                    rays.append(Vec2(x, y))
        if self.can_move(piece, "R"):
            for y in {-1, 1}: rays.append(Vec2(0, y))
            for x in {-1, 1}: rays.append(Vec2(x, 0))
        for ray in rays:
            cur = sqvec
            while True:
                cur += ray
                cursq = cur.to_square()
                if not pos.inbounds(cursq): break
                p = pos.get_piece(cursq)
                if p is None:
                    yield cursq
                else:
                    if p.color == ~my:
                        yield cursq
                    break

    def is_pos_ended(self, pos: Position) -> bool:
        raise TypeError("Called is_pos_ended on Variant base type")

    def game_value(self, startpos: Position, moves: Iterator[Move]) -> Optional[GameEndValue]:
        # TODO: Check 50mr,
        # TODO: Check 3fr,
        pos = startpos
        for m in moves:
            pos = self.execute_move(pos, m)
        if not self.is_pos_ended(pos):
            return None
        return self.pos_value(pos)

    def pos_value(self, pos: Position) -> GameEndValue:
        raise TypeError("Called pos_value on Variant base type")

    def legal_moves(self, pos: Position) -> Iterator[Move]:
        raise TypeError("Called legal_moves on Variant base type")

    def execute_move(self, pos: Position, move: Move) -> Position:
        ...
        # TODO: handle castling
        # TODO: handle e.p.
        # TODO: handle check

    def piece_legal_moves(self, pos: Position, fromsq: Square) -> Iterator[Move]:
        for move in self.legal_moves(pos):
            if move.fromsq == fromsq:
                yield move

    def legal_drops(self, pos: Position, piecetype: Optional[Piece] = None) -> Iterator[Move]:
        for move in self.legal_moves(pos):
            if move.fromsq == None and (piecetype is None or piecetype == move.intopiece):
                yield move

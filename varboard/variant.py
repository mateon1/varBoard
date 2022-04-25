from __future__ import annotations
from typing import Iterator, Optional
import enum
from .state import PositionBuilder, Position, Square, BoardAction, Move, Piece, Color, HandType


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

    def _is_pos_ended(self, pos: Position) -> bool:
        """
        Internal, abstract function. Implement on a variant to use the default game_value implementation.
        Do not rely on this externally.
        """
        raise TypeError("Called _is_pos_ended on Variant base type")

    def _pos_value(self, pos: Position) -> GameEndValue:
        """
        Internal, abstract function. Implement on a variant to use the default game_value implementation.
        Do not rely on this externally.
        """
        raise TypeError("Called _pos_value on Variant base type")

    def startpos(self) -> Position:
        """
        Returns the starting position for this variant.
        """
        raise TypeError("Called startpos on Variant base type")

    def game_value(self, startpos: Position, moves: Iterator[Move]) -> Optional[GameEndValue]:
        """
        Calculates the game's value, if finished, otherwise returns None.
        Prefer to pass a starting position and move sequence to allow implementing rules like three-fold repetition.
        """
        pos = startpos
        for m in moves:
            pos, _ = self.execute_move(pos, m)
        if not self._is_pos_ended(pos):
            return None
        return self._pos_value(pos)

    def legal_moves(self, pos: Position) -> Iterator[Move]:
        """
        Generates a list of legal moves from a given position.

        Implementations of this function should ensure they do not return duplicate moves, and if is_legal is overridden for performance, its results should exactly match the moves generated by this function.
        """
        raise TypeError("Called legal_moves on Variant base type")

    def is_legal(self, pos: Position, move: Move) -> bool:
        """
        Returns whether a move is legal in a given position or not.
        """
        for m in self.legal_moves(pos):
            if m == move: return True
        return False

    def execute_move(self, pos: Position, move: Move) -> tuple[Position, list[BoardAction]]:
        """
        Performs a move. Returns the new position and a list of primitive board actions the move consists of.
        Note that the board actions do not necessarily contain all information about the move, usually that reflected in the Position's extra information.
        The default implementation tries its best to interpret the move without variant-specific knowledge, this is okay for a lot of moves, but may be wrong if moves have extra effects, like castling, setting en-passant state, etc.
        """
        nextpos = PositionBuilder.from_position(pos)
        nextpos.ply(pos.ply + 1)
        color = Color.from_ply(pos.ply)
        actions = []

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
            if pos.get_piece(move.tosq) is not None:
                nextpos.extra("lastcapture", pos.ply)
            if move.fromsq is None:
                nextpos.piece(move.tosq, move.intopiece)
                actions.append(BoardAction(move.tosq, move.intopiece))
            else:
                nextpos.piece(move.tosq, move.intopiece or pos.get_piece(move.fromsq))
                actions.append(BoardAction(move.tosq, move.fromsq))
                if move.intopiece is not None:
                    actions.append(BoardAction(move.tosq, move.intopiece))

        return nextpos.build(), actions

    def piece_legal_moves(self, pos: Position, fromsq: Square) -> Iterator[Move]:
        """
        Convenience function, returns legal moves involving a given piece (square).
        """
        for move in self.legal_moves(pos):
            if move.fromsq == fromsq:
                yield move

    def legal_drops(self, pos: Position, piecetype: Optional[Piece] = None) -> Iterator[Move]:
        """
        Convenience function, returns legal drop moves (potentially limited to a certain piece type).
        """
        for move in self.legal_moves(pos):
            if move.fromsq == None and (piecetype is None or piecetype == move.intopiece):
                yield move


class TicTacToe(Variant):
    @staticmethod
    def lines(pos: Position) -> Iterator[list[Optional[Piece]]]:
        """
        Helper, returns all lines on the board
        """
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

    def _is_pos_ended(self, pos: Position) -> bool:
        if all(p is not None for sq, p in pos.squares_iter()):
            return True
        for line in self.lines(pos):
            if any(p is None for p in line):
                continue
            colors = [p.color for p in line if p is not None]
            if len(set(colors)) == 1:
                return True
        return False

    def _pos_value(self, pos: Position) -> GameEndValue:
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

    def can_move(self, piece: Piece, like: str) -> bool:
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
        forwardy = 1 if my == Color.WHITE else -1
        W = len(pos.board[0])
        H = len(pos.board)
        ox, oy = square.to_tuple()

        if piece.ty == "P":
            upsq = square.offset(0, forwardy)
            assert pos.inbounds(upsq)
            if pos.get_piece(upsq) is None:
                yield upsq
                _, height = pos.bounds()
                up2sq = square.offset(0, 2 * forwardy)
                if relrank == 1 and pos.get_piece(up2sq) is None:
                    yield up2sq
            if ox > 0:
                sq = upsq.offset(-1, 0)
                p = pos.get_piece(sq)
                if p is not None and p.color == ~my:
                    yield sq
                elif pos.get_extra("ep") == sq:
                    yield sq
            if ox < W-1:
                sq = upsq.offset(1, 0)
                p = pos.get_piece(sq)
                if p is not None and p.color == ~my:
                    yield sq
                elif pos.get_extra("ep") == sq:
                    yield sq
            return # early return, do not handle pawn-like variant pieces
        if self.can_move(piece, "N"):
            for m in range(8):
                x, y = 1, 2
                if m & 1: x, y = y, x
                if m & 2: x = -x
                if m & 4: y = -y
                sq = square.offset(x, y)
                if 0 <= ox + x < W and 0 <= oy + y < H:
                    p = pos.get_piece(sq)
                    if p is None or p.color == ~my:
                        yield sq
        if self.can_move(piece, "K"):
            for x in {-1, 0, 1}:
                for y in {-1, 0, 1}:
                    sq = square.offset(x, y)
                    if not pos.inbounds(sq): continue
                    p = pos.get_piece(sq)
                    if p is None or p.color == ~my:
                        yield sq
            # NOTE: Castling is complex, but cannot capture pieces, handle separately when generating legal moves
        rays = []
        if self.can_move(piece, "B"):
            for y in {-1, 1}:
                for x in {-1, 1}:
                    rays.append((x, y))
        if self.can_move(piece, "R"):
            for y in {-1, 1}: rays.append((0, y))
            for x in {-1, 1}: rays.append((x, 0))
        for x, y in rays:
            cur = square
            while True:
                cur = cur.offset(x, y)
                if not pos.inbounds(cur): break
                p = pos.get_piece(cur)
                if p is None:
                    yield cur
                else:
                    if p.color == ~my:
                        yield cur
                    break

    def game_value(self, startpos: Position, moves: Iterator[Move]) -> Optional[GameEndValue]:
        # TODO: Check 50mr, draw
        # TODO: Check 3fr, draw
        positions = [startpos]
        for m in moves:
            p, _ = self.execute_move(positions[-1], m)
            positions.append(p)
        pos = positions[-1]
        for m in self.legal_moves(pos):
            break
        else:
            # no legal moves
            if self.is_in_check(pos, Color.from_ply(pos.ply)): # Checkmate
                return GameEndValue.win_for(~Color.from_ply(pos.ply))
            else: # Stalemate
                return GameEndValue.DRAW

        return None

    def is_in_check(self, pos: Position, color: Color) -> bool:
        for sq, _ in pos.pieces_iter(~color):
            for tsq in self.target_squares(pos, sq):
                p = pos.get_piece(tsq)
                if p is not None and p.color == color and p.ty == "K":
                    return True
        return False

    def legal_moves(self, pos: Position) -> Iterator[Move]:
        # NOTE: Only supports 8x8 boards, smaller and larger variants should reimplement
        my = Color.from_ply(pos.ply)
        pieces = []
        opppieces = []
        for sq, p in pos.pieces_iter():
            if p.color == my:
                pieces.append((sq, p))
            else:
                opppieces.append((sq, p))

        incheck = self.is_in_check(pos, my)

        for sq, p in pieces:
            for tsq in self.target_squares(pos, sq):
                # Does move lead to our king being threatened?
                probepos, _ = self.execute_move(pos, Move.move(sq, tsq))
                if self.is_in_check(probepos, my):
                    continue # if so, prune the move

                # handle promotion case
                if p.ty == "P" and tsq.rank in {0, 7}:
                    for ty in "QNRB":
                        yield Move.move_promote(sq, tsq, Piece(ty, my))
                else:
                    yield Move.move(sq, tsq)
        # TODO:
        #  Handle castling
        ...

    def execute_move(self, pos: Position, move: Move) -> tuple[Position, list[BoardAction]]:
        # TODO: 50mr counters
        maybepos, actions = super().execute_move(pos, move)
        nextpos = PositionBuilder.from_position(maybepos).extra("ep", None) # Lose en passant rights
        if move.fromsq is not None:
            fromsq = move.fromsq
        else: # piece drop or null move, let the generic impl handle it
            return nextpos.build(), actions
        piece = pos.get_piece(fromsq)
        assert piece is not None
        if piece.ty in "NBQ": # "simple" piece type
            return nextpos.build(), actions
        my = piece.color
        forwardy = 1 if my == Color.WHITE else -1
        homerank = 0 if my == Color.WHITE else 7
        if piece.ty == "P":
            ep = pos.get_extra("ep")
            if ep is not None and move.tosq == ep:
                capturesq = move.tosq.offset(0, -forwardy)
                nextpos.piece(capturesq, None)
                actions.append(BoardAction(capturesq, None))
            elif move.tosq == fromsq.offset(0, 2 * forwardy):
                p = pos.get_piece(move.tosq.offset(-1, 0))
                if p is not None and p.color == ~my and p.ty == "P":
                    nextpos.extra("ep", move.tosq)
                p = pos.get_piece(move.tosq.offset(1, 0))
                if p is not None and p.color == ~my and p.ty == "P":
                    nextpos.extra("ep", move.tosq)

            return nextpos.build(), actions
        castlew: int
        castleb: int
        castlew, castleb = pos.get_extra("castle") or (3, 3)
        mycastle = castlew if my == Color.WHITE else castleb
        if piece.ty == "K":
            if fromsq.rank == homerank and move.tosq.rank == homerank:
                ...
                # TODO: Handle castling
            if my == Color.WHITE:
                castlew = 0
            else:
                castleb = 0
            nextpos.extra("castle", (castlew, castleb))
            return nextpos.build(), actions
        if piece.ty == "R":
            if fromsq.rank == homerank and fromsq.file in {0, 7}: # TODO: Chess960
                if my == Color.WHITE:
                    castlew &= ~(Chess.CASTLE_LONG if fromsq.file == 0 else Chess.CASTLE_SHORT)
                else:
                    castleb &= ~(Chess.CASTLE_LONG if fromsq.file == 0 else Chess.CASTLE_SHORT)
                nextpos.extra("castle", (castlew, castleb))
            return nextpos.build(), actions
        raise ValueError(f"Bad piece {piece!r}")

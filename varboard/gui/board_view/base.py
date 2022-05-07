from __future__ import annotations

import tkinter as tk
import tkinter.messagebox
from ..widgets import SquareView, PieceView
from ...state import GameEndValue

from typing import Any, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...controller import GameController
    from ...state import Piece, Square


class BoardView(tk.Frame):
    def __init__(self, master: Any, controller: GameController, square_scale: tuple[int, int], reverse: bool = False,
                 white_color: str = 'white', black_color: str = 'white', *args: Any, **kwargs: Any):
        kwargs['relief'] = kwargs.get('relief', 'raised')
        kwargs['bd'] = kwargs.get('bd', 10)
        super().__init__(master, *args, **kwargs)

        self.square_scale = square_scale

        self.controller = controller

        self.board_height, self.board_width = controller.current.pos.bounds()

        self.white_color = white_color
        self.black_color = black_color

        self.reverse = reverse

        self.x_pack_side: str
        self.y_pack_side: str

        if reverse:
            self.x_pack_side = tk.RIGHT
            self.y_pack_side = tk.BOTTOM
        else:
            self.x_pack_side = tk.LEFT
            self.y_pack_side = tk.TOP

        # frame for main board with squares in grid
        self.frm_main_board = tk.Frame(master=self, relief=tk.RAISED, bd=6)

        self.squares = [
            [SquareView(self.frm_main_board, self, square_scale[0], square_scale[1], x, self.board_height - y - 1) for x
             in range(self.board_width)]
            for y in range(self.board_height)]
        self.pieces: dict[tuple[int, int], PieceView] = {}

        self.color_squares()

        self.set_bars()
        self.grid_components()

        # set pieces from current position
        for sq, p in controller.current.pos.pieces_iter():
            self.set_piece(sq, p)

    def color_for(self, x: int, y: int) -> str:
        if self.reverse: x, y = self.board_width - x - 1, self.board_height - y - 1
        return self.white_color if abs(x - y) % 2 == 1 else self.black_color

    def color_squares(self) -> None:
        for row in range(self.board_height):

            self.frm_main_board.columnconfigure(row, weight=1)
            self.frm_main_board.rowconfigure(row, weight=1)
            for column in range(self.board_width):
                padx, pady = (0, 0), (0, 0)

                self.squares[row][column].grid(row=row, column=column, sticky='NESW', padx=padx, pady=pady)

                # setting color of squares
                self.squares[row][column].set_color(self.color_for(self.board_width - row - 1, column))

    def set_bars(self) -> None:
        pass

    def grid_components(self) -> None:
        pass

    def piece_to_id(self, piece: Piece) -> str:
        return piece.color.value + piece.ty

    def set_color(self, pos: Union[Square, tuple[int, int]], color: Optional[str]) -> None:
        sq = pos if isinstance(pos, tuple) else pos.to_tuple()
        if color is None: color = self.color_for(*sq)
        if sq in self.pieces:
            self.pieces[sq].set_color(color)
        self.squares[~sq[1]][sq[0]].set_color(color)

    def _set_piece(self, pos, piece):
        self.pieces[pos] = piece
        self.pieces[pos].set_xy(*pos)
        self.pieces[pos].grid(row=(self.board_height - pos[1] - 1), column=pos[0], sticky='NESW', padx=(0, 0),
                              pady=(0, 0))
        self.pieces[pos].set_color(self.color_for(*pos))

    def set_piece(self, pos: Union[Square, tuple[int, int]], piece: Optional[Piece]) -> None:
        pos = pos if isinstance(pos, tuple) else pos.to_tuple()
        old = self.pieces.get(pos)
        if old:
            old.destroy()
            del self.pieces[pos]
        if piece is None:
            return
        pimg = PieceView.load_image(f"pieces/{self.piece_to_id(piece)}.svg", self.square_scale)
        self._set_piece(pos, PieceView(self.frm_main_board, self, pimg))

    def move_piece(self, fpos: Union[Square, tuple[int, int]], tpos: Union[Square, tuple[int, int]]) -> None:
        fpos = fpos if isinstance(fpos, tuple) else fpos.to_tuple()
        tpos = tpos if isinstance(tpos, tuple) else tpos.to_tuple()
        old = self.pieces[fpos]
        del self.pieces[fpos]
        if tpos in self.pieces:
            self.pieces[tpos].destroy()
        self._set_piece(tpos, old)

    def handle_square_btn(self, obj: Union[SquareView, PieceView], x: int, y: int) -> None:
        pass

    def end_game(self, gameend: GameEndValue) -> None:
        print("Game ended!", gameend)
        print("moves:", " ".join(str(m) for m in self.controller.curmoves))
        if gameend == GameEndValue.WHITE_WIN:
            message = "White won!"
        elif gameend == GameEndValue.BLACK_WIN:
            message = "Black won!"
        else:
            message = "DRAW!"
        tkinter.messagebox.showinfo("Game over", message)
        self.master.end_game()  # type: ignore

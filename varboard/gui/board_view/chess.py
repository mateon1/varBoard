from __future__ import annotations

import tkinter as tk
from typing import Any, Union, Optional, TYPE_CHECKING

from . import BoardView
from ..promotion_window import PromotionWindow
from ..widgets import PieceView

if TYPE_CHECKING:
    from ..widgets import SquareView
    from ...state import Piece, Move
    from ...controller import GameController


class ChessBoardView(BoardView):
    def __init__(self, master: Any, controller: GameController, square_scale: tuple[int, int], reverse: bool = False,
                 white_color: str = 'linen', black_color: str = 'saddle brown', *args: Any, **kwargs: Any):
        super().__init__(master, controller, square_scale, reverse, white_color, black_color, *args, **kwargs)
        self.last_clicked: Optional[tuple[int, int]] = None
        self.promotion_choice: Optional[Piece] = None

    def set_bars(self) -> None:
        self.frm_number_bar = tk.Frame(master=self)
        self.frm_letter_bar = tk.Frame(master=self)

        for row in range(self.board_height):
            # filling bar with numbers
            lbl_number = tk.Label(master=self.frm_number_bar, text=str(self.board_height - row))
            lbl_number.pack(expand=True, fill='y', side=self.y_pack_side)  # type: ignore

            # filling bar with letters
            lbl_letter = tk.Label(master=self.frm_letter_bar, text=chr(ord('A') + row))
            lbl_letter.pack(expand=True, fill='x', side=self.x_pack_side)  # type: ignore

            self.frm_main_board.columnconfigure(row, weight=1)
            self.frm_main_board.rowconfigure(row, weight=1)

    def grid_components(self) -> None:
        self.frm_main_board.grid(row=1, column=1)
        self.frm_letter_bar.grid(row=2, column=1, sticky='nesw')
        self.frm_number_bar.grid(row=1, column=0, sticky='nesw')
        self.frm_side_panel.grid(row=1, column=2, sticky='nesw')


        # empty bars for rest sides to maintain symmetry
        tk.Frame(master=self, height=10).grid(row=0, column=1)
        tk.Frame(master=self, width=10).grid(row=1, column=2)

        self.rowconfigure([0, 1], weight=1)  # type: ignore
        self.columnconfigure([0, 1], weight=1)  # type: ignore

    def do_promotion_move(self, moves: list[Move]) -> None:
        pieces = []
        for m in moves:
            assert m.intopiece is not None
            pieces.append(m.intopiece)
        PromotionWindow(self, pieces).wait_window()

        for move in moves:
            if move.intopiece == self.promotion_choice:
                self.domove(move)
                break
        else:
            raise ValueError("Failed to select promotion piece")
        self.promotion_choice = None

    def handle_square_btn(self, square: Union[SquareView, PieceView], x: int, y: int) -> None:
        print(f"Clicked {x}, {y}, last {self.last_clicked}")
        allmoves = []
        movesto = []
        movesfrom = []
        for m in self.controller.legal_moves():
            allmoves.append(m)
            assert m.tosq is not None
            assert m.fromsq is not None
            if m.tosq.to_tuple() == (x, y): movesto.append(m)
            if m.fromsq.to_tuple() == (x, y): movesfrom.append(m)
        for sq in set(m.tosq for m in allmoves):
            self.set_color(sq, None)
        moves = []
        if self.last_clicked:
            moves = [m for m in movesto if m.fromsq is not None and m.fromsq.to_tuple() == self.last_clicked]
        else:
            if len(set(m.fromsq for m in movesto)) == 1:  # Unique move to
                if len(movesto) > 1:
                    self.do_promotion_move(movesto)
                elif len(movesto):
                    self.domove(movesto[0])
                return
            elif len(set(m.tosq for m in movesfrom)) == 1:  # unique move from
                if len(movesfrom) > 1:
                    self.do_promotion_move(movesfrom)
                elif len(movesfrom):
                    self.domove(movesfrom[0])
                return

            # first click, many options
            for m in movesfrom:
                self.set_color(m.tosq, "pale green" if (m.tosq.rank + m.tosq.file) % 2 == 1 else "lime green")
            if len(movesfrom) > 0:
                self.last_clicked = (x, y)
            return

        if len(moves) > 1:
            self.do_promotion_move(moves)
        elif len(moves):
            self.domove(moves[0])
        self.last_clicked = None

    def select_promotion(self, chosen_piece: Piece) -> None:
        self.promotion_choice = chosen_piece


if __name__ == '__main__':
    from ... import variant
    from ...controller import GameController

    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    controller = GameController(variant.Chess(), None)
    board_view = ChessBoardView(window, controller, scale, reverse=False)
    print(board_view.tk)

    board_view.pack()
    window.mainloop()

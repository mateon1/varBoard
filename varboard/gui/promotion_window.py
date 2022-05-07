from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from .widgets import PieceView, SquareView

if TYPE_CHECKING:
    from .board_view import ChessBoardView
    from ..state import Piece


class PromotionWindow(tk.Toplevel):
    def __init__(self, board_view: ChessBoardView, selection: list[Piece]):
        super().__init__()

        self.board_view = board_view

        self.title('Promotion')
        # self.geometry('350x90')

        self.frm = tk.Frame(self)
        self.frm.pack()
        self.piece_types = selection
        self.pieces = []
        self.squares = []
        for i, piece_type in enumerate(self.piece_types):
            pimg = PieceView.load_image(f"pieces/{board_view.piece_to_id(piece_type)}.svg", (75, 75))
            self.squares.append(SquareView(self.frm, self, 75, 75, i, 0))  # type: ignore
            self.pieces.append(PieceView(self.squares[-1], self, pimg))  # type: ignore
            self.pieces[-1].set_xy(i, 0)
            self.pieces[-1].pack()
            self.squares[-1].pack(side=tk.LEFT)

    def handle_square_btn(self, piece: PieceView, x: int, y: int) -> None:
        print(f"Clicked {x}, {y}")
        self.board_view.select_promotion(self.piece_types[x])
        self.destroy()


if __name__ == '__main__':
    from ..state import Color, Piece
    from .board_view import BoardView


    class MockBoardView:
        def piece_to_id(self, p):
            return BoardView.piece_to_id(self, p)

        def select_promotion(self, p):
            print("Selected promotion piece:", p)


    root = PromotionWindow(MockBoardView(), [Piece(ty, Color.WHITE) for ty in "QNRB"])  # type: ignore
    root.mainloop()

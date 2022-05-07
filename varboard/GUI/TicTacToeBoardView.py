from __future__ import annotations

from .BoardView import BoardView
from ..state import Piece, Color
import tkinter as tk
import tkinter.messagebox
from varboard.variant import GameEndValue

from typing import Any, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from ..controller import GameController
    from .widgets import SquareView, PieceView

class TicTacToeBoardView(BoardView):
    def __init__(self, master: Any, controller: GameController, square_scale: tuple[int, int], reverse: bool = False, white_color: str = 'white', black_color: str = 'white', *args: Any, **kwargs: Any):
        super().__init__(master, controller, square_scale, reverse, white_color, black_color, *args, **kwargs)

    def grid_components(self) -> None:
        self.frm_main_board.grid(row=0, column=0)

    def piece_to_id(self, piece: Piece) -> str:
        return "o" if piece.color == Color.WHITE else "x"

    def handle_square_btn(self, square: Union[SquareView, PieceView], x: int, y: int) -> None:
        print(f"Clicked {x}, {y}")
        for m in self.controller.legal_moves():
            if m.tosq.to_tuple() == (x, y):
                print("executing move", m)
                actns, gameend = self.controller.move(m)
                for a in actns:
                    if a.fromsq is not None:
                        # Not for tic tac toe
                        self.move_piece(a.fromsq, a.tosq)
                    else:
                        self.set_piece(a.tosq, a.piece)
                if gameend != None:
                    print("Game ended!", gameend)
                    if gameend == GameEndValue.WHITE_WIN:
                        message = "Circle won!"
                    elif gameend == GameEndValue.BLACK_WIN:
                        message = "Cross won!"
                    else:
                        message = "DRAW!"
                    tkinter.messagebox.showinfo("Game over", message)
                    self.master.end_game() # type: ignore
                break
        else:
            print("Illegal move!!!")

if __name__ == '__main__':
    from .. import variant
    from ..controller import GameController
    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    controller = GameController(variant.TicTacToe(), None)
    board_view = TicTacToeBoardView(window, controller, scale, reverse=False)
    print(board_view.tk)
    o = Piece("P", Color.WHITE)
    x = Piece("P", Color.BLACK)
    board_view.set_piece((1, 1), o)
    board_view.set_piece((0, 1), x)
    board_view.set_piece((2, 0), o)

    board_view.pack()
    window.mainloop()

from .BoardView import *
from ..state import Piece, Color
import tkinter.messagebox
from varboard.variant import GameEndValue


class TicTacToeBoardView(BoardView):
    def __init__(self, master, controller, square_scale, reverse=False, white_color='white', black_color='white', *args, **kwargs):
        super().__init__(master, controller, square_scale, reverse, white_color, black_color, *args, **kwargs)

    def grid_components(self):
        self.frm_main_board.grid(row=0, column=0)

    def piece_to_id(self, piece):
        return "o" if piece.color == Color.WHITE else "x"

    def handle_square_btn(self, square, x, y):
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
                    self.master.end_game()
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

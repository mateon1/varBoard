import tkinter as tk
import tkinter.messagebox

from .widgets import PieceView
from .BoardView import BoardView

class ChessBoardView(BoardView):
    def __init__(self, master, variant, square_scale, reverse=False, white_color='linen', black_color='saddle brown', *args, **kwargs):
        super().__init__(master, variant, square_scale, reverse, white_color, black_color, *args, **kwargs)
        self.last_pointed_square = self.squares[0][0]

    def set_bars(self, reverse):
        self.frm_number_bar = tk.Frame(master=self)
        self.frm_letter_bar = tk.Frame(master=self)

        for row in range(self.board_height):
            # filling bar with numbers
            lbl_number = tk.Label(master=self.frm_number_bar, text=str(self.board_height - row))
            lbl_number.pack(expand=True, fill='y', side=self.y_pack_side)

            # filling bar with letters
            lbl_letter = tk.Label(master=self.frm_letter_bar, text=chr(ord('A') + row))
            lbl_letter.pack(expand=True, fill='x', side=self.x_pack_side)

            self.frm_main_board.columnconfigure(row, weight=1)
            self.frm_main_board.rowconfigure(row, weight=1)

    def grid_components(self):
        self.frm_main_board.grid(row=1, column=1)
        self.frm_letter_bar.grid(row=2, column=1, sticky='nesw')
        self.frm_number_bar.grid(row=1, column=0, sticky='nesw')

        # empty bars for rest sides to maintain symmetry
        tk.Frame(master=self, height=10).grid(row=0, column=1)
        tk.Frame(master=self, width=10).grid(row=1, column=2)

        self.rowconfigure([0, 1], weight=1)
        self.columnconfigure([0, 1], weight=1)

    def handle_square_btn(self, square, x, y):
        print(f"Clicked {x}, {y}")
        for m in self.controller.legal_moves():
            if m.tosq.to_tuple() == (x, y):
                print("executing move", m)
                actns, gameend = self.controller.move(m)
                for a in actns:
                    if a.fromsq is not None:
                        self.move_piece(a.fromsq, a.tosq)
                    else:
                        self.set_piece(a.tosq, a.piece)
                if gameend != None:
                    print("Game ended!", gameend)
                break
        else:
            print("Illegal move!!!")


if __name__ == '__main__':
    from .. import variant
    from ..controller import GameController
    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    controller = GameController(variant.Chess(), None)
    board_view = ChessBoardView(window, controller, scale, reverse=False)
    print(board_view.tk)
    board_view.set_piece(0, 1, 'bK')
    board_view.set_piece(1, 1, 'wN')
    board_view.set_piece(5, 6, 'bR')
    board_view.set_piece(4, 5, 'wK')

    board_view.pack()
    window.mainloop()

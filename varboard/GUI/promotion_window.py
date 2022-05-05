import tkinter as tk
from varboard.state import Color
from varboard.GUI.widgets import PieceView
from varboard.GUI.widgets import SquareView
from varboard.GUI.BoardView import BoardView


class PromotionWindow(tk.Toplevel):
    def __init__(self, board_view : BoardView, color : Color):
        super().__init__()

        self.board_view = board_view

        self.title('Promotion')
        self.geometry('350x90')

        self.frm = tk.Frame(self)
        self.frm.pack()
        self.piece_types = ['Q', 'N', 'R', 'B']
        self.pieces = []
        self.squares = []
        for i, piece_type in enumerate(self.piece_types):
            pimg = PieceView.load_image(f"../../pieces/{color.value+piece_type}.svg", (75, 75))
            self.squares.append(SquareView(self.frm, self, 75, 75, i, 0))
            self.pieces.append(PieceView(self.squares[-1], self, pimg))
            self.pieces[-1].set_xy(i, 0)
            self.pieces[-1].pack()
            self.squares[-1].pack(side=tk.LEFT)

    def handle_square_btn(self,piece, x, y):
        print(f"Clicked {x}, {y}")
        self.board_view.handle_promotion(self.piece_types[x])
        self.destroy()


if __name__ == '__main__':
    root = PromotionWindow(None, Color.BLACK)
    root.mainloop()




import tkinter as tk
from queue import SimpleQueue
from varboard.state import Color, Piece
from varboard.GUI.widgets import PieceView
from varboard.GUI.widgets import SquareView
from varboard.GUI.BoardView import BoardView


class PromotionWindow(tk.Toplevel):
    def __init__(self, board_view: BoardView, selection: list[Piece]):
        super().__init__()

        self.board_view = board_view

        self.title('Promotion')
        #self.geometry('350x90')

        self.frm = tk.Frame(self)
        self.frm.pack()
        self.piece_types = selection
        self.pieces = []
        self.squares = []
        self.sel_queue = SimpleQueue()
        for i, piece_type in enumerate(self.piece_types):
            pimg = PieceView.load_image(f"pieces/{board_view.piece_to_id(piece_type)}.svg", (75, 75))
            self.squares.append(SquareView(self.frm, self, 75, 75, i, 0))
            self.pieces.append(PieceView(self.squares[-1], self, pimg))
            self.pieces[-1].set_xy(i, 0)
            self.pieces[-1].pack()
            self.squares[-1].pack(side=tk.LEFT)

    def handle_square_btn(self, piece, x, y):
        print(f"Clicked {x}, {y}")
        self.board_view.select_promotion(self.piece_types[x])
        self.destroy()


if __name__ == '__main__':
    class MockBoardView:
        def piece_to_id(self, p):
            return BoardView.piece_to_id(self, p)

        def select_promotion(self, p):
            print("Selected promotion piece:", p)

    root = PromotionWindow(MockBoardView(), [Piece(ty, Color.WHITE) for ty in "QNRB"])
    root.mainloop()



import tkinter as tk
from .GUI.BoardView import BoardView
from .GUI.PieceView import Piece

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        scale = (75, 75)
        board = [[None for _ in range(8)] for _ in range(8)]
        self.board_view = BoardView(self, board, scale[0], scale[1], reverse=False)
        # FIXME: The paths here should be relative to some resource directory
        pieces = {'bK': Piece('varboard/GUI/pieces/bK.svg', scale),
                  'wN': Piece('varboard/GUI/pieces/wN.svg', scale),
                  'bR': Piece('varboard/GUI/pieces/bR.svg', scale),
                  'wK': Piece('varboard/GUI/pieces/wK.svg', scale)}
        self.board_view.squares[1][0].set_piece(pieces['bK'])
        self.board_view.squares[1][1].set_piece(pieces['wN'])
        self.board_view.squares[6][5].set_piece(pieces['bR'])
        self.board_view.squares[5][4].set_piece(pieces['wK'])
        self.board_view.pack()

if __name__ == "__main__":
    root = tk.Tk()
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()

import tkinter as tk
from GUI.ChessBoardView import ChessBoardView
from GUI.TicTacToeBoardView import TicTacToeBoardView

from GUI.PieceView import Piece
from GUI.StartMenu import StartMenu

# import GUI.ChessBoardView as cbv
# import GUI.PieceView as Piece
import variant
import state
# from .GUI.PieceView import Piece

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()

    def handle_play_btn(self, variant):
        if variant == "Standard":
            self.start_menu.destroy()
            board = [[None for _ in range(8)] for _ in range(8)]
            ChessBoardView(self, board, 75, 75).pack()
        elif variant == 'TicTacToe':
            self.start_menu.destroy()
            board = [[None for _ in range(3)] for _ in range(3)]
            TicTacToeBoardView(self, board, 75, 75).pack()

if __name__ == "__main__":
    r = MainApplication()
    r.mainloop()
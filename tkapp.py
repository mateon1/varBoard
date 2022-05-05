import tkinter as tk
from varboard.GUI.ChessBoardView import ChessBoardView
from varboard.GUI.TicTacToeBoardView import TicTacToeBoardView
from varboard.GUI.StartMenu import StartMenu
from varboard.GUI.BoardView import BoardView
from varboard.GUI.PieceView import Piece
from typing import Any

class MainApplication(tk.Frame):
    def __init__(self, parent: Any, *args: Any, **kwargs: Any):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

# import varboard.GUI.ChessBoardView as cbv
# import varboard.GUI.PieceView as Piece
# from varboard.GUI.PieceView import Piece

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

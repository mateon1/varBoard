import tkinter as tk
from varboard.variant import Chess
from varboard.variant import TicTacToe
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

    def handle_play_btn(self, option):
        if option == "Standard":
            self.start_menu.destroy()
            game = Chess()
            ChessBoardView(self, game, (75, 75)).pack()
        elif option == 'TicTacToe':
            self.start_menu.destroy()
            game = TicTacToe()
            TicTacToeBoardView(self, game, (120, 120)).pack()

if __name__ == "__main__":
    r = MainApplication()
    r.mainloop()

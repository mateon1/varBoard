import tkinter as tk
from varboard.variant import Chess
from varboard.variant import TicTacToe
from varboard.controller import GameController
from varboard.GUI.ChessBoardView import ChessBoardView
from varboard.GUI.TicTacToeBoardView import TicTacToeBoardView
from varboard.GUI.StartMenu import StartMenu
from varboard.GUI.BoardView import BoardView
from varboard.GUI.widgets import PieceView
from typing import Any

class MainApplication(tk.Frame):
    def __init__(self, parent: Any, *args: Any, **kwargs: Any):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

# import varboard.GUI.ChessBoardView as cbv
# import varboard.GUI.PieceView as PieceView
# from varboard.GUI.PieceView import PieceView

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()
        self.board_view = None

    def handle_play_btn(self, option):
        if option == "Standard":
            self.start_menu.destroy()
            controller = GameController(Chess(), None)
            self.board_view = ChessBoardView(self, controller, (75, 75))
            self.board_view.pack()
        elif option == 'TicTacToe':
            self.start_menu.destroy()
            controller = GameController(TicTacToe(), None)
            self.board_view = TicTacToeBoardView(self, controller, (120, 120))
            self.board_view.pack()

    def end_game(self):
        self.board_view.destroy()
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()



if __name__ == "__main__":
    r = MainApplication()
    r.mainloop()

import tkinter as tk
from varboard.variant import Chess, TicTacToe, RacingKings
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
            self.start_variant("chess")
        elif option == "TicTacToe":
            self.start_variant("tictactoe")
        elif option == "Racing Kings":
            self.start_variant("racingkings")

    def start_variant(self, variant):
        self.start_menu.destroy()
        if variant == "chess":
            controller = GameController(Chess(), None)
            self.board_view = ChessBoardView(self, controller, (75, 75))
        elif variant == "racingkings":
            controller = GameController(RacingKings(), None)
            self.board_view = ChessBoardView(self, controller, (75, 75))
        elif variant == "tictactoe":
            controller = GameController(TicTacToe(), None)
            self.board_view = TicTacToeBoardView(self, controller, (75, 75))
        else:
            raise ValueError("Unknown variant " + variant)
        self.board_view.pack()

    def end_game(self):
        self.board_view.destroy()
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()


if __name__ == "__main__":
    import sys

    r = MainApplication()
    if len(sys.argv) > 1:
        variant = sys.argv[1]
        r.start_variant(variant)
    r.mainloop()

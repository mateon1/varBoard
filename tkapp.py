from __future__ import annotations

import tkinter as tk
from varboard.variant import Chess, TicTacToe, RacingKings
from varboard.controller import GameController
from varboard.GUI.ChessBoardView import ChessBoardView
from varboard.GUI.TicTacToeBoardView import TicTacToeBoardView
from varboard.GUI.StartMenu import StartMenu
from varboard.GUI.BoardView import BoardView
from varboard.GUI.widgets import PieceView

from typing import Any, Optional


class MainApplication(tk.Tk):
    def __init__(self, *args: Any, **kwargs: Any):
        tk.Tk.__init__(self, *args, **kwargs)
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()
        self.board_view: Optional[BoardView] = None

    def handle_play_btn(self, option: str) -> None:
        if option == "Standard":
            self.start_variant("chess")
        elif option == "TicTacToe":
            self.start_variant("tictactoe")
        elif option == "Racing Kings":
            self.start_variant("racingkings")

    def start_variant(self, variant: str) -> None:
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

    def end_game(self) -> None:
        assert self.board_view is not None
        self.board_view.destroy()
        self.board_view = None
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()


if __name__ == "__main__":
    import sys

    r = MainApplication()
    if len(sys.argv) > 1:
        variant = sys.argv[1]
        r.start_variant(variant)
    r.mainloop()

import tkinter as tk
from varboard.variant import Chess, TicTacToe, RacingKings
from varboard.controller import GameController, TimeControl
from varboard.uci import UCIEngine
from varboard.gui.board_view import ChessBoardView, TicTacToeBoardView
from varboard.gui.start_menu import StartMenu

from typing import Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from varboard.gui.board_view import BoardView


# TODO: Better configuration for this
ENGINE1_PATH = "../Stockfish/releases/fairy-stockfish-14.0.1-ana0-dev-6bdcdd8"
ENGINE2_PATH = "../Stockfish/releases/fairy-stockfish-14.0.1-ana0-dev-6bdcdd8"


class MainApplication(tk.Tk):
    def __init__(self, *args: Any, **kwargs: Any):
        tk.Tk.__init__(self, *args, **kwargs)
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()
        self.board_view: Optional[BoardView] = None

    def handle_play_btn(self, option: str, mode: str) -> None:
        if mode == "2 Players":
            n_engines = 0
        elif mode == "Player vs Computer":
            n_engines = 1
        elif mode == "Computer vs Computer":
            n_engines = 2
        else:
            assert False, f"Impossible mode: {mode}"
        if option == "Standard":
            self.start_variant("chess", n_engines)
        elif option == "TicTacToe":
            self.start_variant("tictactoe", n_engines)
        elif option == "Racing Kings":
            self.start_variant("racingkings", n_engines)

    def start_variant(self, variant: str, n_engines: int, time: Optional[float] = None, inc: Optional[float] = None) -> None:
        global controller # DEBUG!!!
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
        if time is not None:
            controller.set_tc(TimeControl(time, inc))
        if n_engines:
            uci = UCIEngine(ENGINE1_PATH)
            uci2 = UCIEngine(ENGINE2_PATH) if n_engines > 1 else None
            controller.with_engine(uci, uci2)
            self.board_view.engine_setup()
        self.board_view.pack()

    def end_game(self) -> None:
        assert self.board_view is not None
        self.board_view.destroy()
        self.board_view = None
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()


if __name__ == "__main__":
    import sys

    controller = None # XXX: DEBUG

    r = MainApplication()
    if len(sys.argv) > 1:
        variant = sys.argv[1]
        engines = 0
        time = None
        inc = None
        if len(sys.argv) > 2:
            engines = 2 if sys.argv[2] not in {"", "0"} else 0
        if len(sys.argv) > 3:
            time = float(sys.argv[3])
        if len(sys.argv) > 4:
            inc = float(sys.argv[4])
        r.start_variant(variant, engines, time, inc)
    r.mainloop()

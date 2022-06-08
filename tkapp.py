import tkinter as tk
from varboard.variant import Chess, NoCastleChess, PawnsOnly, TicTacToe, RacingKings
from varboard.controller import GameController, TimeControl
from varboard.uci import UCIEngine
from varboard.gui.board_view import ChessBoardView, TicTacToeBoardView
from varboard.gui.start_menu import StartMenu

from typing import Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from varboard.gui.board_view import BoardView


# TODO: Better configuration for this
ENGINE1_PATH = "../Fairy-Stockfish/src/fairy-stockfish-largeboard_x86-64"
ENGINE1_ARGS = "load ../Fairy-Stockfish/src/variants.ini".split()
ENGINE1_CONFIG = {
    "Threads": 32,
    "Hash": 256,
#    "SyzygyPath": "/nfs/syzygy",
}
ENGINE2_PATH = "../Fairy-Stockfish/src/fairy-stockfish-largeboard_x86-64"
ENGINE2_ARGS = "load ../Fairy-Stockfish/src/variants.ini".split()
ENGINE2_CONFIG = ENGINE1_CONFIG


class MainApplication(tk.Tk):
    def __init__(self, *args: Any, **kwargs: Any):
        tk.Tk.__init__(self, *args, **kwargs)
        self.start_menu = StartMenu(master=self)
        self.start_menu.pack()
        self.board_view: Optional[BoardView] = None

    def handle_play_btn(self, option: str, mode: str, initial_time: int, increment_time: int) -> None:
        if mode == "2 Players":
            n_engines = 0
        elif mode == "Player vs Computer":
            n_engines = 1
        elif mode == "Computer vs Computer":
            n_engines = 2
        else:
            assert False, f"Impossible mode: {mode}"
        if option == "Standard":
            self.start_variant("chess", n_engines, time=initial_time, inc=increment_time)
        elif option == "No castling":
            self.start_variant("nocastle", n_engines, time=initial_time, inc=increment_time)
        elif option == "Pawns only":
            self.start_variant("pawnsonly", n_engines, time=initial_time, inc=increment_time)
        elif option == "TicTacToe":
            self.start_variant("tictactoe", n_engines, time=initial_time, inc=increment_time)
        elif option == "Racing Kings":
            self.start_variant("racingkings", n_engines, time=initial_time, inc=increment_time)

    def start_variant(self, variant: str, n_engines: int, time: Optional[float] = None, inc: Optional[float] = None) -> None:
        global controller # DEBUG!!!
        self.start_menu.destroy()
        if variant == "chess":
            controller = GameController(Chess(), None)
            self.board_view = ChessBoardView(self, controller, (75, 75))
        elif variant == "nocastle":
            controller = GameController(NoCastleChess(), None)
            self.board_view = ChessBoardView(self, controller, (75, 75))
        elif variant == "pawnsonly":
            controller = GameController(PawnsOnly(), None)
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
            controller.tc.set_clocks((self.board_view.white_timer, self.board_view.black_timer))
            self.board_view.white_timer.update()
            self.board_view.black_timer.update()
        if n_engines:
            uci = UCIEngine(ENGINE1_PATH, ENGINE1_ARGS)
            for k, v in ENGINE1_CONFIG.items():
                uci.option_set(k, v)
            uci2 = UCIEngine(ENGINE2_PATH, ENGINE2_ARGS) if n_engines > 1 else None
            if uci2 is not None:
                for k, v in ENGINE2_CONFIG.items():
                    uci2.option_set(k, v)
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

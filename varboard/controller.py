from __future__ import annotations

import copy
import time
import threading
import queue

from typing import Optional, Iterable, Iterator, Dict, Any, Callable, Union, TYPE_CHECKING

from .state import Position, Move, BoardAction, GameEndValue, Color
from .variant import Variant

if TYPE_CHECKING:
    from .uci import UCIEngine, Score


class TimeControl:
    def __init__(self, time: Union[int, float, tuple[int, int], tuple[float, float]], inc: Optional[Union[int, float, tuple[int, int], tuple[float, float]]]):
        if isinstance(time, tuple):
            self.time = float(time[0]), float(time[1])
        else:
            self.time = float(time), float(time)
        if inc is not None:
            if isinstance(inc, tuple):
                self.inc = float(inc[0]), float(inc[1])
            else:
                self.inc = float(inc), float(inc)
        else:
            self.inc = 0.0, 0.0

    def subtract(self, color: Color, dur: float) -> bool:
        if color == Color.WHITE:
            self.time = self.time[0] - dur + self.inc[0], self.time[1]
            return self.time[0] >= self.inc[0]
        else:
            self.time = self.time[0], self.time[1] - dur + self.inc[1]
            return self.time[1] >= self.inc[1]


class GameTree:
    def __init__(self, current: Position):
        self.pos = current
        self.next_moves: Dict[Move, GameTree] = {}
        self.extra: Dict[str, Any] = {}
        self.pv_move: Optional[Move] = None

    def add_move(self, move: Move, to: Position) -> None:
        self.next_moves[move] = GameTree(to)
        if self.pv_move is None:
            self.pv_move = move

    def set_pv_move(self, move: Move) -> None:
        self.pv_move = move

    def set_extra(self, prop: str, data: Any) -> None:
        self.extra[prop] = data

    def get_extra(self, prop: str) -> Any:
        return self.extra.get(prop)


class GameController:
    def __init__(self, variant: Variant, pos: Optional[Position] = None, tc: Optional[TimeControl] = None):
        self.variant = variant
        self.root_is_startpos = pos is None
        self.tree = GameTree(variant.startpos() if pos is None else pos)
        self.current = self.tree
        self.curmoves: list[Move] = []
        self.uci: Optional[UCIEngine] = None
        self.uci2: Optional[UCIEngine] = None
        self.uci_info_thread: Optional[threading.Thread] = None
        self.uci2_info_thread: Optional[threading.Thread] = None
        self.move_thread: Optional[threading.Thread] = None
        self.lastuci: Optional[UCIEngine] = None
        self.analysis_callback: Optional[Callable[[list[tuple[Move, Score]]], None]] = None
        self.orig_tc = TimeControl(5.0, 2.0) if tc is None else tc # TODO: Make this default more obvious / configurable
        self.tc = copy.deepcopy(self.orig_tc)

    def set_tc(self, tc: TimeControl) -> None:
        self.orig_tc = tc
        self.tc = copy.deepcopy(tc)

    def reset_tc(self) -> None:
        self.tc = copy.deepcopy(self.orig_tc)

    def root(self) -> None:
        self.current = self.tree
        self.curmoves.clear()

    def moves(self, moves: Iterable[Move]) -> None:
        for m in moves:
            self.move(m)

    def move(self, move: Move) -> tuple[list[BoardAction], Optional[GameEndValue]]:
        newpos, actions = self.variant.execute_move(self.current.pos, move)
        if move not in self.current.next_moves:
            self.current.add_move(move, newpos)
        self.current = self.current.next_moves[move]
        self.curmoves.append(move)
        return actions, self.variant.game_value(self.tree.pos, self.curmoves)

    def move_back(self) -> None:
        self.curmoves.pop()
        moves = self.curmoves.copy()
        self.root()
        self.moves(moves)

    def legal_moves(self) -> Iterator[Move]:
        return self.variant.legal_moves(self.current.pos)

    def with_engine(self, uci: UCIEngine, uci2: Optional[UCIEngine] = None) -> None:
        assert self.uci is None
        self.uci = uci
        self.uci2 = uci2

    def set_analysis_callback(self, cb: Callable[[list[tuple[Move, Score]]], None]) -> None:
        self.analysis_callback = cb

    def _uci_info_thread_fn(self, uci: UCIEngine) -> None:
        assert uci is not None
        assert uci.running
        dirty = True
        while uci.running:
            try:
                uci.uci_info_queue.get(timeout=0.1)
                if not dirty:
                    time.sleep(0.001) # minimal sleep to let info messages accumulate
                dirty = True
            except queue.Empty:
                if dirty:
                    if self.analysis_callback is not None:
                        arg = []
                        for ctx in uci.uci_scores:
                            if ctx is None: continue
                            _score = ctx.get("score")
                            assert _score is not None
                            score: Score = _score
                            _pv = ctx.get("pv")
                            assert _pv is not None
                            pv: str = _pv
                            move = Move.from_uci(pv.split(maxsplit=1)[0], self.current.pos.ply)
                            arg.append((move, score))
                        self.analysis_callback(arg)
                dirty = False

    def _start_engine(self) -> None:
        assert self.uci is not None
        assert self.uci_info_thread is None
        if "UCI_Variant" not in self.uci.uci_options:
            assert self.variant.uci_name() == "chess", "Engines with no UCI_Variant support can only play chess"
        else:
            self.uci.option_set("UCI_Variant", self.variant.uci_name())
        if not self.uci.running:
            self.uci.start()
            self.uci.send_initial()
        self.uci_info_thread = threading.Thread(target=self._uci_info_thread_fn, args=(self.uci,))
        self.uci_info_thread.start()
        if self.uci2 is not None:
            if "UCI_Variant" not in self.uci2.uci_options:
                assert self.variant.uci_name() == "chess", "Engines with no UCI_Variant support can only play chess"
            else:
                self.uci2.option_set("UCI_Variant", self.variant.uci_name())
            if not self.uci2.running:
                self.uci2.start()
                self.uci2.send_initial()
            self.uci2_info_thread = threading.Thread(target=self._uci_info_thread_fn, args=(self.uci2,))
            self.uci2_info_thread.start()

    def engine_move_async(self, cb: Callable[[tuple[list[BoardAction], Optional[GameEndValue]]], None]) -> None:
        assert self.uci is not None
        if self.uci_info_thread is None:
            self._start_engine()
        if self.uci2 is not None:
            self.lastuci = self.uci if self.current.pos.ply % 2 == 0 else self.uci2
        assert self.lastuci is not None
        self.lastuci.set_position(self.variant.pos_to_fen(self.tree.pos) if not self.root_is_startpos else None, self.curmoves)
        def move_thread_fn() -> None:
            start = time.time()
            assert self.lastuci is not None
            move = Move.from_uci(self.lastuci.search_sync(self.tc.time, self.tc.inc), self.current.pos.ply)
            self.tc.subtract(Color.from_ply(self.current.pos.ply), time.time() - start)
            cb(self.move(move))
        self.move_thread = threading.Thread(target=move_thread_fn)
        self.move_thread.start()

    def engine_move(self) -> tuple[list[BoardAction], Optional[GameEndValue]]:
        assert self.uci is not None
        if self.uci_info_thread is None:
            self._start_engine()
        if self.uci2 is not None:
            self.lastuci = self.uci if self.current.pos.ply % 2 == 0 else self.uci2
        assert self.lastuci is not None
        self.lastuci.set_position(self.variant.pos_to_fen(self.tree.pos) if not self.root_is_startpos else None, self.curmoves)
        start = time.time()
        move = Move.from_uci(self.lastuci.search_sync(self.tc.time, self.tc.inc), self.current.pos.ply)
        self.tc.subtract(Color.from_ply(self.current.pos.ply), time.time() - start)
        return self.move(move)

    def engine_analyse(self) -> None:
        assert self.uci is not None
        if self.uci_info_thread is None:
            self._start_engine()
            self.lastuci = self.uci
        assert self.lastuci is not None
        self.lastuci.set_position(self.variant.pos_to_fen(self.tree.pos) if not self.root_is_startpos else None, self.curmoves)
        self.lastuci.search_async()

    def engine_stop(self) -> None:
        assert self.uci is not None
        assert self.lastuci is not None
        self.lastuci.search_stop()

import queue
import subprocess
import threading
import time
import enum
from .controller import GameController
from .variant import *
from typing import Optional, Union, Iterator, Iterable, Callable, Any, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .state import Move

# Types:
class ScoreType(enum.Enum):
    MATE = "M"
    CENTIPAWN = "cp"
    INFINITE = "inf"


Context = dict[str, Any]
CommandData = tuple[str, Context]
Parser = Callable[[bytes, Context], tuple[Any, bytes]]
Score = tuple[ScoreType, int]
T = TypeVar("T")


def score_cp(val: int) -> Score:
    return (ScoreType.CENTIPAWN, val)


def score_mate(val: int) -> Score:
    return (ScoreType.MATE, val)


def take_word(line: bytes) -> tuple[bytes, bytes]:
    space = line.find(b" ")
    if space == -1:
        return line, b""
    else:
        return line[:space], line[space:].lstrip()


def take_word_str(line: bytes) -> tuple[str, bytes]:
    w, rest = take_word(line)
    return w.decode("utf-8"), rest


def parse_word_str(line: bytes, _ctx: Context) -> tuple[str, bytes]:
    return take_word_str(line)


def parse_rest_str(line: bytes, _ctx: Context) -> tuple[str, bytes]:
    return line.decode("utf-8"), b""


def parse_int(line: bytes, _ctx: Context) -> tuple[int, bytes]:
    i, rest = take_word(line)
    return int(i), rest


def parse_score(line: bytes, _ctx: Context) -> tuple[Score, bytes]:
    ty, rest = take_word(line)
    if ty == b"cp":
        v, rest = take_word(rest)
        return score_cp(int(v)), rest
    elif ty == b"mate":
        v, rest = take_word(rest)
        return score_mate(int(v)), rest
    elif b"inf" in ty:
        return (ScoreType.INFINITE, -1 if b"-" in ty else 1), rest
    else:  # Maybe it's centipawns without cp?
        return score_cp(int(ty)), rest


def parse_wdl(line: bytes, _ctx: Context) -> tuple[tuple[int, int, int], bytes]:
    w, rest = take_word(line)
    d, rest = take_word(rest)
    l, rest = take_word(rest)
    return (int(w), int(d), int(l)), rest


def parse_nothing(line: bytes, _ctx: Context) -> tuple[None, bytes]:
    return None, line


def parse_option_name(line: bytes, _ctx: Context) -> tuple[str, bytes]:
    upto = line.index(b" type")
    return line[:upto].strip().decode("utf-8"), line[upto + 1:]


def parse_option_var(line: bytes, ctx: Context) -> tuple[set[str], bytes]:
    varz = ctx.get("var", set())
    v, rest = take_word_str(line)
    return varz | {v}, rest


def parse_option_default(line: bytes, ctx: Context) -> tuple[Any, bytes]:
    ty = ctx["type"]
    if ty == "string":
        s, rest = parse_rest_str(line, ctx)
        if s == "<empty>": s = ""
        return s, rest
    elif ty == "spin":
        i, rest = take_word(line)
        return int(i), rest
    elif ty == "check":
        b, rest = take_word(line)
        assert b.lower() in {b"true", b"false"}
        return b.lower() == b"true", rest
    elif ty == "combo":
        s, rest = take_word_str(line)
        return s, rest
    assert False, f"option default illegal for type {ty}"


UCI_FIELDS: dict[str, dict[str, Union[Parser, set[str]]]] = {
    "id": {
        "name": parse_rest_str,
        "author": parse_rest_str,
    },
    "option": {
        "name": parse_option_name,
        "type": {"check", "spin", "string", "combo", "button"},
        "default": parse_option_default,
        "min": parse_int,
        "max": parse_int,
        "var": parse_option_var,
    },
    "uciok": {},
    "readyok": {},
    "info": {
        "string": parse_rest_str,
        "depth": parse_int,
        "seldepth": parse_int,
        "currmove": parse_word_str,
        "currmovenumber": parse_int,
        "multipv": parse_int,
        "score": parse_score,
        "lowerbound": parse_nothing,
        "upperbound": parse_nothing,
        "wdl": parse_wdl,
        "nodes": parse_int,
        "nps": parse_int,
        "hashfull": parse_int,
        "tbhits": parse_int,
        "time": parse_int,
        "pv": parse_rest_str,
        "alpha": parse_score,
        "beta": parse_score,
    },
    "bestmove": {  # SPECIAL CASE - starts with raw move
        "ponder": parse_word_str,
    },
}

# Windows sucks, so ^C cannot interrupt queue.get(). This is the workaround
def get_interruptible(q: queue.SimpleQueue[T], pred: Callable[[], bool] = lambda: True) -> Optional[T]:
    while pred():
        try:
            return q.get(timeout=0.2)
        except queue.Empty:
            pass
    return None


class UCIEngine:
    def __init__(self, path: str, extra_args: Iterable[str] = ()):
        self.path: str = path
        self.extra_args: tuple[str, ...] = tuple(extra_args)
        self.engine_process: Optional[subprocess.Popen[bytes]] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.log: list[tuple[float, str]] = []
        self.running: bool = False
        self.searching: bool = False

        self.uci_options: dict[str, Context] = {}
        self.uci_ready_queue = queue.SimpleQueue[CommandData]()
        self.uci_info_queue = queue.SimpleQueue[CommandData]()
        self.uci_move_queue = queue.SimpleQueue[CommandData]()
        self.uci_scores: list[Optional[Context]] = [None]

        self.uci_set_options: dict[str, str] = {}

        self.probe_engine()

    def process_line(self, line: bytes) -> None:
        # print("-----")
        # print(line.strip().decode("utf-8"))
        cmd, rest = take_word_str(line.strip())
        if cmd not in UCI_FIELDS:
            print(line)
            print("Unrecognized command:", cmd)
            return

        fields = UCI_FIELDS[cmd]
        ctx: Context = {}
        # print("command:", cmd)
        if cmd == "bestmove":  # special case
            move, rest = parse_word_str(rest, ctx)
            ctx["bestmove"] = move

        while len(rest) > 0:
            field, rest = take_word_str(rest)
            if field not in fields:
                print(f"Unknown field {field} in command {cmd}")
                continue
            # print("field", field, ctx)
            field_parse = fields[field]
            if isinstance(field_parse, set):
                rawval, rest = take_word(rest)
                val = rawval.decode("utf-8")
                if val not in field_parse:
                    print(f"Bad field value: {field} {val}")
                    # allow it to continue parsing anyway, maybe we'll get something useful
            else:
                val, rest = field_parse(rest, ctx)
            ctx[field] = val

        if cmd == "info" and "score" in ctx:
            multipv = ctx.get("multipv", 1) - 1
            while multipv >= len(self.uci_scores): self.uci_scores.append(None)
            self.uci_scores[multipv] = ctx

        if cmd == "option":
            self.uci_options[ctx["name"]] = ctx
        elif cmd in {"info", "id"}:
            self.uci_info_queue.put((cmd, ctx))
        elif cmd in {"uciok", "readyok"}:
            self.uci_ready_queue.put((cmd, ctx))
        elif cmd == "bestmove":
            self.searching = False
            self.uci_move_queue.put((cmd, ctx))
        else:
            print("Unhandled command:", cmd)

    def probe_engine(self) -> None:
        self.start()
        self.send_command("uci")
        print(get_interruptible(self.uci_ready_queue, lambda: self.running))
        self.send_command("isready")
        print(get_interruptible(self.uci_ready_queue, lambda: self.running))
        self.close_wait()

    def option_set(self, option: str, value: Union[None, int, str, bool]) -> None:
        ctx = self.uci_options.get(option)
        if ctx is None:
            raise ValueError("Invalid option " + option)
        if ctx["type"] == "button":
            assert self.running
            self.send_command("setoption name " + option)
            return
        if ctx["type"] == "check":
            assert isinstance(value, bool)
            self.uci_set_options[option] = "true" if value else "false"
        elif ctx["type"] == "spin":
            assert isinstance(value, int)
            assert ctx["min"] <= value <= ctx["max"]
            self.uci_set_options[option] = str(value)
        elif ctx["type"] == "combo":
            assert isinstance(value, str)
            assert value in ctx["var"]
            self.uci_set_options[option] = value
        else:
            assert ctx["type"] == "string"
            assert isinstance(value, str)
            self.uci_set_options[option] = value
        if self.running:
            self.send_command(f"setoption name {option} value {self.uci_set_options[option]}")

    def option_unset(self, option: str) -> None:
        ctx = self.uci_options.get(option)
        if ctx is None:
            raise ValueError("Invalid option " + option)
        assert ctx["type"] != "button"
        if option in self.uci_set_options:
            del self.uci_set_options[option]
            if self.running:
                default = ctx.get("default")
                self.send_command(f"setoption name {option} value {default}")

    def send_initial(self) -> None:
        self.send_command("uci")
        print(get_interruptible(self.uci_ready_queue, lambda: self.running))
        for opt, val in self.uci_set_options.items():
            self.send_command(f"setoption name {opt} value {val}")
        self.send_command("isready")
        print(get_interruptible(self.uci_ready_queue, lambda: self.running))

    def set_position(self, initial: Optional[str], moves: Optional[list[Move]]) -> None:
        cmd = "position "
        if initial is not None:
            if initial.startswith("fen ") or initial == "startpos":
                cmd += initial
            else:
                cmd += "fen " + initial
        else:
            cmd += "startpos"
        if moves is not None:
            cmd += " moves"
            for move in moves:
                cmd += " " + move.to_uci()
        self.send_command(cmd)
        self.send_command("isready")
        print(get_interruptible(self.uci_ready_queue, lambda: self.running))

    def search_sync(self, time: tuple[float, float], inc: Optional[tuple[float, float]] = None) -> str:
        self.search_async(time, inc)
        raw = get_interruptible(self.uci_move_queue)
        assert raw is not None
        _, ctx = raw
        assert not self.searching
        # TODO: Return actual Move -- Need ply info somehow
        move: str = ctx["bestmove"]
        return move

    def search_async(self, time: Optional[tuple[float, float]] = None, inc: Optional[tuple[float, float]] = None) -> None:
        assert not self.searching
        self.searching = True
        cmd = "go"
        if time is not None:
            wtime = int(time[0] * 1000)
            btime = int(time[1] * 1000)
            cmd += f" wtime {wtime} btime {btime}"
            if inc is not None:
                winc = int(inc[0] * 1000)
                binc = int(inc[1] * 1000)
                cmd += f" winc {winc} binc {binc}"
        else:
            cmd += " infinite"
        self.send_command(cmd)

    def search_stop(self) -> str:
        assert self.searching
        self.send_command("stop")
        raw = get_interruptible(self.uci_move_queue)
        assert raw is not None
        _, ctx = raw
        # TODO: Return actual Move
        move: str = ctx["bestmove"]
        return move

    def reader(self, pipe: Iterator[bytes]) -> None:
        assert self.engine_process is not None
        try:
            for l in pipe:
                self.log.append((time.time(), l.decode("utf-8")))
                self.process_line(l)
            if self.engine_process is not None:
                self.engine_process.wait(2.0)
        except KeyboardInterrupt:
            self.close()
            raise
        self.close()

    def close_wait(self) -> None:
        if self.running:
            self.send_command("quit")
            assert self.engine_process is not None
            assert self.reader_thread is not None
            self.reader_thread.join()
        self.close()

    def close(self) -> None:
        if self.engine_process:
            self.engine_process.terminate()
            self.engine_process.wait(5.0)
            if self.engine_process is not None:
                self.engine_process.kill()
        self.engine_process = None
        self.reader_thread = None
        self.running = False

    def start(self) -> None:
        assert self.engine_process is None
        assert self.reader_thread is None
        self.uci_ready_queue = queue.SimpleQueue()
        self.uci_info_queue = queue.SimpleQueue()
        self.uci_move_queue = queue.SimpleQueue()
        subproc = subprocess.Popen((self.path,) + self.extra_args,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.engine_process = subproc
        assert subproc.stdout is not None
        stdout = subproc.stdout
        self.reader_thread = threading.Thread(target=lambda: self.reader(stdout))
        self.reader_thread.name = "UCI Reader " + self.reader_thread.name
        self.reader_thread.start()
        self.running = True

    def send_command(self, command: str) -> None:
        assert self.engine_process is not None
        assert self.engine_process.stdin is not None
        self.engine_process.stdin.write((command.strip() + "\n").encode("utf-8"))
        self.engine_process.stdin.flush()


if __name__ == "__main__":  # TEMPORARY - for testing
    import sys

    print(sys.argv)
    #FISH = "/home/mateon/shared/dev/Stockfish/releases/fairy-stockfish-14.0.1-ana0-dev-6bdcdd8"
    FISH = "/home/mateon/shared/dev/Stockfish/releases/fairy-stockfish-14.0.1-largeboards-dev-6bdcdd8"
    #FISH = "./fairy-stockfish-largeboard_x86-64-bmi2.exe"
    uci = UCIEngine(FISH)
    uci.start()
    uci.send_command("load ../Stockfish/releases/variants.ini")
    # uci.send_command("load ../Fairy-Stockfish/src/variants.ini")
    uci.send_command("uci")
    print(get_interruptible(uci.uci_ready_queue, lambda: uci.running))
    uci.close_wait()

    print("variants", uci.uci_options["UCI_Variant"]["var"])

    variant = "chess"

    if len(sys.argv) > 1:
        uci.option_set("UCI_Variant", sys.argv[1])
        variant = sys.argv[1]
    if len(sys.argv) > 2:
        uci.option_set("EvalFile", sys.argv[2])

    uci.option_set("Hash", 1024)
    uci.option_set("Threads", 32)

    uci.start()
    uci.send_command("load ../Stockfish/releases/variants.ini")
    # uci.send_command("load ../Fairy-Stockfish/src/variants.ini")
    uci.send_initial()

    # for ts, l in uci.log:
    #    if not "option" in l: continue
    #    print(f"{ts:.6f} {l.strip()}")
    cur_i = 0
    wtime = btime = 0.0
    moves: list[str] = []
    start = time.time()

    if variant == "chess":
        controller = GameController(Chess())
    elif variant == "tictactoe":
        controller = GameController(TicTacToe())
    elif variant == "racingkings":
        controller = GameController(RacingKings())

    def info_thread_fn() -> None:
        time.sleep(0.1)
        try:
            while uci.running:
                try:
                    _ = uci.uci_info_queue.get(timeout=0.1)
                    info = uci.uci_scores[0]
                    score = info["score"] if info is not None else "???"
                    depth = "%3d" % info["depth"] if info is not None else "???"
                    est = (time.time() - start)
                    wt = round((wtime - (0 if cur_i & 1 else est))*1000)
                    bt = round((btime - (est if cur_i & 1 else 0))*1000)
                    print(f"{cur_i:3d}/200 ...{' '.join(moves[-5:])} time w{wt:6d} b{bt:6d} depth {depth} score {score}  ",
                          end="\r")
                except queue.Empty:
                    pass
        except KeyboardInterrupt:
            print("Interrupted info thread")
            uci.close()
            raise

    info_thread = threading.Thread(target=info_thread_fn)
    info_thread.start()

    try:
        for game in range(500):
            print(f"===== GAME #{game + 1} =====")
            moves = []
            wtime = btime = 15.0
            winc = binc = 0.2
            for i in range(200):
                cur_i = i
                info = {} if i == 0 else uci.uci_scores[0]
                print(f"{i:3d}/200 ...{' '.join(moves[-5:])} score ???   ", end="\r")
                uci.send_command(f"position startpos moves {' '.join(moves)}")
                start = time.time()
                move = uci.search_sync((wtime, btime), (winc, binc))
                dur = time.time() - start
                if move == "(none)": break
                if i & 1 == 0:
                    wtime -= dur
                    wtime += winc
                else:
                    btime -= dur
                    btime += binc
                # print(move)
                moves.append(move)
            time.sleep(0.05)
            print()
            print(moves)
            print(uci.log[-2])
        uci.close_wait()
    except KeyboardInterrupt:
        uci.close()
    info_thread.join()

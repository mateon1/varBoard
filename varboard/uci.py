import queue
import subprocess
import threading
import time
from typing import Optional, Union, Iterator, Iterable, Callable, IO, Any

# Types:
function = type(lambda: 0)
Context = dict[str, Any]
CommandData = tuple[str, Context]
Parser = Callable[[bytes, Context], tuple[Any, bytes]]

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

def parse_score(line: bytes, _ctx: Context) -> tuple[tuple[str, Any], bytes]:
    ty, rest = take_word(line)
    if ty == b"cp":
        v, rest = take_word(rest)
        return ("cp", int(v)), rest
    elif ty == b"mate":
        v, rest = take_word(rest)
        return ("mate", int(v)), rest
    else: # Maybe it's centipawns without cp?
        return ("cp", float(ty)), rest ## XXX: Hack, handle infinity

def parse_wdl(line: bytes, _ctx: Context) -> tuple[tuple[int, int, int], bytes]:
    w, rest = take_word(line)
    d, rest = take_word(rest)
    l, rest = take_word(rest)
    return (int(w), int(d), int(l)), rest

def parse_nothing(line: bytes, _ctx: Context) -> tuple[None, bytes]:
    return None, line

def parse_option_name(line: bytes, _ctx: Context) -> tuple[str, bytes]:
    upto = line.index(b" type")
    return line[:upto].strip().decode("utf-8"), line[upto+1:]

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
    "bestmove": { # SPECIAL CASE - starts with raw move
        "ponder": parse_word_str,
    },
}

class UCIEngine:
    def __init__(self, path: str, extra_args: Iterable[str] = ()):
        self.path: str = path
        self.extra_args: tuple[str, ...] = tuple(extra_args)
        self.engine_process: Optional[subprocess.Popen[bytes]] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.log: list[tuple[float, str]] = []

        self.uci_options: dict[str, Context] = {}
        self.uci_ready_queue = queue.SimpleQueue[CommandData]()
        self.uci_info_queue = queue.SimpleQueue[CommandData]()
        self.uci_move_queue = queue.SimpleQueue[CommandData]()
        self.uci_scores: list[Optional[Context]] = [None]

        self.uci_set_options: dict[str, str] = {}

        self.probe_engine()

    def process_line(self, line: bytes) -> None:
        #print("-----")
        #print(line.strip().decode("utf-8"))
        cmd, rest = take_word_str(line.strip())
        if cmd not in UCI_FIELDS:
            print(line)
            print("Unrecognized command:", cmd)
            return

        fields = UCI_FIELDS[cmd]
        ctx: Context = {}
        #print("command:", cmd)
        if cmd == "bestmove": # special case
            move, rest = parse_word_str(rest, ctx)
            ctx["bestmove"] = move

        while len(rest) > 0:
            field, rest = take_word_str(rest)
            if field not in fields:
                print(f"Unknown field {field} in command {cmd}")
                continue
            #print("field", field, ctx)
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
            self.uci_move_queue.put((cmd, ctx))
        else:
            print("Unhandled command:", cmd)

    def probe_engine(self) -> None:
        self.start()
        self.send_command("uci")
        print(self.uci_ready_queue.get())
        self.send_command("isready")
        print(self.uci_ready_queue.get())
        self.send_command("quit")
        self.engine_process.wait()
        self.reader_thread.join()

    def option_set(self, option: str, value: Union[None, int, str, bool]) -> None:
        ctx = self.uci_options.get(option)
        if ctx is None:
            raise ValueError("Invalid option " + option)
        if ctx["type"] == "button":
            assert self.running
            uci.send_command("setoption name " + option)
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
        uci.send_command("uci")
        print(uci.uci_ready_queue.get())
        for opt, val in self.uci_set_options.items():
            uci.send_command(f"setoption name {opt} value {val}")
        uci.send_command("isready")
        print(uci.uci_ready_queue.get())

    def reader(self, pipe: Iterator[bytes]) -> None:
        assert self.engine_process is not None
        for l in pipe:
            self.log.append((time.time(), l.decode("utf-8")))
            self.process_line(l)
        self.engine_process.wait()
        self.close()

    def close(self) -> None:
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
        self.reader_thread.setName("UCI Reader " + self.reader_thread.name)
        self.reader_thread.start()
        self.running = True

    def send_command(self, command: str) -> None:
        assert self.engine_process is not None
        assert self.engine_process.stdin is not None
        self.engine_process.stdin.write((command.strip() + "\n").encode("utf-8"))
        self.engine_process.stdin.flush()

if __name__ == "__main__": # TEMPORARY - for testing
    import sys
    print(sys.argv)
    FISH = "/home/mateon/shared/dev/Stockfish/releases/fairy-stockfish-14.0.1-ana0-dev-6bdcdd8"
    uci = UCIEngine(FISH)
    uci.start()
    uci.send_command("load ../Stockfish/releases/variants.ini")
    uci.send_command("uci")
    print(uci.uci_ready_queue.get())
    uci.send_command("quit")
    uci.engine_process.wait()
    uci.reader_thread.join()

    print("variants", uci.uci_options["UCI_Variant"]["var"])

    if len(sys.argv) > 1:
        uci.option_set("UCI_Variant", sys.argv[1])
    if len(sys.argv) > 2:
        uci.option_set("EvalFile", sys.argv[2])

    uci.option_set("Hash", 128)
    uci.option_set("Threads", 32)

    uci.start()
    uci.send_command("load ../Stockfish/releases/variants.ini")
    uci.send_initial()

    #for ts, l in uci.log:
    #    if not "option" in l: continue
    #    print(f"{ts:.6f} {l.strip()}")
    cur_i = 0
    wtime = btime = 0
    moves: list[str] = []
    start = time.time()
    def info_thread_fn() -> None:
        time.sleep(0.1)
        while True:
            try:
                _ = uci.uci_info_queue.get(timeout=0.1)
                info = uci.uci_scores[0]
                score = info["score"] if info is not None else "???"
                depth = "%3d" % info["depth"] if info is not None else "???"
                est = round((time.time() - start)*1000)
                wt = wtime - (0 if cur_i & 1 else est)
                bt = btime - (est if cur_i & 1 else 0)
                print(f"{cur_i:3d}/200 ...{' '.join(moves[-5:])} time w{wt:6d} b{bt:6d} depth {depth} score {score}  ", end="\r")
            except queue.Empty:
                pass
    info_thread = threading.Thread(target=info_thread_fn)
    info_thread.start()
    for game in range(500):
        print(f"===== GAME #{game+1} =====")
        moves = []
        wtime = btime = 15000
        winc = binc = 200
        for i in range(200):
            cur_i = i
            info = {} if i == 0 else uci.uci_scores[0]
            print(f"{i:3d}/200 ...{' '.join(moves[-5:])} score ???   ", end="\r")
            uci.send_command(f"position startpos moves {' '.join(moves)}")
            #uci.send_command("go movetime 1000")
            uci.send_command(f"go wtime {wtime} btime {btime} winc {winc} binc {binc}")
            start = time.time()
            _, move = uci.uci_move_queue.get()
            dur = round((time.time() - start) * 1000)
            if move["bestmove"] == "(none)": break
            if i&1 == 0:
                wtime -= dur
                wtime += winc
            else:
                btime -= dur
                btime += binc
            #print(move)
            moves.append(move["bestmove"])
        time.sleep(0.05)
        print()
        print(moves)
        print(uci.log[-2])
    assert uci.reader_thread is not None
    uci.send_command("quit")
    uci.reader_thread.join()
    info_thread.join()

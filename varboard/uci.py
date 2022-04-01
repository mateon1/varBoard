import subprocess
import threading
import time

def take_word(line: bytes) -> (bytes, bytes):
    space = line.find(b" ")
    if space == -1:
        return line, b""
    else:
        return line[:space], line[space:].lstrip()

def parse_word_str(line: bytes, _ctx: dict) -> (str, bytes):
    w, rest = take_word(line)
    return w.decode("utf-8"), rest

def parse_rest_str(line: bytes, _ctx: dict) -> (str, bytes):
    return line.decode("utf-8"), b""

def parse_int(line, _ctx: dict) -> (int, bytes):
    i, rest = take_word(line)
    return int(i), rest

def parse_score(line, _ctx: dict) -> ('todo', bytes):
    ty, rest = take_word(line)
    if ty == b"cp":
        v, rest = take_word(rest)
        return (("cp", int(v)), rest)
    assert False, "unimplemented"

def parse_option_name(line: bytes, _ctx: dict) -> (str, bytes):
    upto = line.index(b"type")
    return line[:upto].strip().decode("utf-8"), line[upto:]

def parse_option_var(line: bytes, ctx: dict) -> (list, bytes):
    varz = ctx.get(b"var", set())
    v, rest = take_word(line)
    return varz | {v}, rest

def parse_option_default(line: bytes, ctx: dict) -> ('Any', bytes):
    ty = ctx[b"type"]
    if ty == b"string":
        s, rest = parse_rest_str(line, ctx)
        if s == "<empty>": s = ""
        return s, rest
    elif ty == b"spin":
        i, rest = take_word(line)
        return int(i), rest
    elif ty == b"check":
        b, rest = take_word(line)
        assert b.lower() in {b"true", b"false"}
        return b.lower() == b"true", rest
    elif ty == b"combo":
        s, rest = take_word(line)
        return s.decode("utf-8"), rest
    assert False, f"option default illegal for type {ty}"

UCI_FIELDS = {
    b"id": {
        b"name": parse_rest_str,
        b"author": parse_rest_str,
    },
    b"option": {
        b"name": parse_option_name,
        b"type": {b"check", b"spin", b"string", b"combo", b"button"},
        b"default": parse_option_default,
        b"min": parse_int,
        b"max": parse_int,
        b"var": parse_option_var,
    },
    b"uciok": {},
    b"readyok": {},
    b"info": {
        b"string": parse_rest_str,
        b"depth": parse_int,
        b"seldepth": parse_int,
        b"currmove": parse_word_str,
        b"currmovenumber": parse_int,
        b"multipv": parse_int,
        b"score": parse_score,
        b"nodes": parse_int,
        b"nps": parse_int,
        b"hashfull": parse_int,
        b"tbhits": parse_int,
        b"time": parse_int,
        b"pv": parse_rest_str,
    },
    b"bestmove": { # SPECIAL CASE - starts with raw move
        b"ponder": parse_word_str,
    },
}

class UCIEngine:
    def __init__(self, path, extra_args=()):
        self.path = path
        self.extra_args = tuple(extra_args)
        self.running = False
        self.engine_process = None
        self.reader_thread = None
        self.log = []

        self.uci_options = {}
        self.uci_saw = {}

    def process_line(self, line: bytes):
        #print("-----")
        #print(line.strip().decode("utf-8"))
        cmd, rest = take_word(line.strip())
        if cmd not in UCI_FIELDS:
            print(f"Unrecognized command: {cmd}")
            return

        self.uci_saw[cmd] = self.uci_saw.get(cmd, 0) + 1

        fields = UCI_FIELDS[cmd]
        ctx = {}
        #print("command:", cmd)
        if cmd == b"bestmove": # special case
            move, rest = parse_word_str(rest, ctx)
            ctx[b"bestmove"] = move

        while len(rest) > 0:
            field, rest = take_word(rest)
            if field not in fields:
                print(f"Unknown field {field} in command {cmd}")
                continue
            #print("field", field, ctx)
            field_parse = fields[field]
            if type(field_parse) is set:
                val, rest = take_word(rest)
                if val not in field_parse:
                    print(f"Bad field value: {field + b' ' + val}")
                    # allow it to continue parsing anyway, maybe we'll get something useful
            else:
                val, rest = field_parse(rest, ctx)
            ctx[field] = val

        if cmd == b"option":
            self.uci_options[ctx[b"name"]] = ctx

    def reader(self, pipe):
        for l in pipe:
            self.log.append((time.time(), l.decode("utf-8")))
            self.process_line(l)
        self.engine_process.wait()
        self.running = False

    def start(self):
        assert not self.running
        self.engine_process = subprocess.Popen((self.path,) + self.extra_args,
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.reader_thread = threading.Thread(target=lambda: self.reader(self.engine_process.stdout))
        self.reader_thread.setName("UCI Reader " + self.reader_thread.name)
        self.reader_thread.start()
        self.running = True

    def send_command(self, command):
        assert self.running
        self.engine_process.stdin.write((command.strip() + "\n").encode("utf-8"))
        self.engine_process.stdin.flush()

if __name__ == "__main__": # TEMPORARY - for testing
    FISH = "/home/mateon/shared/dev/Stockfish/releases/fairy-stockfish-14.0.1-ana0-dev-6bdcdd8"
    uci = UCIEngine(FISH)
    uci.start()
    uci.send_command("uci")
    uci.send_command("isready")
    #for ts, l in uci.log:
    #    if not "option" in l: continue
    #    print(f"{ts:.6f} {l.strip()}")
    uci.send_command("go depth 10")
    while uci.uci_saw.get(b"bestmove") == 0:
        time.sleep(0.05)
    uci.send_command("quit")
    uci.reader_thread.join()
    for i in uci.uci_options.values():
        print(i)
